import os
import pathlib
import sublime
import sublime_plugin
import subprocess
import shlex
import shutil
import time
import trace
import pprint 
pp = pprint.PrettyPrinter(indent=4)
from threading import Thread
from collections import namedtuple
configFileGroup = namedtuple('configFileGroup', 'userFile templateFile exampleFile')
configFiles = {}

plugin_settings_file = 'ShellRunner.sublime-settings'
plugin_canon_name = 'ShellRunner'
outputToValues = ['newTab', 'sublConsole', 'cursorInsert', 'msgBox', 'clip', None]
outputToJsonKeyStr = str(outputToValues).replace('None', 'null')

def showShRunnerError(errormsg):
    sublime.message_dialog("{} Command Report::\n\n{}".format(plugin_canon_name, errormsg))


class splitCommand():
    def __init__(self, cmdStr):
        self.cmdStr = cmdStr
        self.tokens = ['']
        self.OK = False
        self.errorStr = ""
        try:
            self.tokens = shlex.split(self.cmdStr, posix=True)
            self.OK = True
        except Exception as err:
            self.errorStr = ("An unexpected exception occurred in splitting/tokenising your command for the shell. "
                              "Please check your command is formatted correctly.\n\n"
                              "Split attempted on:: {}\n\n"
                              "Details:: {}\n\n{}").format(self.cmdStr, err.__class__.__name__, err)


def retrieveSetting(settingName, primaryDict, secondaryDict={}, default=None):
    if secondaryDict:
        return primaryDict.get(settingName, secondaryDict.get(settingName, default))
    else:
        return primaryDict.get(settingName, default)


# define our global main settings with default values
# `- this dictionary is kept up to date with
#  - a) a callback if any of the ShellRunner.sublime-settings files are changed
#  - b) a triggered event if a project loads (i.e. .sublime-project file is saved)
activeSettings = {
    "openTerminalCmd": "",
    "showSidebarTerminalCmd": True,
    "showContextTerminalCmd": True,
    "showSidebarEditMenu": True,
    "showContextEditMenu": True,
    "initChangeDir": True,
    "outputTo": [""],
    "outputTabName": "",
    "cmdCombineOutputStreams": False,
    "textCmdTimeout": 10,
    "textCmdStopOnErr": True,
    "multiSelSeparator": " ",
    "selAsLiteralStr": False,
    "cleanShellEnv": False,
    "extraGlobalShellEnvVars": {},
    "extraGlobalSubstVars": {}, 
}


def consoleWarn(warnMsg):
    print("{} Warning: {}".format(plugin_canon_name, warnMsg))

def setupConfigFileFramework(factoryReset=False):
    """
    4 user manipulable config files can exist in the ${packages}/ShellRunner directory
    `- these are: ShellRunner.sublime-settings, Side Bar.sublime-menu
     - Context.sublime-menu, and Default (${platform}).sublime-keymap
    Each of these files has a corresponding 'template' (blankish canvas) file,
    `- and a corresponding 'example' (fullish canvas) file
    This 'setupConfigFileFramework' gets run under two circumstances:
    `- A) When the ShellRunner plugin is loaded:
          Here the function checks to see if the 'user' version of each config file
          exists, and if it does not, the 'template' version is copied into its place
    `- B) When the user issues a 'Factory Reset' command (available via the command palette):
          Here the function copies 'template' files over 'user' files irrespective of
          whether the 'user' file exists or not.
    The 'setupConfigFileFramework' function also sets up a global reference dict
    for ease of access to all the various config files. This 'configFiles' dict is mainly
    used by the user 'editConfigFile' functions that present the 'example' file next to
    the 'user' file for handy editing.
    """
    global configFiles
    # determine the running platform (Linux, Windows or OSX)
    # `- so we can correctly name our 'Default (${platform}).sublime-keymap' file
    curPlatform = sublime.platform()
    if curPlatform == "osx":
        curPlatform = "OSX"
    else:
        curPlatform = curPlatform.capitalize()
    exampleDir = "configExamples"
    templateDir = "configTemplates"
    # We now have enough info to configure our global 'configFiles' dictionary
    configFiles['settings'] = configFileGroup("{}.sublime-settings".format(plugin_canon_name),
                                           "{}/{}.settings-template".format(templateDir, plugin_canon_name),
                                           "{}/Example.sublime-settings".format(exampleDir))
    configFiles['sideBarMenu'] = configFileGroup("Side Bar.sublime-menu",
                                                 "{}/Side Bar.menu-template".format(templateDir),
                                                 "{}/ExampleSideBar.sublime-menu".format(exampleDir))
    configFiles['contextMenu'] = configFileGroup("Context.sublime-menu",
                                                 "{}/Context.menu-template".format(templateDir),
                                                 "{}/ExampleContext.sublime-menu".format(exampleDir))
    configFiles['keyMap'] = configFileGroup("Default ({}).sublime-keymap".format(curPlatform),
                                            "{}/keymap.template".format(templateDir),
                                            "{}/Example.sublime-keymap".format(exampleDir))
    # Set up 4x config files:
    # `- copy 'template' version to 'user' version
    #    unless 'user' version exists or factoryReset=True
    plugin_loose_pkg_dir = pathlib.Path(sublime.packages_path()) / plugin_canon_name
    if not plugin_loose_pkg_dir.is_dir():
        plugin_loose_pkg_dir.mkdir(parents=True, exist_ok=True)
    for key, trisomy in configFiles.items():
        target = plugin_loose_pkg_dir / trisomy.userFile
        if not target.is_file() or factoryReset:
            template = sublime.load_resource("Packages/{}/{}".format(plugin_canon_name, trisomy.templateFile))
            with open(str(target), 'w') as f:
                f.write(template)
                f.close()


class FactoryResetCommand(sublime_plugin.WindowCommand):
    def run(self):
        ans = sublime.ok_cancel_dialog(
            "Do you really want to perform a factory reset?\n\n"
            "This will erase all {} user settings you have implemented, "
            "and return ShellRunner to a virgin install state.\n\n"
            "THIS OPERATION CANNOT BE UNDONE".format(plugin_canon_name),
            "FACTORY RESET"
        )
        if not ans:
            return
        setupConfigFileFramework(factoryReset=True)

def settingsUpdateByProject(projectFileShellRunnerSectionDict, projectFileName):
    """
    Overwrites global: activeSettings dict with entries from ShellRunner section
    `- of the active .sublime-project file.
       Note: As settings from .sublime-projects have higher priority than the
       'ShellRunner.sublime-settings' files, they can be directly written
       to 'activeSettings'
    """
    global activeSettings
    for k,v in projectFileShellRunnerSectionDict.items():
        if k in activeSettings:
            activeSettings[k] = v
        else:
            consoleWarn("Unknown setting [{}] in {} (Ignored)".format(k, projectFileName))

def plugin_loaded():
    """
    1. Sets up global: configFile dictionary + ensures necessary config files are in place
    2. Loads initial set of ShellRunner settings into global: activeSettings dictionary
    """
    def readInUserSettings():
        global activeSettings
        nonlocal srSettings
        # A: Load relevant settings from 'srSettings' object (i.e. ShellRunner.sublime-settings file(s))
        srSettsAsDict = srSettings.to_dict()
        for key, value in srSettsAsDict.items():
            if key in activeSettings:
                activeSettings[key] = value
            else:
                consoleWarn("Unknown setting [{}] (Ignored)".format(key))
        # B: Load any overrides in the 'ShellRunner' section of the active 'sublime-project' file (if present)
        if sublime.active_window().project_data():
            proj_plugin_settings = sublime.active_window().project_data().get(plugin_canon_name, None)
            if proj_plugin_settings:
                # any ShellRunner settings in the .sublime-project file will override same name Default/User settings
                settingsUpdateByProject(proj_plugin_settings, sublime.active_window().project_file_name())


    # Step A:
    setupConfigFileFramework()
    # Step B: Load in a local sublime 'Settings' object with the ShellRunner settings
    # Note: ShellRunner's functions do not access this 'Settings' object directly.
    #    `- ShellRunner uses a callback event on this object to maintain a
    #       global dictionary of settings called 'activeSettings'
    #       ShellRunner's functions read settings directly from 'activeSettings'
    srSettings = sublime.load_settings('ShellRunner.sublime-settings')
    # Step C: Populate global 'activeSettings'
    #      `- First from any ShellRunner.sublime-settings file(s)
    #         Second (and overridingly) from any 'ShellRunner' section of the active 'sublime-project' file   
    readInUserSettings()
    # Step D: Activate a listener for changes to the ShellRunner.sublime-settings file(s)
    #      `- Note: A listener for changes to the active 'sublime-project' file is implemented
    #            `- via a separate EventListener Class (ProjectSettingsUpdateListener)
    srSettings.clear_on_change('callBackKey')
    srSettings.add_on_change('callBackKey', readInUserSettings)



class ProjectSettingsUpdateListener(sublime_plugin.EventListener):
    def on_load_project(self, window):
        global Settings
        proj_plugin_settings = window.project_data().get(plugin_canon_name, None)
        if proj_plugin_settings:
            settingsUpdateByProject(proj_plugin_settings, window.project_file_name())


def editConfigFile(thisGrp, thisWindow):
    targetFile = pathlib.Path(sublime.packages_path()) / plugin_canon_name / thisGrp.userFile
    args = {"base_file": "${packages}/" + plugin_canon_name + "/" + thisGrp.exampleFile,
            "user_file": "{}".format(str(targetFile)),
            }
    thisWindow.run_command('edit_settings', args)


class EditShellrunnerSidebarCommandsCommand(sublime_plugin.WindowCommand):
    def run(self):
        editConfigFile(configFiles['sideBarMenu'], self.window)


class EditShellrunnerContextCommandsCommand(sublime_plugin.WindowCommand):
    def run(self):
        editConfigFile(configFiles['contextMenu'], self.window)


class EditShellrunnerKeyBindingsCommand(sublime_plugin.WindowCommand):
    def run(self):
        editConfigFile(configFiles['keyMap'], self.window)


class EditShellrunnerSettingsCommand(sublime_plugin.WindowCommand):
    def run(self):
        editConfigFile(configFiles['settings'], self.window)


class SidebarEditMenuViewabilityCommand(sublime_plugin.WindowCommand):
    def is_visible(self):
        return activeSettings.get("showSidebarEditMenu", False)


class ContextEditMenuViewabilityCommand(sublime_plugin.WindowCommand):
    def is_visible(self):
        return activeSettings.get("showContextEditMenu", False)

class runSafeSubprocess():
    def __init__(self, cmdTokens: list, **processArgs):
        self.OK = False
        self.cmdResult = None
        self.failStr = ""
        try:
            self.cmdResult = subprocess.run(cmdTokens, **processArgs)
            self.OK = True
        except subprocess.TimeoutExpired:
            self.failStr = ("No text processed due to shell command timeout after {} seconds.\n\n"
                            "The timeout can be set in the range 1-600 seconds.").format(processArgs.get("timeout", "excess"))
        except Exception as err:
            self.failStr = ("Shell command failed as an unexpected exception occurred.\n\n"
                              "Details:: {}\n\n{}".format(err.__class__.__name__, err))



class OpenTerminalHereCommand(sublime_plugin.WindowCommand):
    def __init__(self, window, sideBarMode: bool = False):
        super().__init__(window)
        self.sideBarMode = sideBarMode

    def is_visible(self, **kwargs) -> bool:
        if self.sideBarMode:  # sidebar mode
            return activeSettings.get("showSidebarTerminalCmd", False)
        else:  # window mode (via keybind or context menu)
            return activeSettings.get("showContextTerminalCmd", False)

    def is_enabled(self, **kwargs) -> bool:
        # Always return True for this as allows keybind to work even if menu 'is_visible' is disabled
        return True

    def run(self, **kwargs):
        self.cmdArgs = kwargs
        self.termCmd = activeSettings.get("openTerminalCmd", None)
        if self.termCmd is not None:
            if self.termCmd == "":
                # "openTerminalCmd" is set to an empty string so we can search for a likely term emulator
                foundOne = False
                for termprog in ["xterm", "gnome-terminal", "konsole"]:
                    pathStr = shutil.which(termprog)
                    if pathStr:
                        self.termCmd = pathStr
                        foundOne = True
                        break
                if not foundOne:
                    showShRunnerError("Cannot locate a terminal emulator program on your system.\n\n"
                                        "The \"openTerminalCmd\" is set to an empty string in your ShellRunner "
                                        "settings. This causes ShellRunner to search for a suitable terminal "
                                        "emulator, which has just been done without satisfaction.\n\n"
                                        "Please consider setting \"openTerminalCmd\" to a valid terminal emulator "
                                        "command string.")
                    return

        else:
            showShRunnerError("WARNING: Cannot open a terminal without \"openTerminalCmd\" being defined.\n\n"
                                "Check and change your ShellRunner settings.")
            return

        if not self.sideBarMode:  # window / context mode
            change_dir = self.window.extract_variables().get('file_path', '.')
        else:  # sidebar mode
            pathsList = self.cmdArgs.get('paths', [])
            if pathsList:
                if os.path.isdir(pathsList[0]):
                    change_dir = pathsList[0]
                else:
                    change_dir = os.path.dirname(pathsList[0])
            else:
                change_dir = self.window.extract_variables().get('file_path', '.')
        cmd_array = splitCommand(self.termCmd)
        if cmd_array.OK:
            terminalRun = runSafeSubprocess(cmd_array.tokens, cwd=change_dir)
            # subprocess.run(cmd_array.tokens, cwd=change_dir)
            if not terminalRun.OK:
                showShRunnerError("Error running the \"openTerminalCmd\" command, "
                                  "please check/adjust your ShellRunner settings.\n\n"
                                  "Offending command:: {}\n\n{}".format(self.termCmd, terminalRun.failStr))
        else:
            showShRunnerError("There is a problem with your \"openTerminalCmd\""
                              ". Please check your ShellRunner settings.\n\n{}".format(cmd_array.errorStr))

class WindowOpenTerminalHereCommand(OpenTerminalHereCommand):
    def __init__(self, window):
        super().__init__(window, sideBarMode=False)

class SidebarOpenTerminalHereCommand(OpenTerminalHereCommand):
    def __init__(self, window):
        super().__init__(window, sideBarMode=True)

def buildPathFileDirSidebarItemStrings(argsDict):
    """
    Build space separated string lists of 'files', 'dirs', 'paths' from same-named lists available in args passed
    Sublime Text fills these optional sidebar menu args appropriately when they are given in a sidebar menu command:
    `- e.g. a list arg "dirs": [] will be filled in with a list of dirs currently selected in the sidebar
    Additionally 'lastFile', 'lastDir' and 'lastPath' strings are made which correspond to the most recent selected
    If any of the lists required is not available, the appropriate strings are set to zero length strings.
    """
    addDict = {}
    for addList in ['files', 'dirs', 'paths']:
        gotList = argsDict.get(addList)
        lastSelectedKey = "last" + addList[:-1].capitalize()
        if gotList:
            escapedList = [shlex.quote(a) for a in gotList]
            addDict[addList] = " ".join(escapedList)
            addDict[lastSelectedKey] = escapedList[0]
        else:
            addDict[addList] = ""
            addDict[lastSelectedKey] = ""
    return addDict


def truncateStr(thisStr: str, chopFromStart=False, replacementStr="...", outputLength=35) -> str:
    lenny = len(thisStr)
    if lenny > outputLength:
        chopLen = outputLength - len(replacementStr)
        if chopFromStart:
            chopLen = lenny - chopLen
            thisStr = (replacementStr + thisStr[chopLen:])
        else:
            thisStr = (thisStr[:chopLen] + replacementStr)
    return thisStr

def underlined(bareStr: str) -> str:
    return bareStr + "\n" + "-" * len(bareStr)

class DebugLogger():
    def __init__(self, commandStr, initPrefix="", consoleMode=True, tabReport=False):
        self.fullCommandStr = commandStr
        self.cs = truncateStr(commandStr)
        self.prefix = initPrefix
        self.consoleMode = consoleMode
        self.tabReport = tabReport
        self.report = "ShellRunner Command Debug Report\n" \
                      "================================\n\n" \
                      "Bare Shell Command: {}\n\n{}\n".format(self.fullCommandStr,
                                                        underlined(self.prefix))


    def log(self, logmsg=""):
        if self.consoleMode:
            print("{}:[[CMD:{}]]:{}".format(self.prefix, self.cs, logmsg))
        if self.tabReport:
            self.report += "> {}\n".format(logmsg)

    def setPrefix(self, newPrefix):
        self.prefix = newPrefix
        self.report += "\n{}\n".format(underlined(self.prefix))

    def finalReport(self):
        self.setPrefix("Processing Completed")
        self.log("DEBUG Session Ended")
        if self.tabReport:
            self.output_file = sublime.active_window().new_file()
            self.output_file.set_name("ShellRunner Debug")
            self.output_file.run_command('view_insert_big_text', {'pos': self.output_file.size(), 'text': self.report})



def deListCmd(cmdMightBeList):
    if isinstance(cmdMightBeList, list):
        return "".join(cmdMightBeList)
    else:
        return cmdMightBeList

def amIEnabled(visArgs, windowVars={}, sbMode=True):
    enablementRep = ""
    def buildRep(addStr):
        nonlocal enablementRep
        enablementRep += addStr
    visMe = True
    DEBUG = visArgs.get('consoleDebug', False)
    DEBUG and buildRep('*************************************\n')
    DEBUG and buildRep("ShellRunner Command Enablement Check:\n"
                       "=====================================\n" 
                       "- Target Command: {}\n".format(truncateStr(deListCmd(visArgs.get('shellCommand', "NO COMMAND!")))))
    targetExtns = visArgs.get('targetExtensions', False)
    if sbMode:
        DEBUG and buildRep("- Sidebar Menu Mode Check\n")
        dirOnly = visArgs.get('dirOnly', False)
        extraForDirs = "(or dir) "
    else:
        DEBUG and buildRep("- Context Menu or Key Bind Mode Check\n")
        # the 'dirOnly' arg has no place in a 'window' command, ignore it if is set
        dirOnly = False
        extraForDirs = ""
    if targetExtns:
        DEBUG and buildRep("- File extension match required\n")
        DEBUG and buildRep("- Extensions to match = {}\n".format(targetExtns))
        visMe = False  # until proven otherwise
        # NB: the initial dot/period must be included for each of targetExtensions e.g. ".jpg" not "jpg"
        #    ` multipart extensions are not catered for e.g. ".tar.gz" will never match, but ".gz" will
        if sbMode:
            lastSelectedSidebarPath = ""
            DEBUG and buildRep("-- Looking for last selected sidebar file via [files] arg\n")
            sbFiles = visArgs.get('files', False)
            if sbFiles:
                lastSelectedSidebarPath = sbFiles[0]
                DEBUG and buildRep('-- Last selected sidebar file to match = {}\n'.format(truncateStr(lastSelectedSidebarPath, outputLength=25, chopFromStart=True)))
            else:
                DEBUG and buildRep("-- [files] arg not available, looking via [paths] arg\n")
                sbPaths = visArgs.get('paths', False)
                if sbPaths:
                    lastSelectedSidebarPath = sbPaths[0]
                    DEBUG and buildRep('-- Last selected sidebar path to match = {}\n'.format(truncateStr(lastSelectedSidebarPath, outputLength=25, chopFromStart=True)))
                    if os.path.isfile(sbPaths[0]):
                        DEBUG and buildRep('-- Path found is a file\n')
                        lastSelectedSidebarPath = sbPaths[0]
                    else:
                        DEBUG and buildRep('Path found is NOT a file\n')
                else:
                    DEBUG and buildRep("-- WARNING: No sidebar 'files':[] or 'paths': [] args via which to acquire file to match\n")
            fileToCheckExtn = lastSelectedSidebarPath
        else:  # not sidebar mode i.e. key bind or context menu
            fileToCheckExtn = windowVars.get('file')
            DEBUG and buildRep('-- Active window file to match = {}\n'.format(truncateStr(fileToCheckExtn, outputLength=25, chopFromStart=True)))
        if fileToCheckExtn:
            # targetExtn entries must be preceeded by a dot to work
            haveExtn = os.path.splitext(fileToCheckExtn)[1]
            if haveExtn in targetExtns:
                DEBUG and buildRep('-- Target file extension ({}) matches\n'.format(haveExtn))
                visMe = True
            else:
                DEBUG and buildRep('-- Target file extension ({}) does not match\n'.format(haveExtn))
        else:
            DEBUG and buildRep('-- No target file found on which to perform match check.\n')
    elif dirOnly:
        DEBUG and buildRep('- Command valid only for directories i.e. "dirOnly" set in args (must be sidebar mode)\n')
        visMe = False
        if visArgs.get('dirs', False):
            DEBUG and buildRep('- Directory detected in sidebar selections (via [dirs] arg)\n')
            # If any directory is selected
            visMe = True
        else:
            DEBUG and buildRep('- No sidebar directory selection detected (is [dirs] arg provided)\n')
    else:
        DEBUG and buildRep("No file extension {}restrictions found in args".format(extraForDirs))
    DEBUG and buildRep('Command Visible/Enabled = {}\n'.format(visMe))
    DEBUG and buildRep('[Note: Sublime Text runs enablement checks twice under some circumstances,]\n')
    DEBUG and buildRep('[so do not worry if you see this message printed two times]\n')
    DEBUG and buildRep('*************************************\n')
    DEBUG and print("{}".format(enablementRep))
    return visMe



class ViewInsertBigTextCommand(sublime_plugin.TextCommand):
    """
    A sublime_plugin.TextCommand is reqd. for inserting large amounts of text into a document
    The run_command('insert', {"characters": rxText}) option is fine for small amounts of text
    `- but goes a bit awry with a large quantity of characters
    """
    def run(self, edit, pos, text):
        self.view.insert(edit, pos, text)


class runShellCommand(Thread):
    """
    Run a shell command as a threaded subprocess, according to parameters given in 'passedArgs'
    Distinguish between two types of command, dependent on whether a target 'view' is passed to __init__:
    `- A text command, whose output we are interested in capturing and putting somewhere e.g. a new tab
     - A simple spawned command, which we can simply run and leave
    Captured text from text commands is output to the given destination(s) unless that destination is msgBox
    `- as msgBox output is stored within the object for outputting by a thread manager on thread completion.
    If an error/exception occurs then an error msg is stored in an object attribute (self.errStr) which is
    `- also output by a thread manager (in a sublime message_dialog box) on thread completion.
    """
    def __init__(self, passedArgs, targetView={}, debugger=None):
        self.cmdArgs = passedArgs
        self.DEBUG = self.cmdArgs.get('consoleDebug', False) or self.cmdArgs.get('tabDebugReport', False)
        if debugger is None:
            self.DEBUG = False
            self.db = None
        else:
            self.db = debugger
        # if a view is passed in this means we are dealing with a text command not a spawned command
        self.targetView = targetView
        self.isTextCommand = bool(self.targetView)

        self.commandSuccess = False
        self.outputMsgBox = None
        self.errStr = None
        Thread.__init__(self)

    def run(self):
        if self.DEBUG:
            self.db.setPrefix("ShellRunner Run Phase")
            if self.isTextCommand:
                self.db.log('We believe we have a text command to run (not a spawn command)')
            else:
                self.db.log('We believe we have a spawn command to run (not a text command)')
        # try:
        processArgs = {}
        processArgs["cwd"] = self.cmdArgs["initChangeDir"]
        if self.cmdArgs["cleanShellEnv"]:
            exportEnv = {}
        else:
            exportEnv = os.environ.copy()
        exportEnv.update(self.cmdArgs["exportEnv"])
        processArgs["env"] = exportEnv
        if self.isTextCommand:
            if self.cmdArgs["cmdCombineOutputStreams"]:
                errDest = subprocess.STDOUT
            else:
                errDest = subprocess.PIPE
            processArgs["stdout"] = subprocess.PIPE
            processArgs["stderr"] = errDest
            processArgs["encoding"] = 'UTF-8'
            processArgs["timeout"] = self.cmdArgs["textCmdTimeout"]

        self.DEBUG and self.db.log("Compiled shell command args::\n{}\n".format(pp.pformat(processArgs)))
        self.DEBUG and self.db.log("Running shell command NOW:")
        runObj = runSafeSubprocess(self.cmdArgs["shellCommand"], **processArgs)
        if not runObj.OK:
            self.errStr = ("Shell command failed. No text processed.\n\n"
                              "Offending command:: {}\n\n"
                              "Failure Details:: {}\n\n{}".format(self.termCmd, runObj.failStr))
            return
            # cmdRes = subprocess.run(self.cmdArgs["shellCommand"], **processArgs)
        # except subprocess.TimeoutExpired:
            # self.errStr = ("No text processed due to shell command timeout after {} seconds.\n\n"
                            # "The timeout can be set in the range 1-600 seconds.\n\n"
                              # "Offending command:: {}".format(self.cmdArgs["textCmdTimeout"],
                                                             # self.cmdArgs["origCmd50CharLabel"]))
            # self.DEBUG and self.db.log("Error running shell command: {}".format(self.errStr)) 
            # return
        # except Exception as err:
            # self.errStr = ("Shell command failed as an unexpected exception occurred.\n\n"
                              # "Offending command:: {}\n\n"
                              # "Details:: {}\n\n{}".format(self.cmdArgs["origCmd50CharLabel"], err.__class__.__name__, err))
            # self.DEBUG and self.db.log("Error running shell command: {}".format(self.errStr)) 
            # return

        self.DEBUG and self.db.log("Cmd completed with exit code: {}".format(runObj.cmdResult.returncode))
        if self.isTextCommand:
            self.DEBUG and self.db.log("Starting Text Command Post Processing")
            if self.cmdArgs["textCmdStopOnErr"]:
                if runObj.cmdResult.returncode != 0:
                    textOp = "stdout:: " + runObj.cmdResult.stdout
                    if not self.cmdArgs["cmdCombineOutputStreams"]:
                        textOp += "\nstderr:: {}".format(runObj.cmdResult.stderr)
                    self.errStr = ("No text processed due to error code {} being returned from the shell.\n\n"
                                      "Offending command:: {}\n\n{}".format(runObj.cmdResult.returncode, 
                                                                            self.cmdArgs["origCmd50CharLabel"],
                                                                            textOp))
                    return
            elif runObj.cmdResult.returncode != 0:
                self.DEBUG and self.db.log("Non-zero shell exit code ({}) ignored as \"textCmdStopOnErr\" is false.".format(runObj.cmdResult.returncode))
            self.commandSuccess = True
            rxText = runObj.cmdResult.stdout
            if rxText:
                self.DEBUG and self.db.log("Outputting text to {}".format(self.cmdArgs["outputTo"]))
                for destination in self.cmdArgs["outputTo"]:
                    if destination == "newTab":
                        self.output_file = sublime.active_window().new_file()
                        if self.cmdArgs["newTabName"]:
                            self.output_file.set_name(self.cmdArgs["newTabName"])
                        self.output_file.run_command('view_insert_big_text', {'pos': self.output_file.size(), 'text': rxText})
                    elif destination == "sublConsole":
                        sublime.active_window().run_command('show_panel', {"panel": "console", "toggle": False})
                        print(rxText)
                    elif destination == "cursorInsert":
                        sel = self.targetView.sel();
                        for s in sel:       
                            self.targetView.run_command('view_insert_big_text', {'pos': s.a, 'text': rxText})
                    elif destination == "msgBox":
                        # save rxText in an object attribute for processing after this thread is completed
                        self.outputMsgBox = rxText
                    elif destination == "clip":
                        sublime.set_clipboard(rxText)
                        # subprocess.Popen(('xsel', '-i', '-b'), stdin=subprocess.PIPE).communicate(bytearray(rxText, 'utf-8'))
        else:
            self.DEBUG and self.db.log("Non Text Command spawning complete")
            self.commandSuccess = True


class ThreadProgress():

    """
    Animates an indicator, [=   ], in the status area while a thread runs
    :param thread:
        The thread to track for activity
    :param message:
        The message to display next to the activity indicator
    :param success_message:
        The message to display once the thread is complete
    """

    def __init__(self, thread, message, success_message):
        self.thread = thread
        self.message = message
        self.success_message = success_message
        self.addend = 1
        self.size = 8
        self.last_view = None
        self.window = None
        sublime.set_timeout(lambda: self.run(0), 100)

    def run(self, i):
        if self.window is None:
            self.window = sublime.active_window()
        active_view = self.window.active_view()

        if self.last_view is not None and active_view != self.last_view:
            self.last_view.erase_status('_shellRunner')
            self.last_view = None

        if not self.thread.is_alive():
            def cleanup():
                active_view.erase_status('_shellRunner')
            # if hasattr(self.thread, 'textOut') and self.thread.textOut is None:
            # if self.thread.textOut is None:
            if not self.thread.commandSuccess:
                cleanup()
                if self.thread.errStr is not None:
                    showShRunnerError(self.thread.errStr)
                return
            active_view.set_status('_shellRunner', self.success_message)
            if self.thread.outputMsgBox is not None:
                sublime.message_dialog(self.thread.outputMsgBox)
            sublime.set_timeout(cleanup, 1000)
            return

        before = i % self.size
        after = (self.size - 1) - before

        active_view.set_status('_shellRunner', '%s [%s=%s]' % (self.message, ' ' * before, ' ' * after))
        if self.last_view is None:
            self.last_view = active_view

        if not after:
            self.addend = -1
        if not before:
            self.addend = 1
        i += self.addend

        sublime.set_timeout(lambda: self.run(i), 100)


class ShellRunnerCommand(sublime_plugin.WindowCommand):

    def __init__(self, window, sbMode=False, spawnMode=False):
        super().__init__(window)
        self.sideBarMode = sbMode
        self.spawnMode = spawnMode
        self.DEBUG = False
        self.db = None
        self.origCmd200CharStr = "<cmd not yet defined: pre-processing>"
        self.cmdArgs = {}

    def focus(self, window_to_move_to):
        active_view = window_to_move_to.active_view()
        if active_view is not None:
            window_to_move_to.focus_view(active_view)

    def reportArgError(self, errorStr):
        contextStr = "\n\nOffending command:: {}".format(self.origCmd200CharStr)
        showShRunnerError('Shell command arg error:: {}{}'.format(errorStr, contextStr))
        self.DEBUG and self.db.log("Fatal error processing shell command arguments: {}".format(errorStr))

    def sanitiseSpawnCmdArgs(self):
        # :Step A1: Check and build the run command
        runcmd = deListCmd(retrieveSetting("shellCommand", self.cmdArgs))
        if not runcmd or not isinstance(runcmd, str):
            self.reportArgError("Zero length or incorrectly defined \"shellCommand\"::\n\n{}".format(runcmd))
            return False
        else:
            # We have our base shellCommand, now we need to expand any substitution variables it contains
            # `- so we must build a dictionary of substitution variables that can be expanded in our command
            #  - This is done in steps A to F below
            # A: get the sublime window env. placeholder variables
            # `- e.g. ${packages} ${platform} ${file} ${file_path} ${file_name} ${file_base_name} ${project_extension}
            #  - ${file_extension} ${folder} ${project} ${project_path} ${project_name} ${project_base_name}
            self.DEBUG and self.db.log("Compiling substitution dictionary (to replace any placeholders in our base command)")
            replacementVars = self.window.extract_variables()
            # B: Use shell env vars in substitution string if cleanShellEnv is not set
            self.cmdArgs["cleanShellEnv"] = retrieveSetting("cleanShellEnv", self.cmdArgs, activeSettings, default=False)
            if not self.cmdArgs["cleanShellEnv"]:
                self.DEBUG and self.db.log("Including shell env vars as substitution vars (\"cleanShellEnv\" is not set)")
                replacementVars.update(os.environ.copy())
            else:
                self.DEBUG and self.db.log("Including shell env vars as substitution vars (\"cleanShellEnv\" is not set)")
            # C: if we're in sidebar mode: compile available strings of side bar selected items
            # `- ${paths}, ${lastPath}, ${dirs}, ${lastDir}, ${files}, ${lastFile}
            #  - (all as escaped 'shell friendly' strings) 
            if self.sideBarMode:
                replacementVars.update(buildPathFileDirSidebarItemStrings(self.cmdArgs))
            # D: get any extra, user defined "global" substitution variables
            substVars = retrieveSetting("extraGlobalSubstVars", activeSettings, default={})
            # E: get any extra, user defined "local" command-arg substitution variables
            substVars.update(retrieveSetting("extraCmdSubstVars", self.cmdArgs, default={}))
            replacementVars.update(substVars)
            # F: build a dictionary of new env vars from global and cmd args settings
            # `- we use it here for substitution vars, later it will update the shell environment
            self.cmdArgs["exportEnv"] = retrieveSetting("extraGlobalShellEnvVars", activeSettings, default={})
            self.cmdArgs["exportEnv"].update(retrieveSetting("extraCmdShellEnvVars", self.cmdArgs, default={}))
            replacementVars.update(self.cmdArgs["exportEnv"])
            # F: add one (or all) selected region(s), (and separated by 'multiSelSeparator') - ${selText}
            sel = self.window.active_view().sel()
            replacementVars["selText"] = ""
            selSeparator = retrieveSetting("multiSelSeparator", self.cmdArgs, activeSettings, default=" ")
            selLiteral = retrieveSetting("selAsLiteralStr", self.cmdArgs, activeSettings, default=False)
            buildAll = []
            for s in sel:
                foundStr = self.window.active_view().substr(s)
                if foundStr:
                    buildAll += [foundStr]
            if buildAll:
                replacementVars["selText"] = selSeparator.join(buildAll)
            if selLiteral:
                replacementVars["selText"] = replacementVars["selText"].replace("\\", "\\\\")
                replacementVars["selText"] = "$'" + replacementVars["selText"].replace("'", "\\'") + "'"
            
            self.DEBUG and self.db.log("Substitution dictionary compiled as::\n{}\n".format(pp.pformat(replacementVars)))

            # split command into shell tokens (for subprocess) BEFORE performing var substitution on individual tokens
            self.DEBUG and self.db.log("Splitting full shell command into 'tokens' for running purposes")
            cmdObj = splitCommand(runcmd)
            if cmdObj.OK:
                self.cmdArgs["shellCommand"] = cmdObj.tokens
            else:
                self.reportArgError(cmdObj.errorStr)
                self.DEBUG and self.db.log("Error during splitting/tokenising process: {}".format(cmdObj.errorStr))
                return False
            self.DEBUG and self.db.log("Pre-substitution  \"shellCommand\" tokens:\n{}\n".format(pp.pformat(self.cmdArgs["shellCommand"])))

            # perform variable substitution on each token
            for count, shellToken in enumerate(self.cmdArgs["shellCommand"]):
                self.cmdArgs["shellCommand"][count] = sublime.expand_variables(shellToken, replacementVars)
            self.DEBUG and self.db.log("Post-substitution \"shellCommand\" tokens:\n{}\n".format(pp.pformat(self.cmdArgs["shellCommand"])))

        self.origCmd200CharStr = truncateStr(runcmd, outputLength=200)
        # self.cmdArgs["origCmd200CharLabel"] = truncateStr(runcmd, outputLength=200)
        self.cmdArgs["origCmd50CharLabel"] = truncateStr(runcmd, outputLength=50)
        
        # :Step A2: Check 'initChangeDir' setting to see if we should change dir, to file loc, before running command
        # Note: We read this as 'boolean' but change it to a path (str) of the directory into which we'll cd
        doChgDir = retrieveSetting("initChangeDir", self.cmdArgs, activeSettings, default=True)
        if not isinstance(doChgDir, bool):
            self.reportArgError("\"initChangeDir\" must be defined [true or false (type=bool)].\n\n"
                                "The current setting [{} (type={})] is invalid.".format(doChgDir, type(doChgDir)))
            return False
        self.DEBUG and self.db.log("\"initChangeDir\" (orig bool) = {}".format(doChgDir))
        if doChgDir:
            self.cmdArgs["initChangeDir"] = self.window.extract_variables().get('file_path', '.')
        else:
            self.cmdArgs["initChangeDir"] = "."
        self.DEBUG and self.db.log("\"initChangeDir\" (as dir)  = {}".format(self.cmdArgs["initChangeDir"]))

        return True

    def sanitiseTextCmdArgs(self):
        # first check all the basic args (which are all that spawned cmds require)
        if not self.sanitiseSpawnCmdArgs():
            return False

        # now check additional args that are relevant to the text manipulation commands
        # :Step B1: Check 'outputTo' is defined correctly:
        output_dest_list = retrieveSetting("outputTo", self.cmdArgs, activeSettings, default=[])
        # be careful with the null setting in json, which is read as None into python
        if isinstance(output_dest_list, str) or output_dest_list is None:
            output_dest_list = [output_dest_list]
        for output_dest in output_dest_list:
            if output_dest not in outputToValues:
                self.reportArgError("\"outputTo\" contains an incorrect entry <\"{}\">."
                                    "\n\n\"outputTo\" must be set to one (or a list) of: {}.".format(output_dest, outputToJsonKeyStr))
                return False
        if not output_dest_list:
            self.reportArgError("No \"outputTo\" destination is defined.")
            return False
        self.cmdArgs["outputTo"] = list(set(output_dest_list))  # ensure list contains no duplicates
        self.DEBUG and self.db.log("\"outputTo\" (as list)  = {}".format(self.cmdArgs["outputTo"]))

        # :Step B2: Prepare 'newTabName' from settings (if this is None, that's OK, we just have a nameless new tab)
        self.cmdArgs["newTabName"] = retrieveSetting("outputTabName", self.cmdArgs, activeSettings)
        self.DEBUG and self.db.log("\"newTabName\"  = {}".format(self.cmdArgs["newTabName"]))

        # :Step B3: Check 'cmdCombineOutputStreams' setting to see if we should merge stdout and stderr from command
        self.cmdArgs["cmdCombineOutputStreams"] = retrieveSetting("cmdCombineOutputStreams", self.cmdArgs, activeSettings, default=False)
        if not isinstance(self.cmdArgs["cmdCombineOutputStreams"], bool):
            self.reportArgError("\"cmdCombineOutputStreams\" must be defined [true or false (type=bool)].\n\n"
                    "The current setting [{} (type={})] is invalid.".format(self.cmdArgs["cmdCombineOutputStreams"], type(self.cmdArgs["cmdCombineOutputStreams"])))
            return False
        self.DEBUG and self.db.log("\"cmdCombineOutputStreams\"  = {}".format(self.cmdArgs["cmdCombineOutputStreams"]))

        # :Step B4: Check 'textCmdTimeout' setting to see if we should set a timeout for our command    
        self.cmdArgs["textCmdTimeout"] = retrieveSetting("textCmdTimeout", self.cmdArgs, activeSettings, default=10)
        if not isinstance(self.cmdArgs["textCmdTimeout"], int):
            self.reportArgError("\"textCmdTimeout\" should contain the number of seconds, as an integer, after which to timeout the command.\n\n"
                    "The current setting [{} (type={})] is invalid.".format(self.cmdArgs["textCmdTimeout"], type(self.cmdArgs["textCmdTimeout"])))
            return False
        elif (self.cmdArgs["textCmdTimeout"] <= 0) or (self.cmdArgs["textCmdTimeout"] > 600):
            self.cmdArgs["textCmdTimeout"] = 600
        self.DEBUG and self.db.log("\"textCmdTimeout\"  = {}".format(self.cmdArgs["textCmdTimeout"]))

        # :Step B5: Check 'textCmdStopOnErr' setting to see if we should stop on shell errors    
        self.cmdArgs["textCmdStopOnErr"] = retrieveSetting("textCmdStopOnErr", self.cmdArgs, activeSettings, default=True)
        if not isinstance(self.cmdArgs["textCmdStopOnErr"], bool):
            self.reportArgError("\"textCmdStopOnErr\" must be defined [true or false (type=bool)].\n\n"
                    "The current setting [{} (type={})] is invalid.".format(self.cmdArgs["textCmdStopOnErr"], type(self.cmdArgs["textCmdStopOnErr"])))
            return False
        self.DEBUG and self.db.log("\"textCmdStopOnErr\"  = {}".format(self.cmdArgs["textCmdStopOnErr"]))

        self.DEBUG and self.db.log("Shell command arguments ALL CHECKED OK")
        # :All checks OK. self.cmdArgs prepared for running phase
        return True

    def run(self, **kwargs):
        self.cmdArgs = kwargs
        # sublime.message_dialog('cmdArgs: {}'.format(self.cmdArgs))
        self.origCmd200CharStr = "<cmd not yet defined: pre-processing>"
        self.DEBUG = False
        self.db = None
        if self.cmdArgs.get('consoleDebug', False) or self.cmdArgs.get('tabDebugReport', False):
            self.DEBUG = True
            self.db = DebugLogger(deListCmd(self.cmdArgs.get('shellCommand', "NO COMMAND!")),
                                    initPrefix="ShellRunner Check Cmd Args",
                                    consoleMode = self.cmdArgs.get('consoleDebug', False),
                                    tabReport = self.cmdArgs.get('tabDebugReport', False))

        self.DEBUG and self.db.log("DUMPING THE INITIAL ARGS OF THE COMMAND WE ARE AIMING TO RUN:\n{}\n".format(pp.pformat(self.cmdArgs)))
        # Sanitise self.cmdArgs before running the command
        if self.spawnMode:
            if not self.sanitiseSpawnCmdArgs():
                self.DEBUG and self.db.finalReport()
                return
            else:
                # All sanitised OK, so spawn the command
                doSpawnCommand = runShellCommand(self.cmdArgs, debugger=self.db)
                doSpawnCommand.start()
        else:
            if not self.sanitiseTextCmdArgs():
                self.DEBUG and self.db.finalReport()
                return
            else:
                # All sanitised OK, so run the command as a thread and show its progress in the status bar
                doTxtCommand = runShellCommand(self.cmdArgs, self.window.active_view(), debugger=self.db)
                doTxtCommand.start()
                status_message = "ShellRunner running: {}".format(self.cmdArgs["origCmd50CharLabel"])
                ThreadProgress(doTxtCommand, status_message, "ShellRunner command completed OK")
                self.focus(self.window)

        self.DEBUG and self.db.finalReport()

    def is_visible(self, **tkwargs):
        self.visArgs = tkwargs
        return True
        
    def is_enabled(self, **tkwargs):
        self.visArgs = tkwargs
        return amIEnabled(self.visArgs, windowVars=self.window.extract_variables(), sbMode=self.sideBarMode)

class SidebarShellrunnerTextCommandCommand(ShellRunnerCommand):
    def __init__(self, window):
        super().__init__(window, sbMode=True, spawnMode=False)

class WindowShellrunnerSpawnCommandCommand(ShellRunnerCommand):
    def __init__(self, window):
        super().__init__(window, sbMode=False, spawnMode=True)

class SidebarShellrunnerSpawnCommandCommand(ShellRunnerCommand):
    def __init__(self, window):
        super().__init__(window, sbMode=True, spawnMode=True)

class WindowShellrunnerTextCommandCommand(ShellRunnerCommand):
    def __init__(self, window):
        super().__init__(window, sbMode=False, spawnMode=False)
