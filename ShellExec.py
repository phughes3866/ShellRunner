import sys
import os
import pathlib
# import time
import sublime
import sublime_plugin
import re
import subprocess
import shlex
import time
# from subprocess import Popen, PIPE, STDOUT
from threading import Thread

plugin_settings_file = 'ShellRunner.sublime-settings'
plugin_canon_name = 'ShellRunner'

def showShRunnerError(errormsg):
    sublime.error_message("{} plugin error::\n\n{}".format(plugin_canon_name, errormsg))

def splitCommand(cmdStr):
    return shlex.split(cmdStr, posix=True)

def retrieveSetting(settingName, primaryDict, secondaryDict={}, default=None):
    if secondaryDict:
        return primaryDict.get(settingName, secondaryDict.get(settingName, default))
    else:
        return primaryDict.get(settingName, default)

# def window_set_status(key, textMessage=""):
#     for window in sublime.windows():
#         for view in window.views():
#             view.set_status(key, textMessage)

# class ProgressNotifier():
#     """
#     Animates an indicator, [=   ]

#     :param message:
#         The message to display next to the activity indicator

#     :param success_message:
#         The message to display once the thread is complete
#     """

#     def __init__(self, message, success_message=''):
#         self.message = message
#         self.success_message = success_message
#         self.stopped = False
#         self.addend = 1
#         self.size = 8
#         sublime.set_timeout(lambda: self.run(0), 100)

#     def run(self, i):
#         if self.stopped:
#             return

#         before = i % self.size
#         after = (self.size - 1) - before

#         # sublime.status_message('%s [%s=%s]' % (self.message, ' ' * before, ' ' * after))
#         sublime.status_message('deary doo')
#         if not after:
#             self.addend = -1
#         if not before:
#             self.addend = 1
#         i += self.addend

#         sublime.set_timeout(lambda: self.run(i), 100)

#     def stop(self):
#         sublime.status_message(self.success_message)
#         self.stopped = True

class DoViewInsertCommand(sublime_plugin.TextCommand):
  def run(self, edit, pos, text):
    # sublime.message_dialog('trying to insert at poz{} the text:{}'.format(pos, text))
    self.view.insert(edit, pos, text)

class EditShellrunnerCommandsCommand(sublime_plugin.WindowCommand):
  def run(self, **kwargs):
    package_dir = sublime.active_window().extract_variables().get('packages')
    if os.path.isdir(package_dir):
        plugin_user_dir = pathlib.Path(package_dir) / 'User' / plugin_canon_name
        plugin_user_dir.mkdir(parents=True, exist_ok=True)
        # sublime.message_dialog('user plugin dir = {}'.format(str(plugin_user_dir)))
        # "default": "[\n\t{\n\t\"id\": \"shell-runner-shell-commands\",\n\t\"children\": [\n\t// Insert User Defined ShellRunner Commands Below\n\t$0\n\n\t]\n\t}\n]\n"
        args = {
        "base_file": "${packages}/ShellRunner/ExampleSideBar.sublime-menu",
        "user_file": "${packages}/User/ShellRunner/Side Bar.sublime-menu",
        "default": ("[{\"id\": \"shell_runner_sidebar_menu\", \"children\": [\n"
                    "\t{ \"caption\" : \"-\", \"id\": \"shell_runner_user_commands_below_here\"},\n"
                    "\t// Insert User Defined ShellRunner Commands Here\n"
                    "\t$0\n\n"
                    "]}]")
        }
        self.window.run_command('edit_settings', args)

class OpenTerminalCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        super().__init__(window)
        self.shrunner_settings = sublime.load_settings(plugin_settings_file)
        proj_plugin_settings = sublime.active_window().active_view().settings().get(plugin_canon_name, {})
        # any ShellRunner settings in the .sublime-project file will override same name Default/User settings
        self.shrunner_settings.update(proj_plugin_settings)
        # If the "open_terminal_cmd" is defined then we can enable the 'Open Terminal' menu command
        # `- we define a boolean var during 'init' to implement this:
        self.termCmdIsDefined = bool(self.shrunner_settings.get("open_terminal_cmd", None))
    def is_visible(self, **kwargs):
        return self.termCmdIsDefined
    def is_enabled(self, **kwargs):
        return self.termCmdIsDefined
    def run(self, **kwargs):
        if self.termCmdIsDefined:
            change_dir = sublime.active_window().extract_variables().get('file_path', '.')
            cmd_array = splitCommand(self.shrunner_settings.get("open_terminal_cmd"))
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

def amIEnabled(visArgs):
    # sublime.message_dialog("vis args: {}".format(visArgs))
    visMe = True
    targetExtns = visArgs.get('targetExtensions', False)
    dirOnly = visArgs.get('dirOnly', False)
    if targetExtns:
        print("targetExtns: {}".format(targetExtns))
        visMe = False  # until proven otherwise
        sbPaths = visArgs.get('paths', False)
        sbFiles = visArgs.get('files', False)
        lastSelectedSidebarPath = ""
        if sbFiles:
            lastSelectedSidebarPath = sbFiles[0]
            print("found in files: {}".format(lastSelectedSidebarPath))
        elif sbPaths:
            lastSelectedSidebarPath = sbPaths[0]
            print("found in paths: {}".format(lastSelectedSidebarPath))
            if not os.path.isfile(lastSelectedSidebarPath):
                print("not a file: {}".format(lastSelectedSidebarPath))
                lastSelectedSidebarPath = ""
        else:
            print("ShellRunner Warning: Command[{}] has no 'files':[] or 'paths': [] to check against allowed extensions: {}".format(visArgs.get('shellCommand', "NO COMMAND"), targetExtns))
        if lastSelectedSidebarPath:
            haveExtn = os.path.splitext(lastSelectedSidebarPath)[1]
            if haveExtn in targetExtns:
                visMe = True
    elif dirOnly:
        visMe = False
        if visArgs.get('dirs', False):
            # If any directory is selected
            visMe = True
            print('enabled as we have a dir')
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
    # def __init__(self):
        # self.haveit = "here we go"

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
            self.cmdArgs["shellCommand"] = sublime.expand_variables(runcmd, addMultiItems(self.window.extract_variables(), self.cmdArgs))
        
        ## Step A2: Check 'initChangeDir' setting to see if we should change dir, to file loc, before running command
        doChgDir = retrieveSetting("initChangeDir", self.cmdArgs, self.shrunner_settings)
        if not isinstance(doChgDir, bool):
            showShRunnerError("Settings error: 'initChangeDir' must be defined True or False, not [{}]".format(doChgDir))
            return False
        if doChgDir:
            self.cmdArgs["initChangeDir"] = self.window.extract_variables().get('file_path', '.')
        else:
            self.cmdArgs["initChangeDir"] = "."
        return True

    def sanitiseTextCmdArgs(self):
        if not self.sanitiseSpawnCmdArgs():
            return False

        ## Step B1: Prepare 'newTabName' from settings (if this is None, that's OK, we just have a nameless new tab)
        self.cmdArgs["newTabName"] = retrieveSetting("outputTabName", self.cmdArgs, self.shrunner_settings)

        ## Step B2: Check 'outputTo' is defined correctly:
        output_dest = retrieveSetting("outputTo", self.cmdArgs, self.shrunner_settings, default=None)
        if not output_dest in ['newTab', 'sublConsole', 'cursorInsert', 'clip', None]:
            showShRunnerError("'outputTo' is incorrectly defined in settings. [{}] is invalid.".format(output_dest))
            return False
        else:
            self.cmdArgs["outputTo"] = output_dest

        ## Step B3: Check 'cmdCombineOutputStreams' setting to see if we should merge stdout and stderr from command
        combineStreams = retrieveSetting("cmdCombineOutputStreams", self.cmdArgs, self.shrunner_settings, default=False)
        if not isinstance(combineStreams, bool):
            showShRunnerError("Settings error: 'cmdCombineOutputStreams' must be defined True or False, not [{}]".format(combineStreams))
            return False
        else:
            self.cmdArgs["cmdCombineOutputStreams"] = combineStreams

        ## Step B4: Check 'textCmdTimeout' setting to see if we should set a timeout for our command    
        timeoutSecs = retrieveSetting("textCmdTimeout", self.cmdArgs, self.shrunner_settings)
        if not timeoutSecs or not isinstance(timeoutSecs, int):
            timeoutSecs = 10  # default timeout
        self.cmdArgs["textCmdTimeout"] = timeoutSecs

        ## Step B5: Check 'textCmdStopOnErr' setting to see if we should stop on shell errors    
        self.cmdArgs["textCmdStopOnErr"] = retrieveSetting("textCmdStopOnErr", self.cmdArgs, self.shrunner_settings, default=False)
        if not isinstance(self.cmdArgs["textCmdStopOnErr"], bool):
            showShRunnerError("Settings error: 'textCmdStopOnErr' must be defined True or False, not [{}]".format(self.cmdArgs["textCmdStopOnErr"]))
            return False
            # stopOnErr = False  # default timeout
        # self.cmdArgs["textCmdStopOnErr"] = stopOnErr

        ## All checks OK. self.cmdArgs prepared for running phase
        return True

class runTxtCommand(Thread):

    def __init__(self, passedArgs, targetView):
        self.cmdArgs = passedArgs
        self.targetView = targetView
        self.textOut = None
        Thread.__init__(self)

    def run(self):
        if self.cmdArgs["cmdCombineOutputStreams"]:
            errDest = subprocess.STDOUT
        else:
            errDest = subprocess.PIPE
        raisedException = True
        try:
            cmdRes = subprocess.run(splitCommand(self.cmdArgs["shellCommand"]),
                                    cwd=self.cmdArgs["initChangeDir"],
                                    stdout=subprocess.PIPE,
                                    stderr=errDest,
                                    encoding='UTF-8',
                                    timeout=self.cmdArgs["textCmdTimeout"])
            # raise ValueError('A very specific bad thing happened.')
            raisedException = False
        except subprocess.TimeoutExpired:
            showShRunnerError('Process timed out after {} seconds (user set timeout)\n\nCommand: [{}]'.format(self.cmdArgs["textCmdTimeout"], self.cmdArgs["shellCommand"]))
            return
        except Exception as err:
            showShRunnerError("Unexpected Exception ({}):\n{}\n\nOffending Command:\n{}".format(err.__class__.__name__, err, self.cmdArgs["shellCommand"]))

        if raisedException:
            return
        if self.cmdArgs["textCmdStopOnErr"]:
            if cmdRes.returncode != 0:
                textOp = "stdout:: " + cmdRes.stdout
                if not self.cmdArgs["cmdCombineOutputStreams"]:
                    textOp += "\nstderr:: {}".format(cmdRes.stderr)
                showShRunnerError("Error code {} running command:\n{}\n\n{}".format(cmdRes.returncode, self.cmdArgs["shellCommand"], textOp))
                return
        self.textOut = cmdRes.stdout
        rxText = cmdRes.stdout
        if rxText:
            ## Step 4: Send command output to set destination
            if self.cmdArgs["outputTo"] == "newTab":
                self.output_file = sublime.active_window().new_file()
                if self.cmdArgs["newTabName"]:
                    self.output_file.set_name(self.cmdArgs["newTabName"])
                self.output_file.run_command("do_view_insert", {'pos': self.output_file.size(), "text": rxText})
            elif self.cmdArgs["outputTo"] == "sublConsole":
                sublime.active_window().run_command('show_panel', {"panel": "console", "toggle": False})
                print (rxText)
            elif self.cmdArgs["outputTo"] == "cursorInsert":
                self.targetView.run_command('insert', {"characters": rxText})
            elif self.cmdArgs["outputTo"] == "clip":
                subprocess.Popen(('xsel', '-i', '-b'), stdin=subprocess.PIPE).communicate(bytearray(rxText, 'utf-8'))


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

class ShellRunTextCommandCommand(sublime_plugin.WindowCommand, argChecker):

    def __init__(self, window):
        super().__init__(window)
        argChecker.__init__(self)

    def run(self, **kwargs):
        # Initialise Command Args and Plugin Settings
        self.cmdArgs = kwargs
        self.shrunner_settings = loadPluginAndProjSettings(self.window)
        # Sanitise self.cmdArgs before running the command
        if not self.sanitiseTextCmdArgs():
            return
        # All sanitised OK, so run the command as a thread and show its progress in the status bar
        doTxtCommand = runTxtCommand(self.cmdArgs, self.window.active_view())
        doTxtCommand.start()
        status_message = "ShellRunner running: {}".format(self.cmdArgs["shellCommand"])
        ThreadProgress(doTxtCommand, status_message, "ShellRunner command completed OK")
        
    def is_enabled(self, **tkwargs):
        self.visArgs = tkwargs
        return amIEnabled(self.visArgs)


class ShellSpawnCommandCommand(sublime_plugin.WindowCommand, argChecker):

    def __init__(self, window):
        super().__init__(window)
        argChecker.__init__(self)

    def run(self, **kwargs):
        # Initialise Command Args and Plugin Settings
        self.cmdArgs = kwargs
        self.shrunner_settings = loadPluginAndProjSettings(self.window)
        # Sanitise self.cmdArgs before running the command
        if not self.sanitiseSpawnCmdArgs():
            return
        subprocess.Popen(splitCommand(self.cmdArgs["shellCommand"]),
                        cwd=self.cmdArgs["initChangeDir"])
        print ("ShellRunner spawned: {}".format(self.cmdArgs["shellCommand"]))

    def is_enabled(self, **tkwargs):
        self.visArgs = tkwargs
        return amIEnabled(self.visArgs)

