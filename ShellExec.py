import sys
import os
import pathlib
# import time
import sublime
import sublime_plugin
import re
import subprocess
import shlex
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
        self.have_command = bool(self.shrunner_settings.get("open_terminal_cmd", None))
    def is_visible(self, **kwargs):
        return self.have_command
    def is_enabled(self, **kwargs):
        return self.have_command
    def run(self, **kwargs):
        if self.have_command:
            change_dir = sublime.active_window().extract_variables().get('file_path', '.')
            cmd_array = splitCommand(self.shrunner_settings.get("open_terminal_cmd"))
            subprocess.Popen(cmd_array, cwd=change_dir)


class ShellSpawnCommandCommand(sublime_plugin.WindowCommand):
    def run(self, **kwargs):
        self.cmdArgs = kwargs
        sublime.message_dialog('args = {}'.format(self.cmdArgs))
        sublSettings = self.window.extract_variables()
        subl_top_folder_path = sublSettings.get("folder")
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

class ShellRunTextCommandCommand(sublime_plugin.WindowCommand):

    def run(self, **kwargs):
        self.cmdArgs = kwargs
        sublime.message_dialog('args = {}'.format(self.cmdArgs))
        sublSettings = self.window.extract_variables()
        subl_top_folder_path = sublSettings.get("folder")
        self.shrunner_settings = sublime.load_settings(plugin_settings_file)
        proj_plugin_settings = sublime.active_window().active_view().settings().get(plugin_canon_name, {})
        # any ShellRunner settings in the .sublime-project file will override same name Default/User settings
        self.shrunner_settings.update(proj_plugin_settings)
        self.runcmd = retrieveSetting("command", self.cmdArgs)
        if not self.runcmd:
            showShRunnerError("No command defined.")
            return
        self.output_dest = retrieveSetting("outputTo", self.cmdArgs, self.shrunner_settings)
        if not self.output_dest in ['newTab', 'sublConsole', 'cursorInsert']:
            showShRunnerError("'outputTo' is incorrectly defined in settings. [{}] is invalid.".format(self.output_dest))
            return

        self.runcmd = sublime.expand_variables(self.runcmd, sublSettings)

        # cmd_output = subprocess.check_output(splitCommand(self.runcmd), encoding='UTF-8')
        doChgDir = retrieveSetting("initChangeDir", self.cmdArgs, self.shrunner_settings)
        if not isinstance(doChgDir, bool):
            showShRunnerError("Settings error: 'initChangeDir' must be defined True or False, not [{}]".format(doChgDir))
            return
        if doChgDir:
            change_dir = sublime.active_window().extract_variables().get('file_path', '.')
        else:
            change_dir = "."

        combineStreams = retrieveSetting("cmdCombineOutputStreams", self.cmdArgs, self.shrunner_settings)
        if not isinstance(combineStreams, bool):
            showShRunnerError("Settings error: 'cmdCombineOutputStreams' must be defined True or False, not [{}]".format(combineStreams))
            return
        if combineStreams:
            errDest = subprocess.STDOUT
        else:
            errDest = subprocess.PIPE

        timeoutSecs = retrieveSetting("textCmdTimeout", self.cmdArgs, self.shrunner_settings)
        try:
            cmdRes = subprocess.run(splitCommand(self.runcmd),
                                    cwd=change_dir,
                                    stdout=subprocess.PIPE,
                                    stderr=errDest,
                                    encoding='UTF-8',
                                    timeout=timeoutSecs)
            # raise ValueError('A very specific bad thing happened.')
        except subprocess.TimeoutExpired:
            showShRunnerError('Process timed out after {} seconds\n\nCommand: [{}]'.format(timeoutSecs, self.runcmd))
            return
        except Exception as err:
            showShRunnerError("Unexpected Exception ({}):\n{}\n\nOffending Command:\n{}".format(err.__class__.__name__, err, self.runcmd))
            return
        
        sublime.message_dialog('errorRes = {}\ntext = {} [{}]'.format(cmdRes.returncode, cmdRes.stdout, cmdRes.stderr))

        if retrieveSetting("textCmdStopOnErr", self.cmdArgs, self.shrunner_settings):
            if cmdRes.returncode != 0:
                textOp = "stdout:: " + cmdRes.stdout
                if not combineStreams:
                    textOp += "\nstderr:: {}".format(cmdRes.stderr)
                showShRunnerError("Error code {} running command:\n{}\n\n{}".format(cmdRes.returncode, self.runcmd, textOp))
                return

        if self.output_dest == "newTab":
            self.output_file = sublime.active_window().new_file()
            self.output_file.set_name("ShellRunner Output")
            self.output_file.run_command("do_view_insert", {'pos': self.output_file.size(), "text": cmdRes.stdout})
        elif self.output_dest == "sublConsole":
            sublime.active_window().run_command('show_panel', {"panel": "console", "toggle": False})
            # sys.stdout.write(cmd_output)
            print (cmdRes.stdout)
        elif self.output_dest == "cursorInsert":
            self.window.active_view().run_command('insert', {"characters": cmdRes.stdout})


