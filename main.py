import os
import sys
import pathlib
import sublime
import sublime_plugin
import subprocess
# import shlex
import shutil
import time
import trace
import pprint
import json
import copy
import zipfile
import inspect
pp = pprint.PrettyPrinter(indent=4)
from threading import Thread
from .utils.constants import pluginEnv, honeRunArgs, pluginSettingsGovernor
from .utils.utils import buildPathFileDirSidebarItemStrings, splitCommand, truncateStr, cmdEnabledInMenu
from .utils.utils import makeLiteralStr, deListCmd, cmdManips
from collections import namedtuple
initFileInfo = namedtuple('initFileInfo', 'filePath templateFromPackage templateDefaultStr')


try:
    from saltydog.saltydog import pluginCentraliser
except:
    from .utils.saltydog import pluginCentraliser

global pluginCentral

if int(sublime.version()) >= 3114:

    # Clear module cache to force reloading all modules of this package.
    prefix = __package__ + "."  # don't clear the base package
    for module_name in [
        module_name
        for module_name in sys.modules
        if module_name.startswith(prefix) and module_name != __name__
    ]:
        del sys.modules[module_name]
    prefix = None

    # Import public API classes
    # from .core.command import MyTextCommand
    # from .core.events import MyEventListener

    def plugin_loaded():
        """
        Initialize plugin:
        This module level function is called on ST startup when the API is ready. 
        """
        global pluginCentral
        pluginCentral = pluginCentraliser(pluginSettingsGovernor, pluginEnv)
        print(f'{pluginCentral.pluginName} settings initialised')

    def plugin_unloaded():
        """
        This module level function is called just before the plugin is unloaded.
        Complete tasks.
        Cleanup package caches.
        Exit threads.
        """
        # deactivateSettings()
        print(f'{pluginEnv["pluginName"]} unloaded')
        # pass

else:
    raise ImportWarning(f"The ?? plugin doesn't work with Sublime Text versions prior to 3114")

def get_kwargs():
    frame = inspect.currentframe().f_back
    keys, _, _, values = inspect.getargvalues(frame)
    kwargs = {}
    for key in keys:
        if key != 'self':
            kwargs[key] = values[key]
    return kwargs

outputToPythonValues = ['newTab', 'sublConsole', 'cursorInsert', 'msgBox', 'clip', None]
outputToJsonValues = [ value if value is not None else 'null' for value in outputToPythonValues ]
outputToJsonKeyStr = str(outputToJsonValues)

# initiate a global variable with the current platform (windows, linux or osx)
# `- and format the variable to a way it can be used in sublime text filenames (Windows, Linux, OSX)
curPlatform = sublime.platform()
if curPlatform == "osx":
    curPlatform = "OSX"
else:
    curPlatform = curPlatform.capitalize()

# set up some common filenames (strings) and directories (pathlib paths)
plugin_canon_name = "ShellRunner"
plugin_settings_file = "{}.sublime-settings".format(plugin_canon_name)
sublime_user_dir = pathlib.Path(sublime.packages_path()) / "User"
shellrunner_user_dir = sublime_user_dir / plugin_canon_name

osDefaultShellCommands = {
    "Linux": "ls",
    "Windows": "dir",
    "OSX": "ls"
}

buildCommandArgDefaults = {
    "shellCommand": osDefaultShellCommands[curPlatform],
    "outputTo": "msgBox",
}



class EditShellrunnerSidebarCommandsCommand(sublime_plugin.WindowCommand):
    def run(self):
        args = {"user_file": "${packages}/User/ShellRunner/Side Bar.sublime-menu",
                "base_file": "${packages}/ShellRunner/menus/exampleBase/ShellRunner(Linux)SideBar.sublime-menu-example",
                # "default": ??
                }
        self.window.run_command('edit_settings', args)


class EditShellrunnerContextCommandsCommand(sublime_plugin.WindowCommand):
    def run(self):
        args = {"user_file": "${packages}/User/ShellRunner/Context.sublime-menu",
                "base_file": "${packages}/ShellRunner/menus/exampleBase/ShellRunner(Linux)Context.sublime-menu-example",
                }
        self.window.run_command('edit_settings', args)


class SideBarMenuVisabilityControlCommand(sublime_plugin.WindowCommand):
    def is_visible(self):
        return pluginCentral.settingsAsDict().get('sideBarMenuOn', True)

class ContextMenuVisabilityControlCommand(sublime_plugin.WindowCommand):
    def is_visible(self):
        return pluginCentral.settingsAsDict().get('contextMenuOn', True)

class runSafeSubprocess():
    def __init__(self, cmdTokens: list, **processArgs):
        self.OK = False
        self.cmdResult = None
        self.failStr = ""
        try:
            self.cmdResult = subprocess.run(cmdTokens, **processArgs)
            self.OK = True
        except subprocess.TimeoutExpired:
            self.failStr = (f'The given shell command timed out after {processArgs.get("timeout", "excess")} seconds.\n\n'
                             'The timeout can be set in the range 1-600 seconds.')
        except Exception as err:
            self.failStr = ("Shell command failed as an unexpected exception occurred.\n\n"
                              "Details:: {}\n\n{}".format(err.__class__.__name__, err))


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
    Captured text from text commands is output to the given destination(s) 
    If an error/exception occurs then an error msg is stored in an object attribute (self.errStr) which is
    `- also output by a thread manager (in a sublime message_dialog box) on thread completion.
    """
    def __init__(self, **passedArgs):
        super(runShellCommand, self).__init__()
        self.cmdArgs = passedArgs
        self.commandSuccess = False # only set to True at end of run, if applicable
        self.errStr = None # only set if an error is encountered running the shell command thread

    def name(self):
        return 'shellRunner Thread Process'

    def run(self):
        # compile the processArgs that will be passed to the 'runSafeSubprocess' execution function
        # 1: Set the 'cwd' arg
        processArgs = {}
        processArgs["cwd"] = self.cmdArgs["initChangeDir"]
        # 2: Set the 'env' arg
        if self.cmdArgs["cleanShellEnv"]:
            exportEnv = {}
        else:
            exportEnv = os.environ.copy()
        exportEnv.update(self.cmdArgs["exportEnv"])
        processArgs["env"] = exportEnv
        processArgs["timeout"] = self.cmdArgs["cmdTimeout"]
        # If we have a text capture command, further args should be set as follows
        if self.cmdArgs.get('textOutputMode'):
            if self.cmdArgs["cmdCombineOutputStreams"]:
                errDest = subprocess.STDOUT
            else:
                errDest = subprocess.PIPE
            processArgs["stdout"] = subprocess.PIPE
            processArgs["stderr"] = errDest
            processArgs["encoding"] = 'UTF-8'

        pluginCentral.dBug("Compiled shell command args::\n{}\n".format(pp.pformat(processArgs)))
        pluginCentral.dBug("Running shell command NOW:")
        runObj = runSafeSubprocess(self.cmdArgs["shellCommand"], **processArgs)
        if not runObj.OK:
            # if the run was unsuccessful, set our errStr, using the runObj.failStr, and return
            self.errStr = ("Shell command failed. No text processed.\n\n"
                              f"Offending command::\n{self.cmdArgs['origCmd50CharLabel']}\n\n"
                              f"Failure Details::\n{runObj.failStr}")
            return

        pluginCentral.dBug("Cmd completed with exit code: {}".format(runObj.cmdResult.returncode))
        if self.cmdArgs.get('textOutputMode'):
            pluginCentral.dBug("Starting Text Command Post Processing")
            if self.cmdArgs.get("textCmdStopOnErr", False):
                if runObj.cmdResult.returncode != 0:
                    # We have found a shell error code that we must stop for:
                    # `- So we can set our errStr accordingly, and return
                    textOp = "stdout:: " + runObj.cmdResult.stdout
                    if not self.cmdArgs["cmdCombineOutputStreams"]:
                        textOp += "\nstderr:: {}".format(runObj.cmdResult.stderr)
                    self.errStr = ("No text processed due to error code {} being returned from the shell.\n\n"
                                      "Offending command:: {}\n\n{}".format(runObj.cmdResult.returncode, 
                                                                            self.cmdArgs["origCmd50CharLabel"],
                                                                            textOp))
                    return
            elif runObj.cmdResult.returncode != 0:
                pluginCentral.dBug("Non-zero shell exit code ({}) ignored as \"textCmdStopOnErr\" is false.".format(runObj.cmdResult.returncode))
            self.commandSuccess = True
            rxText = runObj.cmdResult.stdout
            if rxText:
                pluginCentral.dBug("Outputting text to {}".format(self.cmdArgs["outputTo"]))
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
                        sel = self.cmdArgs.get('targetView').sel();
                        for s in sel:       
                            self.cmdArgs.get('targetView').run_command('view_insert_big_text', {'pos': s.a, 'text': rxText})
                    elif destination == "msgBox":
                        # show msgbox in a new thread so this thread can end
                        sublime.set_timeout_async(lambda: sublime.message_dialog(rxText))
                    elif destination == "clip":
                        sublime.set_clipboard(rxText)
                        # subprocess.Popen(('xsel', '-i', '-b'), stdin=subprocess.PIPE).communicate(bytearray(rxText, 'utf-8'))
        else:
            pluginCentral.dBug("Non Text Command spawning complete")
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

    # def name(self):
        # return 'thread manager'

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
                    pluginCentral.error_message(self.thread.errStr)
                return
            active_view.set_status('_shellRunner', self.success_message)
            # if self.thread.outputMsgBox is not None:
                # sublime.message_dialog(self.thread.outputMsgBox)
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

class ShellRunnerCommand(sublime_plugin.WindowCommand, cmdEnabledInMenu, cmdManips):

    def focus(self, window_to_move_to):
        active_view = window_to_move_to.active_view()
        if active_view is not None:
            window_to_move_to.focus_view(active_view)

    def parseArgs(self):
        # :Step A1: Parse the run command into string formats for display usage
        cmdAsString = json.dumps(self.shellCmdAsStr(self.cmdArgs.get("shellCommand", "")))
        self.cmdArgs["origCmd50CharLabel"] = truncateStr(cmdAsString, outputLength=50)

        # :Step A2: Parse the run command into tokens for execution purposes
        self.cmdArgs["shellCommand"], tokenErr = self.shellCmdAsTokens(self.cmdArgs.get("shellCommand", ""))
        if tokenErr:
            pluginCentral.console_message(tokenErr)
            return False

        # :Step A3: Calculate some 'programmatic' modal variables
        # if command was activated in a view (i.e. context menu) the mouse 'event' contains 'x' 'y' coordinates
        self.cmdArgs['sideBarMode'] = 'x' not in self.cmdArgs.get('event', {})
        self.cmdArgs['textOutputMode'] = "outputTo" in self.cmdArgs
        self.cmdArgs['targetView'] = self.window.active_view()

        # We have our base shellCommand, now we need to expand any substitution variables it contains
        # `- so we must build a dictionary of substitution variables that can be expanded in our command
        #  - This is done in steps A to G below
        # A: get the sublime window env. placeholder variables
        # `- e.g. ${packages} ${platform} ${file} ${file_path} ${file_name} ${file_base_name} ${project_extension}
        #  - ${file_extension} ${folder} ${project} ${project_path} ${project_name} ${project_base_name}
        replacementVars = self.window.extract_variables()
        # B: Use shell env vars in substitution string if cleanShellEnv is not set
        if not self.cmdArgs["cleanShellEnv"]:
            # self.dBug("Including shell env vars as substitution vars")
            replacementVars.update(os.environ.copy())
        # C: if we're in sidebar mode: compile available strings of side bar selected items
        # `- ${paths}, ${lastPath}, ${dirs}, ${lastDir}, ${files}, ${lastFile}
        #  - (all as escaped 'shell friendly' strings) 
        if self.cmdArgs['sideBarMode']:
            replacementVars.update(buildPathFileDirSidebarItemStrings(self.cmdArgs))
        # D: get any extra, user defined "global" substitution variables
        replacementVars.update(pluginCentral.settingsAsDict().get("extraGlobalSubstVars", {}))
        # E: get any extra, user defined "local" command-arg substitution variables
        replacementVars.update(self.cmdArgs.get("extraCmdSubstVars", {}))
        # F: build a dictionary of new env vars from global and cmd args settings
        # `- we use it here for substitution vars, later it will update the shell environment
        self.cmdArgs["exportEnv"] = pluginCentral.settingsAsDict().get("extraGlobalShellEnvVars", {})
        self.cmdArgs["exportEnv"].update(self.cmdArgs.get("extraCmdShellEnvVars", {}))
        replacementVars.update(self.cmdArgs["exportEnv"])
        # F: add one (or all) selected region(s), (and separated by 'multiSelSeparator') - ${selText}
        sel = self.window.active_view().sel()
        replacementVars["selText"] = ""
        selSeparator = self.cmdArgs.get("multiSelSeparator", pluginCentral.settingsAsDict().get("multiSelSeparator", " "))
        selLiteral = self.cmdArgs.get("selAsLiteralStr", pluginCentral.settingsAsDict().get("selAsLiteralStr", False))
        buildAll = []
        for s in sel:
            foundStr = self.window.active_view().substr(s)
            if foundStr:
                buildAll += [foundStr]
        if buildAll:
            replacementVars["selText"] = selSeparator.join(buildAll)
        if selLiteral:
            replacementVars["selText"] = makeLiteralStr(replacementVars["selText"])
        # G: add the shellCommand itself as a replacement var
        replacementVars["shellCommand"] = makeLiteralStr(cmdAsString)           
        pluginCentral.dBug("Substitution dictionary compiled as::\n{}\n".format(pp.pformat(replacementVars)))
        # End of compilation of 'replacementVars'

        # perform var substitution on each individual token in shellCommand
        pluginCentral.dBug("Pre-substitution  \"shellCommand\" tokens:\n{}\n".format(pp.pformat(self.cmdArgs["shellCommand"])))
        for count, shellToken in enumerate(self.cmdArgs["shellCommand"]):
            self.cmdArgs["shellCommand"][count] = sublime.expand_variables(shellToken, replacementVars)
        pluginCentral.dBug("Post-substitution \"shellCommand\" tokens:\n{}\n".format(pp.pformat(self.cmdArgs["shellCommand"])))

        # :Step A4: Check 'initChangeDir' setting to see if we should change dir, to file loc, before running command
        # Note: We read this as 'boolean' but change it to a path (str) of the directory into which we'll cd
        doChgDir = self.cmdArgs.get("initChangeDir", pluginCentral.settingsAsDict().get("initChangeDir", True))
        # doChgDir = getArgOrGlobalSetting("initChangeDir", self.cmdArgs, finalResortVal=True)
        # if not isinstance(doChgDir, bool):
        #     self.console_message("\"initChangeDir\" must be defined [true or false (type=bool)].\n\n"
        #                         "The current setting [{} (type={})] is invalid.".format(doChgDir, type(doChgDir)))
        #     return False
        # self.dBug("\"initChangeDir\" (orig bool) = {}".format(doChgDir))
        if doChgDir:
            self.cmdArgs["initChangeDir"] = self.window.extract_variables().get('file_path', '.')
        else:
            self.cmdArgs["initChangeDir"] = "."
        pluginCentral.dBug("\"initChangeDir\" (as dir)  = {}".format(self.cmdArgs["initChangeDir"]))

        # :Step A5: Check 'outputTo' is defined correctly:
        if self.cmdArgs.get("outputTo"):
            self.cmdArgs["outputTo"] = list(set(self.cmdArgs["outputTo"]))  # ensure list contains no duplicates
            pluginCentral.dBug("\"outputTo\" (as list)  = {}".format(self.cmdArgs["outputTo"]))

        pluginCentral.dBug("Shell command arguments ALL CHECKED OK")
        # :All checks OK. self.cmdArgs prepared for running phase
        return True

    def run(self, **args):
        pluginCentral.dBug("RAW ARGS FOR THE COMMAND WE ARE AIMING TO RUN:\n{}\n".format(pp.pformat(args)))

        self.cmdArgs, errorRep = honeRunArgs(args)
        if errorRep:
            pluginCentral.error_message(f'Please correct errors in command arguments:\n\n{errorRep}')
            return
        pluginCentral.dBug("HONED ARGS FOR THE COMMAND WE ARE AIMING TO RUN:\n{}\n".format(pp.pformat(self.cmdArgs)))


        if not self.parseArgs():
            pluginCentral.error_message("Could not run the command.\n\nCheck sublime text's console output for reasons.")
            return
        pluginCentral.dBug("PARSED ARGS FOR THE COMMAND WE ARE AIMING TO RUN:\n{}\n".format(pp.pformat(self.cmdArgs)))

        # if not self.cmdArgs['textOutputMode']:
        #     doSpawnCommand = runShellCommand(**self.cmdArgs)
        #     doSpawnCommand.start()
        # else:
        # run the command as a thread and show its progress in the status bar
        doCommand = runShellCommand(**self.cmdArgs)
        doCommand.start()
        status_message = "ShellRunner running: {}".format(self.cmdArgs["origCmd50CharLabel"])
        ThreadProgress(doCommand, status_message, "ShellRunner command completed OK")
        self.focus(self.window)

    def want_event(self):
        # this ensures an 'event' dict of mouse coordinate variables is included with the run args
        # ` when the command is mouse activated
        return True

    def is_enabled(self, **tkwargs):
        self.visArgs = tkwargs
        viewInMenu = cmdEnabledInMenu(self.visArgs, self.window.extract_variables())
        if viewInMenu.is_enabled():
            return True
        else:
            pluginCentral.console_message(viewInMenu.disabledReason)
            return False