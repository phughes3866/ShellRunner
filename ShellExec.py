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

class TerminalRunCmdCommand(sublime_plugin.WindowCommand):
    def run(self, **kwargs):
        self.args = kwargs

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
            cmd_array = shlex.split(self.shrunner_settings.get("open_terminal_cmd"), posix=True)
            subprocess.Popen(cmd_array, cwd=change_dir)

class ShellExecRunPhCommand(sublime_plugin.WindowCommand):
    def run(self, **kwargs):
        self.args = kwargs
        sublime.message_dialog('args = {}'.format(self.args))
        sublSettings = self.window.extract_variables()
        subl_top_folder_path = sublSettings.get("folder")
        shrunner_settings = sublime.load_settings(plugin_settings_file)
        proj_plugin_settings = sublime.active_window().active_view().settings().get(plugin_canon_name, {})
        # any ShellRunner settings in the .sublime-project file will override same name Default/User settings
        shrunner_settings.update(proj_plugin_settings)
        self.runcmd = self.args.get("command")
        if not self.runcmd:
            showShRunnerError("No command defined.")
            return

        # if args.get("format"):
        #   command = args["format"].replace('${input}', command)

        regexp = re.compile(r'\${[a-zA-Z_]+}')
        if regexp.search(self.runcmd):
            # print('matched')
            for region in self.window.active_view().sel():
                (row,col) = self.window.active_view().rowcol(self.window.active_view().sel()[0].begin())

                self.runcmd = self.runcmd.replace('${row}', str(row+1))
                self.runcmd = self.runcmd.replace('${region}', self.window.active_view().substr(region))
                # break as we only take initial selection (not multi)
                break

            # packages, platform, file, file_path, file_name, file_base_name,
            # file_extension, folder, project, project_path, project_name,
            # project_base_name, project_extension.
            self.runcmd = sublime.expand_variables(self.runcmd, sublSettings)

        # sublime.message_dialog("self.runcmd is: {}".format(self.runcmd))

        # bashCommand = "ls -la"
        # process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        # output, error = process.communicate()
        # from subprocess import check_output
        # output = subprocess.check_output(bashCommand.split())
        # output = output.decode("utf-8") 
        # sublime.message_dialog('output={}, ---error={}'.format(output, error))
        # sublime.message_dialog('type={}, output={}'.format(type(cmd_output), cmd_output))

        self.output_dest = self.args.get("output")
        if self.output_dest in ['file', 'panel', 'insert']:
            cmd_output = subprocess.check_output(self.runcmd.split(), encoding='UTF-8')
            if self.output_dest == "file":
                self.output_file = sublime.active_window().new_file()
                self.output_file.set_name("ShellRunner Output")
                self.output_file.run_command("do_view_insert", {'pos': self.output_file.size(), "text": cmd_output})
            elif self.output_dest == "panel":
                sublime.active_window().run_command('show_panel', {"panel": "console", "toggle": False})
                # sys.stdout.write(cmd_output)
                print (cmd_output)
            elif self.output_dest == "insert":
                self.window.active_view().run_command('insert', {"characters": cmd_output})
        else:
            cmd_array = shlex.split(self.runcmd, posix=True)
            subprocess.Popen(cmd_array)
            print ("ShellRunner spawned: {}".format(self.runcmd))

        # self.output_file.set_scratch(True)
        # an_edit = self.output_file().begin_edit()
        # self.output_file().insert(edit, self.output_file().sel()[0].begin(), "honey happiness")
        # self.output_file.insert(an_edit, 0, 'Hello')
        # self.output_file().end_edit(an_edit)
        # self.window.active_view().run_command("do_view_insert",{"text": output})
        # edit = self.window.active_view().begin_edit()
        # self.window.active_view().insert(edit, self.window.active_view().sel()[0].begin(), "howzy")
        # self.window.active_view().end_edit(edit)
        # window = self.output_file.window()
        # window.focus_view(self.output_file)
        # self.output_file.run_command("insert",{"characters": output})
        # window.focus_view(self.output_file)
        # self.output_file.run_command("insert",{"characters": output})
        # self.view.insert(edit, pos, text)
        # sublime_shell_source = ''

        # sh_file_settings = ShellExec.get_setting('load_sh_file', args, True)
        # sh_file_shortcut = ShellExec.get_setting('load_sh_file', args, False)

        # sublime_shell_source = ShellExec.load_sh_file(sublime_shell_source, sh_file_settings, args)

        # if sh_file_settings != sh_file_shortcut:
        #   sublime_shell_source = ShellExec.load_sh_file(sublime_shell_source, sh_file_shortcut, args)

        # if ShellExec.get_setting('debug', args):
            # print('new Thread')

        # t = Thread(target=ShellExec.execute_shell_command, args=(sublime_shell_source, command, pure_command, args))
        # t.start()
