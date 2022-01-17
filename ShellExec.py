import sys
import os
import pathlib
import sublime
import sublime_plugin
import re
import subprocess
import shlex
import shutil
import time
from threading import Thread

plugin_settings_file = 'ShellRunner.sublime-settings'
plugin_canon_name = 'ShellRunner'

def showShRunnerError(errormsg):
    sublime.message_dialog("{} Command Report::\n\n{}".format(plugin_canon_name, errormsg))

def splitCommand(cmdStr):
    return shlex.split(cmdStr, posix=True)

def retrieveSetting(settingName, primaryDict, secondaryDict={}, default=None):
    if secondaryDict:
        return primaryDict.get(settingName, secondaryDict.get(settingName, default))
    else:
        return primaryDict.get(settingName, default)


class EditShellrunnerSidebarCommandsCommand(sublime_plugin.WindowCommand):
  def run(self, **kwargs):
    package_dir = self.window.extract_variables().get('packages')
    if os.path.isdir(package_dir):
        plugin_user_dir = pathlib.Path(package_dir) / 'User' / plugin_canon_name
        plugin_user_dir.mkdir(parents=True, exist_ok=True)
        args = {
        "base_file": "${packages}/ShellRunner/ExampleSideBar.sublime-menu",
        "user_file": "${packages}/User/ShellRunner/Side Bar.sublime-menu",
        "default": ("[{\"id\": \"shell_runner_sidebar_menu\", \"children\": [\n"
                    "\t{ \"caption\" : \"-\", \"id\": \"shell_runner_user_commands_below_here\"},\n"
                    "\t// Insert user defined ShellRunner sidebar-menu commands below here\n"
                    "\t$0\n\n"
                    "]}]")
        }
        self.window.run_command('edit_settings', args)

class EditShellrunnerContextCommandsCommand(sublime_plugin.WindowCommand):
  def run(self, **kwargs):
    package_dir = self.window.extract_variables().get('packages')
    if os.path.isdir(package_dir):
        plugin_user_dir = pathlib.Path(package_dir) / 'User' / plugin_canon_name
        plugin_user_dir.mkdir(parents=True, exist_ok=True)
        args = {
        "base_file": "${packages}/ShellRunner/ExampleContext.sublime-menu",
        "user_file": "${packages}/User/ShellRunner/Context.sublime-menu",
        "default": ("[{\"id\": \"shell_runner_context_menu\", \"children\": [\n"
                    "\t{ \"caption\" : \"-\", \"id\": \"shell_runner_context_commands_below_here\"},\n"
                    "\t// Insert user defined ShellRunner context-menu commands below here\n"
                    "\t$0\n\n"
                    "]}]")
        }
        self.window.run_command('edit_settings', args)

class VisibilitySetParentMenuCommand(sublime_plugin.WindowCommand):
    """
    A wrapper to be used for parent menus (command-less) to make them visible only in certain scopes/contexts.
    The class overrides the 'is_visible' method so it returns True only when the current scope matches the target scope
    """
    def run(self):
        pass

    def is_visible(self):
        self.shrunner_settings = loadPluginAndProjSettings(self.window)
        viewMe = self.shrunner_settings.get("contextMenu", False)
        if not isinstance(viewMe, bool):
            viewMe = False
        return viewMe

class EditShellrunnerKeyBindingsCommand(sublime_plugin.WindowCommand):
  def run(self, **kwargs):
    package_dir = self.window.extract_variables().get('packages')
    if os.path.isdir(package_dir):
        plugin_user_dir = pathlib.Path(package_dir) / 'User' / plugin_canon_name
        plugin_user_dir.mkdir(parents=True, exist_ok=True)
        args = {
        "base_file": "${packages}/ShellRunner/Example.sublime-keymap",
        "user_file": "${packages}/User/ShellRunner/Default (${platform}).sublime-keymap",
        "default": ("// This file is for user defined key bindings associated with the ShellRunner plugin\n"
                    "[\n\t// Insert key bindings below here:"
                    "\n\t//$0{ \"keys\":     [\"ctrl+shift+c\"],"
                    "\n\t//\t\"command\":    \"shell_run_text_command\","   
                    "\n\t//\t\"args\"    :   {   \"shellCommand\": \"/usr/bin/bash -c 'echo ShellRunner insert text demo'\","   
                    "\n\t//\t\t\t\t\"outputTo\": \"cursorInsert\","   
                    "\n\t//\t\t\t}\n\t//},\n]")
        }
        self.window.run_command('edit_settings', args)

class OpenTerminalHereCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        super().__init__(window)
        self.shrunner_settings = loadPluginAndProjSettings(self.window)
        self.termCmd = self.shrunner_settings.get("open_terminal_cmd", None)
        if not self.termCmd is None:
            if not self.termCmd:
                # "open_terminal_cmd" is set to an empty string so we can search for a likely term emulator
                for termprog in ["xterm", "gnome-terminal", "konsole"]:
                    pathStr = shutil.which(termprog)
                    if pathStr:
                        self.termCmd = pathStr
                        break
        # If the "open_terminal_cmd" is defined then we can enable the 'Open Terminal' menu command
        # `- we define a boolean var during 'init' to implement this:
        self.termCmdIsDefined = bool(self.termCmd)
    def is_visible(self, **kwargs):
        return self.termCmdIsDefined
    def is_enabled(self, **kwargs):
        return self.termCmdIsDefined
    def run(self, **kwargs):
        self.cmdArgs = kwargs
        if self.termCmdIsDefined:
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


def addMultiItems(settingsDict, argsDict={}):
    """
    Build space separated string lists of 'files', 'dirs', 'paths' as available in args passed
    Sublime fills the optional sidebar menu args appropriately when they are given in the menu command:
    e.g. and arg "dirs": [] will result in a list of dirs currently selected in the sidebar
    If the list is not available, or empty, define a zero length string
    """
    addDict = {}
    for addList in ['files', 'dirs', 'paths']:
        gotList = argsDict.get(addList)
        lastSelectedKey = "last" + addList[:-1].capitalize()
        if gotList:
            escapedList = [ shlex.quote(a) for a in gotList ]
            addDict[addList] = " ".join(escapedList)
            addDict[lastSelectedKey] = escapedList[0]
        else:
            addDict[addList] = ""
            addDict[lastSelectedKey] = ""
    settingsDict.update(addDict)
    return settingsDict

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

    def __init__(self, commandStr, prefix=""):
        self.cs = truncateStr(commandStr)
        self.prefix = prefix

    def log(self, logmsg=""):
        print("{}:[[CMD:{}]]:{}".format(self.prefix, self.cs, logmsg))


def amIEnabled(visArgs, windowVars={}, sbMode=True):
    # sublime.message_dialog("vis args: {}".format(visArgs))
    visMe = True
    DEBUG = visArgs.get('consoleDebug', False)
    db = DebugLogger(visArgs.get('shellCommand', "NO COMMAND!"), prefix="ShellRunner Check Cmd Enablement")
    targetExtns = visArgs.get('targetExtensions', False)
    if sbMode:
        DEBUG and db.log('Sidebar Mode Check')
        dirOnly = visArgs.get('dirOnly', False)
        extraForDirs = "(or dir) "
    else:
        DEBUG and db.log('Window Mode Check')
        dirOnly = False
        extraForDirs = ""
    if targetExtns:
        DEBUG and db.log("Valid file extns: {}".format(targetExtns))
        visMe = False  # until proven otherwise
        # NB: the initial dot/period must be included for each of targetExtensions e.g. ".jpg" not "jpg"
        #    ` multipart extensions are not catered for e.g. ".tar.gz" will never match, but ".gz" will
        if sbMode:
            lastSelectedSidebarPath = ""
            sbFiles = visArgs.get('files', False)
            if sbFiles:
                lastSelectedSidebarPath = sbFiles[0]
                DEBUG and db.log('Last selected sidebar file to match = {}'.format(truncateStr(lastSelectedSidebarPath, length=25, chopFront=True)))
            else:
                sbPaths = visArgs.get('paths', False)
                if sbPaths:
                    lastSelectedSidebarPath = sbPaths[0]
                    DEBUG and db.log('Last selected sidebar path to match = {}'.format(truncateStr(lastSelectedSidebarPath, length=25, chopFront=True)))
                    if os.path.isfile(sbPaths[0]):
                        DEBUG and db.log('Last selected sidebar path is a file')
                        lastSelectedSidebarPath = sbPaths[0]
                    else:
                        DEBUG and db.log('Last selected sidebar path is NOT a file')
                else:
                    DEBUG and db.log("No sidebar 'files':[] or 'paths': [] to check against allowed extensions")
            fileToCheckExtn = lastSelectedSidebarPath
        else: # not sidebar mode i.e. key bind or context menu
            fileToCheckExtn = windowVars.get('file')
            DEBUG and db.log('Window file to match = {}'.format(truncateStr(fileToCheckExtn, length=25, chopFront=True)))
        if fileToCheckExtn:
            haveExtn = os.path.splitext(fileToCheckExtn)[1]
            if haveExtn in targetExtns:
                DEBUG and db.log('Target file extension ({}) matches.'.format(haveExtn))
                visMe = True
            else:
                DEBUG and db.log('Target file extension ({}) does not match.'.format(haveExtn))
        else:
            DEBUG and db.log('WARNING: No target file found on which to perform match check.')
            visMe = True
    elif dirOnly:
        DEBUG and db.log('Directory Only Command')
        visMe = False
        if visArgs.get('dirs', False):
            DEBUG and db.log('Directory detected in sidebar selections')
            # If any directory is selected
            visMe = True
        else:
            DEBUG and db.log('No sidebar directory selection detected (is dirs arg provided)')
    else:
        DEBUG and db.log("No file extension {}restrictions found in args.".format(extraForDirs))
    DEBUG and db.log('Command Visible/Enabled = {}'.format(visMe))
    return visMe

def loadPluginAndProjSettings(curWindow):
    theSettings = sublime.load_settings(plugin_settings_file)
    if curWindow.project_data():
        proj_plugin_settings = curWindow.project_data().get(plugin_canon_name, None)
        if proj_plugin_settings:
            # any ShellRunner settings in the .sublime-project file will override same name Default/User settings
            theSettings.update(proj_plugin_settings)
    return theSettings

class argChecker():

    def sanitiseSpawnCmdArgs(self):
        ## Step A1: Check and build the run command
        runcmd = retrieveSetting("shellCommand", self.cmdArgs)
        if not runcmd:
            showShRunnerError("No command defined.")
            return False
        else:
            # expand any 'standard' sublime placeholder variables in our command
            # `- e.g. ${packages} ${platform} ${file} ${file_path} ${file_name} ${file_base_name} ${project_extension}
            #  - ${file_extension} ${folder} ${project} ${project_path} ${project_name} ${project_base_name}
            # furthermore allow for several custom placeholder vars to be expanded:
            # `- ${paths}, ${lastPath}, ${dirs}, ${lastDir}, ${files}, ${lastFile} (all as escaped 'shell friendly' strings) 
            self.DEBUG and self.db.log("Pre-substitution  \"shellCommand\": {}".format(self.cmdArgs["shellCommand"]))
            self.cmdArgs["shellCommand"] = sublime.expand_variables(runcmd, addMultiItems(self.window.extract_variables(), self.cmdArgs))
            self.DEBUG and self.db.log("Post-substitution \"shellCommand\": {}".format(self.cmdArgs["shellCommand"]))
        
        ## Step A2: Check 'initChangeDir' setting to see if we should change dir, to file loc, before running command
        doChgDir = retrieveSetting("initChangeDir", self.cmdArgs, self.shrunner_settings, default=True)
        if not isinstance(doChgDir, bool):
            showShRunnerError("Settings error: 'initChangeDir' must be defined True or False, not [{}]".format(doChgDir))
            return False
        self.DEBUG and self.db.log("\"initChangeDir\" (orig bool) = {}".format(doChgDir))
        if doChgDir:
            self.cmdArgs["initChangeDir"] = self.window.extract_variables().get('file_path', '.')
        else:
            self.cmdArgs["initChangeDir"] = "."
        self.DEBUG and self.db.log("\"initChangeDir\" (as dir)  = {}".format(self.cmdArgs["initChangeDir"]))

        return True

    def sanitiseTextCmdArgs(self):
        if not self.sanitiseSpawnCmdArgs():
            return False

        ## Step B1: Check 'outputTo' is defined correctly:
        output_dest_list = retrieveSetting("outputTo", self.cmdArgs, self.shrunner_settings, default=[])
        if isinstance(output_dest_list, str):
            output_dest_list = [ output_dest_list ]
        for output_dest in output_dest_list:
            if not output_dest in ['newTab', 'sublConsole', 'cursorInsert', 'msgBox', 'clip', None]:
                showShRunnerError("Command arg error: 'outputTo' contains incorrect entry. [{}] is invalid.".format(output_dest))
                return False
        self.cmdArgs["outputTo"] = output_dest_list
        self.DEBUG and self.db.log("\"outputTo\" (as list)  = {}".format(self.cmdArgs["outputTo"]))

        ## Step B2: Prepare 'newTabName' from settings (if this is None, that's OK, we just have a nameless new tab)
        self.cmdArgs["newTabName"] = retrieveSetting("outputTabName", self.cmdArgs, self.shrunner_settings)
        self.DEBUG and self.db.log("\"newTabName\"  = {}".format(self.cmdArgs["newTabName"]))

        ## Step B3: Check 'cmdCombineOutputStreams' setting to see if we should merge stdout and stderr from command
        self.cmdArgs["cmdCombineOutputStreams"] = retrieveSetting("cmdCombineOutputStreams", self.cmdArgs, self.shrunner_settings, default=False)
        if not isinstance(self.cmdArgs["cmdCombineOutputStreams"], bool):
            showShRunnerError("Command arg error: 'cmdCombineOutputStreams' must be defined True or False,"
                                " not [{}]".format(self.cmdArgs["cmdCombineOutputStreams"]))
            return False
        self.DEBUG and self.db.log("\"cmdCombineOutputStreams\"  = {}".format(self.cmdArgs["cmdCombineOutputStreams"]))

        ## Step B4: Check 'textCmdTimeout' setting to see if we should set a timeout for our command    
        self.cmdArgs["textCmdTimeout"] = retrieveSetting("textCmdTimeout", self.cmdArgs, self.shrunner_settings, default=10)
        if not isinstance(self.cmdArgs["textCmdTimeout"], int):
            showShRunnerError("Command arg error: 'textCmdTimeout' must be an integer,"
                                " not [{}]".format(self.cmdArgs["textCmdTimeout"]))
            return False
        self.DEBUG and self.db.log("\"textCmdTimeout\"  = {}".format(self.cmdArgs["textCmdTimeout"]))

        ## Step B5: Check 'textCmdStopOnErr' setting to see if we should stop on shell errors    
        self.cmdArgs["textCmdStopOnErr"] = retrieveSetting("textCmdStopOnErr", self.cmdArgs, self.shrunner_settings, default=True)
        if not isinstance(self.cmdArgs["textCmdStopOnErr"], bool):
            showShRunnerError("Command arg error: 'textCmdStopOnErr' must be defined True or False,"
                                " not [{}]".format(self.cmdArgs["textCmdStopOnErr"]))
            return False
        self.DEBUG and self.db.log("\"textCmdStopOnErr\"  = {}".format(self.cmdArgs["textCmdStopOnErr"]))

        ## All checks OK. self.cmdArgs prepared for running phase
        return True

class ViewInsertBigTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, pos, text):
        self.view.insert(edit, pos, text)

class runTxtCommand(Thread):

    def __init__(self, passedArgs, targetView={}):
        self.cmdArgs = passedArgs
        self.DEBUG = self.cmdArgs.get('consoleDebug', False)
        self.db = DebugLogger(self.cmdArgs.get('shellCommand', "NO COMMAND!"), prefix="ShellRunner Run")
        self.targetView = targetView
        self.isTextCommand = bool(self.targetView)
        self.textOut = None
        Thread.__init__(self)

    def run(self):
        self.DEBUG and self.db.log("Splitting full cmd str (( {} ))".format(self.cmdArgs["shellCommand"]))
        try:
            cmdAsArray = splitCommand(self.cmdArgs["shellCommand"])
        except Exception as err:
            showShRunnerError("Command was not run as an unexpected exception occurred in splitting it for the shell. "
                              "Please check your command is formatted correctly.\n\n"
                              "Offending command:: {}\n\n"
                              "Details:: {}\n\n{}".format(self.cmdArgs["shellCommand"], err.__class__.__name__, err))
            return
        self.DEBUG and self.db.log("Cmd as Array: {}".format(cmdAsArray))

        try:
            processArgs = {}
            processArgs["cwd"] = self.cmdArgs["initChangeDir"]
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
            cmdRes = subprocess.run(cmdAsArray, **processArgs)
        except subprocess.TimeoutExpired:
            showShRunnerError("No text processed due to shell command enforced timeout ({} seconds)\n\n"
                              "Offending command:: {}".format(self.cmdArgs["textCmdTimeout"],
                                                              self.cmdArgs["shellCommand"]))
            return
        except Exception as err:
            showShRunnerError("Shell command failed as an unexpected exception occurred.\n\n"
                              "Offending command:: {}\n\n"
                              "Details:: {}\n\n{}".format(self.cmdArgs["shellCommand"], err.__class__.__name__, err))
            return

        self.DEBUG and self.db.log("Cmd completed with exit code: {}".format(cmdRes.returncode))
        if self.isTextCommand:
            self.DEBUG and self.db.log("Starting Text Command Post Processing")
            if self.cmdArgs["textCmdStopOnErr"]:
                if cmdRes.returncode != 0:
                    textOp = "stdout:: " + cmdRes.stdout
                    if not self.cmdArgs["cmdCombineOutputStreams"]:
                        textOp += "\nstderr:: {}".format(cmdRes.stderr)
                    showShRunnerError("No text processed due to error code {} being returned from the shell.\n\n"
                                      "Offending command:: {}\n\n{}".format(cmdRes.returncode, 
                                                                            self.cmdArgs["shellCommand"],
                                                                            textOp))
                    return
            elif cmdRes.returncode != 0:
                self.DEBUG and self.db.log("Non-zero shell exit code ({}) ignored as \"textCmdStopOnErr\" is false.".format(cmdRes.returncode))
            rxText = cmdRes.stdout
            if rxText:
                ## Step 4: Send command output to set destination
                self.DEBUG and self.db.log("Outputting text to {}".format(self.cmdArgs["outputTo"]))
                for destination in self.cmdArgs["outputTo"]:
                    if destination == "newTab":
                        self.output_file = sublime.active_window().new_file()
                        if self.cmdArgs["newTabName"]:
                            self.output_file.set_name(self.cmdArgs["newTabName"])
                        self.output_file.run_command('view_insert_big_text', {'pos': self.output_file.size(), 'text': rxText})
                        # self.output_file.run_command("insert", {"characters": rxText})
                    elif destination == "sublConsole":
                        sublime.active_window().run_command('show_panel', {"panel": "console", "toggle": False})
                        print (rxText)
                    elif destination == "cursorInsert":
                        self.targetView.run_command('insert', {"characters": rxText})
                    elif destination == "msgBox":
                        sublime.message_dialog(rxText)
                    elif destination == "clip":
                        subprocess.Popen(('xsel', '-i', '-b'), stdin=subprocess.PIPE).communicate(bytearray(rxText, 'utf-8'))
        else:
            self.DEBUG and self.db.log("Non Text Command spawning complete")

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
            if self.thread.textOut is None:
                cleanup()
                return
            active_view.set_status('_shellRunner', self.success_message)
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

    def run(self, **kwargs):
        # Initialise Command Args and Plugin Settings
        self.cmdArgs = kwargs
        self.shrunner_settings = loadPluginAndProjSettings(self.window)
        # Sanitise self.cmdArgs before running the command
        self.DEBUG = self.cmdArgs.get('consoleDebug', False)
        self.db = DebugLogger(self.cmdArgs.get('shellCommand', "NO COMMAND!"), prefix="ShellRunner Check Cmd Args")

        if not self.sanitiseTextCmdArgs():
            return
        # All sanitised OK, so run the command as a thread and show its progress in the status bar
        doTxtCommand = runTxtCommand(self.cmdArgs, self.window.active_view())
        doTxtCommand.start()
        status_message = "ShellRunner running: {}".format(self.cmdArgs["shellCommand"])
        ThreadProgress(doTxtCommand, status_message, "ShellRunner command completed OK")
        
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

    def run(self, **kwargs):
        # Initialise Command Args and Plugin Settings
        self.cmdArgs = kwargs
        self.shrunner_settings = loadPluginAndProjSettings(self.window)
        # Sanitise self.cmdArgs before running the command
        self.DEBUG = self.cmdArgs.get('consoleDebug', False)
        self.db = DebugLogger(self.cmdArgs.get('shellCommand', "NO COMMAND!"), prefix="ShellRunner Check Cmd Args")

        if not self.sanitiseSpawnCmdArgs():
            return
        doSpawnCommand = runTxtCommand(self.cmdArgs)
        doSpawnCommand.start()

    def is_enabled(self, **tkwargs):
        self.visArgs = tkwargs
        return amIEnabled(self.visArgs, windowVars=self.window.extract_variables(), sbMode=self.sideBarMode)

class SidebarShellrunnerSpawnCommandCommand(WindowShellrunnerSpawnCommandCommand):

    def __init__(self, window):
        super().__init__(window, sbMode=True)
