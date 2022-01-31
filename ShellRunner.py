import os
import pathlib
import sublime
import sublime_plugin
import subprocess
import shlex
import shutil
import time
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


def splitCommand(cmdStr):
    return shlex.split(cmdStr, posix=True)


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


def ensureUserFilesArePresent(factoryReset=False):
    global configFiles

    curPlatform = sublime.platform()
    if curPlatform == "osx":
        curPlatform = "OSX"
    else:
        curPlatform = curPlatform.capitalize()
    configFiles['settings'] = configFileGroup("{}.sublime-settings".format(plugin_canon_name),
                                           "{}.settings-template".format(plugin_canon_name),
                                           "Example.sublime-settings")
    configFiles['sideBarMenu'] = configFileGroup("Side Bar.sublime-menu",
                                                 "Side Bar.menu-template",
                                                 "ExampleSideBar.sublime-menu")
    configFiles['contextMenu'] = configFileGroup("Context.sublime-menu",
                                                 "Context.menu-template",
                                                 "ExampleContext.sublime-menu")
    configFiles['keyMap'] = configFileGroup("Default ({}).sublime-keymap".format(curPlatform),
                                            "keymap.template",
                                            "Example.sublime-keymap")
    plugin_loose_pkg_dir = pathlib.Path(sublime.packages_path()) / plugin_canon_name
    if not plugin_loose_pkg_dir.is_dir():
        plugin_loose_pkg_dir.mkdir(parents=True, exist_ok=True)
    # sublime.message_dialog("File names: {}".format(configFiles))
    for key, trisomy in configFiles.items():
        target = plugin_loose_pkg_dir / trisomy.userFile
        if not target.is_file() or factoryReset:
            template = sublime.load_resource("Packages/{}/{}".format(plugin_canon_name, trisomy.templateFile))
            with open(str(target), 'w') as f:
                f.write(template)
                f.close()

def settingsUpdateByProject(updict={}, projectFile="Unknown"):
    global activeSettings
    for k,v in updict.items():
        if k in activeSettings:
            activeSettings[k] = v
            # print("Project File: {} has updated setting {} to {}".format(projectFile, k, v))
        else:
            print("Warning: Unknown ShellRunner setting [{}] in {} (Ignored)".format(k, projectFile))
    # print("After settingsUpdateByProject, activeSettings = {}".format(activeSettings))

def plugin_loaded():

    ensureUserFilesArePresent()
    srSettings = sublime.load_settings('ShellRunner.sublime-settings')

    def readInProjectSettings():
        if sublime.active_window().project_data():
            proj_plugin_settings = sublime.active_window().project_data().get(plugin_canon_name, None)
            if proj_plugin_settings:
                # any ShellRunner settings in the .sublime-project file will override same name Default/User settings
                settingsUpdateByProject(proj_plugin_settings, sublime.active_window().project_file_name())

    def readInUserSettings():
        global activeSettings
        for key, value in activeSettings.items():
            pulledInAfresh = srSettings.get(key)
            print("{}: {}".format(key, pulledInAfresh))
            if pulledInAfresh is not None:
                print('`- saved as not None')
                activeSettings[key] = pulledInAfresh
        print("After settings update by ShellRunner.sublime-settings:\n`- Settings = {}".format(activeSettings))
        readInProjectSettings()

    # read initial setting
    readInUserSettings()
    # listen for changes
    srSettings.add_on_change('ShellRunner', readInUserSettings)

    

class FactoryResetCommand(sublime_plugin.WindowCommand):
    def run(self):
        ans = sublime.ok_cancel_dialog(
            "Do you really want to perform a factory reset?\n\n"
            "This will erase all {} user settings you have implemented, "
            "and return ShellRunner to a virgin install state.\n\n"
            "THIS OPERATION CANNOT BE UNDONE".format(plugin_canon_name)
        )
        if not ans:
            return
        ensureUserFilesArePresent(factoryReset=True)


class ProjectSettingsUpdateListener(sublime_plugin.EventListener):
    def on_load_project(self, window):
        global Settings
        proj_plugin_settings = window.project_data().get(plugin_canon_name, None)
        if proj_plugin_settings:
            # any ShellRunner settings in the .sublime-project file will override same name Default/User settings
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


class OpenTerminalHereCommand(sublime_plugin.WindowCommand):
    def __init__(self, window, sideBarMode=None):
        super().__init__(window)
        self.sideBarMode = sideBarMode

    def is_visible(self, **kwargs):
        if self.sideBarMode:  # sidebar mode
            return activeSettings.get("showSidebarTerminalCmd", False)
        else:  # window mode (via keybind or context menu)
            return activeSettings.get("showContextTerminalCmd", False)
        # return bool(self.termCmd) and self.settingsSayShow

    def is_enabled(self, **kwargs):
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
            print("ShellRunner WARNING: Trying to open a terminal without \"openTerminalCmd\" being defined.")
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
        subprocess.Popen(cmd_array, cwd=change_dir)

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


def truncateStr(thisStr, chopFront=False, dotStr="...", length=35):
    lenny = len(thisStr)
    if lenny > length:
        chopLen = length - len(dotStr)
        if chopFront:
            chopLen = lenny - chopLen
            thisStr = (dotStr + thisStr[chopLen:])
        else:
            thisStr = (thisStr[:chopLen] + dotStr)
    return thisStr


class DebugLogger():
    def __init__(self, commandStr, prefix="", consoleMode=True, tabReport=False):
        self.cs = truncateStr(commandStr)
        self.prefix = prefix
        self.consoleMode = consoleMode
        self.tabReport = tabReport
        self.report = ""

    def log(self, logmsg=""):
        if self.consoleMode:
            print("{}:[[CMD:{}]]:{}".format(self.prefix, self.cs, logmsg))
        if self.tabReport:
            self.report += "{}:[[CMD:{}]]:{}\n".format(self.prefix, self.cs, logmsg)

    def finalReport(self):
        self.output_file = sublime.active_window().new_file()
        self.output_file.set_name("SR Debug Report")
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
    DEBUG = True
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
                DEBUG and buildRep('-- Last selected sidebar file to match = {}\n'.format(truncateStr(lastSelectedSidebarPath, length=25, chopFront=True)))
            else:
                DEBUG and buildRep("-- [files] arg not available, looking via [paths] arg\n")
                sbPaths = visArgs.get('paths', False)
                if sbPaths:
                    lastSelectedSidebarPath = sbPaths[0]
                    DEBUG and buildRep('-- Last selected sidebar path to match = {}\n'.format(truncateStr(lastSelectedSidebarPath, length=25, chopFront=True)))
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
            DEBUG and buildRep('-- Active window file to match = {}\n'.format(truncateStr(fileToCheckExtn, length=25, chopFront=True)))
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
    DEBUG and buildRep('*************************************\n')
    DEBUG and print("{}".format(enablementRep))
    return visMe


class argChecker():

    def __init__(self, cmdArgs):
        self.cmdArgs = cmdArgs
        self.origCmd200CharStr = "<cmd not yet defined: pre-processing>"

    def reportArgError(self, errorStr):
        contextStr = "\n\nOffending command:: {}".format(self.origCmd200CharStr)
        showShRunnerError('Shell command arg error:: {}{}'.format(errorStr, contextStr))

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
            replacementVars = self.window.extract_variables()
            # B: Use shell env vars in substitution string if cleanShellEnv is not set
            self.cmdArgs["cleanShellEnv"] = retrieveSetting("cleanShellEnv", self.cmdArgs, activeSettings, default=False)
            if not self.cmdArgs["cleanShellEnv"]:
                replacementVars.update(os.environ.copy())
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
            
            self.DEBUG and self.db.log("Command substitution dictionary compiled as: {}".format(replacementVars))

            # split command into shell tokens (for subprocess) BEFORE performing var substitution on individual tokens
            self.DEBUG and self.db.log("Splitting full cmd str (( {} ))".format(runcmd))
            try:
                self.cmdArgs["shellCommand"] = splitCommand(runcmd)
            except Exception as err:
                self.reportArgError("Command was not run as an unexpected exception occurred in splitting it for the shell. "
                                  "Please check your command is formatted correctly.\n\n"
                                  "Split attempted on:: {}\n\n"
                                  "Details:: {}\n\n{}".format(runcmd, err.__class__.__name__, err))
                return False
            self.DEBUG and self.db.log("Pre-substitution  \"shellCommand\" tokens: {}".format(self.cmdArgs["shellCommand"]))

            # perform variable substitution on each token
            for count, shellToken in enumerate(self.cmdArgs["shellCommand"]):
                self.cmdArgs["shellCommand"][count] = sublime.expand_variables(shellToken, replacementVars)
            self.DEBUG and self.db.log("Post-substitution \"shellCommand\" tokens: {}".format(self.cmdArgs["shellCommand"]))

        self.origCmd200CharStr = truncateStr(runcmd, length=200)
        # self.cmdArgs["origCmd200CharLabel"] = truncateStr(runcmd, length=200)
        self.cmdArgs["origCmd50CharLabel"] = truncateStr(runcmd, length=50)
        
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

        # :All checks OK. self.cmdArgs prepared for running phase
        return True


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
    def __init__(self, passedArgs, targetView={}):
        self.cmdArgs = passedArgs
        self.DEBUG = self.cmdArgs.get('consoleDebug', False)
        self.db = DebugLogger(self.cmdArgs["origCmd50CharLabel"], prefix="ShellRunner Run")
        # if a view is passed in this means we are dealing with a text command not a spawned command
        self.targetView = targetView
        self.isTextCommand = bool(self.targetView)

        self.commandSuccess = False
        self.outputMsgBox = None
        self.errStr = None
        Thread.__init__(self)

    def run(self):
        try:
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

            self.DEBUG and self.db.log("Subprocess Args: {}".format(processArgs))
            cmdRes = subprocess.run(self.cmdArgs["shellCommand"], **processArgs)
        except subprocess.TimeoutExpired:
            self.errStr = ("No text processed due to shell command timeout after {} seconds.\n\n"
                            "The timeout can be set in the range 1-600 seconds.\n\n"
                              "Offending command:: {}".format(self.cmdArgs["textCmdTimeout"],
                                                              self.cmdArgs["origCmd50CharLabel"]))
            return
        except Exception as err:
            self.errStr = ("Shell command failed as an unexpected exception occurred.\n\n"
                              "Offending command:: {}\n\n"
                              "Details:: {}\n\n{}".format(self.cmdArgs["origCmd50CharLabel"], err.__class__.__name__, err))
            return

        self.DEBUG and self.db.log("Cmd completed with exit code: {}".format(cmdRes.returncode))
        if self.isTextCommand:
            self.DEBUG and self.db.log("Starting Text Command Post Processing")
            if self.cmdArgs["textCmdStopOnErr"]:
                if cmdRes.returncode != 0:
                    textOp = "stdout:: " + cmdRes.stdout
                    if not self.cmdArgs["cmdCombineOutputStreams"]:
                        textOp += "\nstderr:: {}".format(cmdRes.stderr)
                    self.errStr = ("No text processed due to error code {} being returned from the shell.\n\n"
                                      "Offending command:: {}\n\n{}".format(cmdRes.returncode, 
                                                                            self.cmdArgs["origCmd50CharLabel"],
                                                                            textOp))
                    return
            elif cmdRes.returncode != 0:
                self.DEBUG and self.db.log("Non-zero shell exit code ({}) ignored as \"textCmdStopOnErr\" is false.".format(cmdRes.returncode))
            self.commandSuccess = True
            rxText = cmdRes.stdout
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


class WindowShellrunnerTextCommandCommand(sublime_plugin.WindowCommand, argChecker):

    def __init__(self, window, sbMode=False):
        super().__init__(window)
        argChecker.__init__(self)
        self.sideBarMode = sbMode
        self.DEBUG = False
        self.db = None

    def focus(self, window_to_move_to):
        active_view = window_to_move_to.active_view()
        if active_view is not None:
            window_to_move_to.focus_view(active_view)

    def run(self, **kwargs):
        self.cmdArgs = kwargs
        if self.cmdArgs.get('consoleDebug', False) or self.cmdArgs.get('tabDebugReport', False):
            self.DEBUG = True
            self.db = DebugLogger(deListCmd(self.cmdArgs.get('shellCommand', "NO COMMAND!")),
                                    prefix="ShellRunner Check Cmd Args",
                                    consoleMode = self.cmdArgs.get('consoleDebug', False),
                                    tabReport = self.cmdArgs.get('tabDebugReport', False))

        # Sanitise self.cmdArgs before running the command
        if not self.sanitiseTextCmdArgs():
            return
        # All sanitised OK, so run the command as a thread and show its progress in the status bar
        doTxtCommand = runShellCommand(self.cmdArgs, self.window.active_view())
        doTxtCommand.start()
        status_message = "ShellRunner running: {}".format(self.cmdArgs["origCmd50CharLabel"])
        ThreadProgress(doTxtCommand, status_message, "ShellRunner command completed OK")
        self.focus(self.window)
        self.DEBUG and self.db.finalReport()

    def is_visible(self):
        return True
        
    def is_enabled(self, **tkwargs):
        self.visArgs = tkwargs
        # sublime.message_dialog('running the vis thing')
        return amIEnabled(self.visArgs, windowVars=self.window.extract_variables(), sbMode=self.sideBarMode)


class SidebarShellrunnerTextCommandCommand(WindowShellrunnerTextCommandCommand):
    def __init__(self, window):
        super().__init__(window, sbMode=True)


class WindowShellrunnerSpawnCommandCommand(sublime_plugin.WindowCommand, argChecker):
    def __init__(self, window, sbMode=False):
        super().__init__(window)
        argChecker.__init__(self)
        self.sideBarMode = sbMode
        self.DEBUG = False
        self.db = None

    def run(self, **kwargs):
        self.cmdArgs = kwargs
        if self.cmdArgs.get('consoleDebug', False) or self.cmdArgs.get('tabDebugReport', False):
            self.DEBUG = True
            self.db = DebugLogger(deListCmd(self.cmdArgs.get('shellCommand', "NO COMMAND!")),
                                    prefix="ShellRunner Check Cmd Args",
                                    consoleMode = self.cmdArgs.get('consoleDebug', False),
                                    tabReport = self.cmdArgs.get('tabDebugReport', False))

        # Sanitise self.cmdArgs before running the command
        if not self.sanitiseSpawnCmdArgs():
            return
        doSpawnCommand = runShellCommand(self.cmdArgs)
        doSpawnCommand.start()
        self.DEBUG and self.db.finalReport()

    def is_enabled(self, **tkwargs):
        self.visArgs = tkwargs
        return amIEnabled(self.visArgs, windowVars=self.window.extract_variables(), sbMode=self.sideBarMode)


class SidebarShellrunnerSpawnCommandCommand(WindowShellrunnerSpawnCommandCommand):
    def __init__(self, window):
        super().__init__(window, sbMode=True)
