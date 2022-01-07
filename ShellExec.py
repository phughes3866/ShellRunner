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
# from threading import Thread

plugin_settings_file = 'ShellRunner.sublime-settings'
plugin_canon_name = 'ShellRunner'

def showShRunnerError(errormsg):
    sublime.error_message("{} plugin error::\n\n{}".format(plugin_canon_name, errormsg))

def splitCommand(cmdStr):
    return shlex.split(cmdStr, posix=True)

def retrieveSetting(settingName, primaryDict, secondaryDict={}):
    if secondaryDict:
        return primaryDict.get(settingName, secondaryDict.get(settingName))
    else:
        return primaryDict.get(settingName)

def window_set_status(key, textMessage=""):
    for window in sublime.windows():
        for view in window.views():
            view.set_status(key, textMessage)

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
        if gotList:
            addDict[addList] = " ".join(gotList)
        else:
            addDict[addList] = ""
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
            print("ShellRunner Warning: Command[{}] has no 'files':[] or 'paths': [] to check against allowed extensions: {}".format(visArgs.get('command', "NO COMMAND"), targetExtns))
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


class ShellSpawnCommandCommand(sublime_plugin.WindowCommand):
    def run(self, **kwargs):
        self.cmdArgs = kwargs
        # sublime.message_dialog('args = {}'.format(self.cmdArgs))
        sublSettings = addMultiItems(self.window.extract_variables(), self.cmdArgs)
        self.shrunner_settings = sublime.load_settings(plugin_settings_file)
        proj_plugin_settings = sublime.active_window().active_view().settings().get(plugin_canon_name, {})
        # any ShellRunner settings in the .sublime-project file will override same name Default/User settings
        self.shrunner_settings.update(proj_plugin_settings)
        self.runcmd = retrieveSetting("command", self.cmdArgs)
        if not self.runcmd:
            showShRunnerError("No command defined.")
            return
        self.runcmd = sublime.expand_variables(self.runcmd, sublSettings)
        cmd_array = splitCommand(self.runcmd)
        doChgDir = retrieveSetting("initChangeDir", self.cmdArgs, self.shrunner_settings)
        if not isinstance(doChgDir, bool):
            showShRunnerError("Settings error: 'initChangeDir' must be defined True or False, not [{}]".format(doChgDir))
            return
        if doChgDir:
            change_dir = sublime.active_window().extract_variables().get('file_path', '.')
        else:
            change_dir = "."
        subprocess.Popen(cmd_array, cwd=change_dir)
        print ("ShellRunner spawned: {}".format(self.runcmd))

    def is_enabled(self, **tkwargs):
        self.visArgs = tkwargs
        return amIEnabled(self.visArgs)


class ShellRunTextCommandCommand(sublime_plugin.WindowCommand):

    def run(self, **kwargs):
        ## Step 1: Initialise Settings
        self.cmdArgs = kwargs
        sublSettings = addMultiItems(self.window.extract_variables(), self.cmdArgs)
        # sublime.message_dialog('all settings = {}'.format(sublSettings))
        # subl_top_folder_path = sublSettings.get("folder")
        self.shrunner_settings = sublime.load_settings(plugin_settings_file)
        proj_plugin_settings = sublime.active_window().active_view().settings().get(plugin_canon_name, {})
        # any ShellRunner settings in the .sublime-project file will override same name Default/User settings
        self.shrunner_settings.update(proj_plugin_settings)

        ## Step 2: Build the run command 'self.runcmd' and perform pre-run checks
        self.runcmd = retrieveSetting("command", self.cmdArgs)
        if not self.runcmd:
            showShRunnerError("No command defined.")
            return
        self.output_dest = retrieveSetting("outputTo", self.cmdArgs, self.shrunner_settings)
        if not self.output_dest in ['newTab', 'sublConsole', 'cursorInsert', None]:
            showShRunnerError("'outputTo' is incorrectly defined in settings. [{}] is invalid.".format(self.output_dest))
            return
        # expand any sublime placeholder variables in our command
        # `- e.g. ${packages} ${platform} ${file} ${file_path} ${file_name} ${file_base_name} ${project_extension}
        #  - ${file_extension} ${folder} ${project} ${project_path} ${project_name} ${project_base_name}
        # sublime.message_dialog("settings: {}".format(sublSettings))
        self.runcmd = sublime.expand_variables(self.runcmd, sublSettings)
        # check 'initChangeDir' setting to see if we should change dir, to file loc, before running command
        doChgDir = retrieveSetting("initChangeDir", self.cmdArgs, self.shrunner_settings)
        if not isinstance(doChgDir, bool):
            showShRunnerError("Settings error: 'initChangeDir' must be defined True or False, not [{}]".format(doChgDir))
            return
        if doChgDir:
            change_dir = sublime.active_window().extract_variables().get('file_path', '.')
        else:
            change_dir = "."
        # check 'cmdCombineOutputStreams' setting to see if we should merge stdout and stderr from command
        combineStreams = retrieveSetting("cmdCombineOutputStreams", self.cmdArgs, self.shrunner_settings)
        if not isinstance(combineStreams, bool):
            showShRunnerError("Settings error: 'cmdCombineOutputStreams' must be defined True or False, not [{}]".format(combineStreams))
            return
        if combineStreams:
            errDest = subprocess.STDOUT
        else:
            errDest = subprocess.PIPE
        # check 'textCmdTimeout' setting to see if we should set a timeout for our command    
        timeoutSecs = retrieveSetting("textCmdTimeout", self.cmdArgs, self.shrunner_settings)

        ## Step 3: Run command, capture output. Implement error check and timeout as per settings.
        status_key = "ShellRunner-" + str(time.time())
        status_message = "ShellRunner Waiting On: {}".format(self.runcmd)
        if timeoutSecs:
            status_message += " (timeout:{}secs)".format(timeoutSecs)
        else:
            status_message += " (timeout not set)"
        # self.window.active_view().set_status(status_key, status_message)
        self.window.active_view().set_status("terry", "turnip" + str(time.time()))
        # sublime.active_window().active_view().set_status(status_key, status_message)
        # sublime.active_window().set_status_bar_visible()
        raisedException = True
        try:
            cmdRes = subprocess.run(splitCommand(self.runcmd),
                                    cwd=change_dir,
                                    stdout=subprocess.PIPE,
                                    stderr=errDest,
                                    encoding='UTF-8',
                                    timeout=timeoutSecs)
            # raise ValueError('A very specific bad thing happened.')
            raisedException = False
        except subprocess.TimeoutExpired:
            showShRunnerError('Process timed out after {} seconds\n\nCommand: [{}]'.format(timeoutSecs, self.runcmd))
            return
        except Exception as err:
            showShRunnerError("Unexpected Exception ({}):\n{}\n\nOffending Command:\n{}".format(err.__class__.__name__, err, self.runcmd))
        finally:
            self.window.active_view().set_status("terry", "")
            if raisedException:
                return
        # sublime.message_dialog('errorRes = {}\ntext = {} [{}]'.format(cmdRes.returncode, cmdRes.stdout, cmdRes.stderr))
        # Stop on error if required by settings
        if retrieveSetting("textCmdStopOnErr", self.cmdArgs, self.shrunner_settings):
            if cmdRes.returncode != 0:
                textOp = "stdout:: " + cmdRes.stdout
                if not combineStreams:
                    textOp += "\nstderr:: {}".format(cmdRes.stderr)
                showShRunnerError("Error code {} running command:\n{}\n\n{}".format(cmdRes.returncode, self.runcmd, textOp))
                return

        ## Step 4: Send command output to set destination
        if self.output_dest == "newTab":
            self.output_file = sublime.active_window().new_file()
            newTabName = retrieveSetting("outputTabName", self.cmdArgs, self.shrunner_settings)
            if newTabName:
                self.output_file.set_name(newTabName)
            self.output_file.run_command("do_view_insert", {'pos': self.output_file.size(), "text": cmdRes.stdout})
        elif self.output_dest == "sublConsole":
            sublime.active_window().run_command('show_panel', {"panel": "console", "toggle": False})
            # sys.stdout.write(cmd_output)
            print (cmdRes.stdout)
        elif self.output_dest == "cursorInsert":
            self.window.active_view().run_command('insert', {"characters": cmdRes.stdout})

    def is_enabled(self, **tkwargs):
        self.visArgs = tkwargs
        return amIEnabled(self.visArgs)



        # visRes = True
        # if extnVals:
        #     self.window.extract_variables().get('file_extension')
        # # self.is_visible(self, paths, application, extensions, args=[])
        # return True

    # def is_visible(self, paths=[], application="", extensions="", args=[]):
    #     if extensions == "*":
    #         extensions = ".*"
    #     if extensions == "":
    #         return CACHED_SELECTION(paths).len() > 0
    #     else:
    #         has = CACHED_SELECTION(paths).hasFilesWithExtension(extensions)
    #         return has or (
    #             not has
    #             and not s.get(
    #                 "hide_open_with_entries_when_there_are_no_applicable", False
    #             )
    #         )


