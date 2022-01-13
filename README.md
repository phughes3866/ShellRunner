# ShellRunner Plugin README.md

ShellRunner enables Linux Sublime Text users to run (user defined) shell commands from the Sublime Text sidebar menu or key bindings.

Shell commands can be run in one of the following three ways:

1. Run a command, capture its textual output and insert this in a user defined destination e.g. at the insertion point(s) of the file under edit, or in the sublime text console, or to a new file/tab.
2. Spawn a command in a separate process and return control immediately to sublime text (useful when you're not interested
in capturing the output of the shell command)
3. Spawn a user defined 'Open Terminal' command to open the user's preferred terminal emulator

The above three aspects are further detailed below with respect to their configuration and functionality.

# Configuration

## Sidebar Menu

Entries in the sidebar menu can be edited via selecting (in the right-click sidebar menu) `Shell Commands` -> `Edit Shell Commands`. This will open a two panel edit screen with an ExampleSideBar.sublime-menu file on the left and the {Package Dir}/User/ShellRunner/Side Bar.sublime-menu file on the right. Copy across, edit and save any menu commands you wish to implement. No menu commands are enabled by default.

## Key Bindings

Key bindings can be edited/activated via `Preferences` -> `Package Settings` -> `ShellRunner` -> `Settings` -> `Key Bindings`. This will open a two panel editing screen with an Example.sublime-keymap file on the left and the {Package Dir}/User/ShellRunner/Default ({platform}).sublime-keymap file on the right. Copy across, edit and save any key bindings you wish to implement. No key bindings are enabled by default. 

# Commands that capture text (shell_run_text_command)

Here are some examples and explanations of sidebar menu entries for the `shell_run_text_command` 

{
	"caption": "shell output to new tab",
	"command": "shell_run_text_command",
	"args": { "shellCommand": "/usr/bin/bash -c 'echo hello'",
			  "outputTo": "newTab" }
},
{
	"caption": "shell output name of last selected sidebar item to cursor(s)",
	"command": "shell_run_text_command",
	"args": { "shellCommand": "/usr/bin/bash -c \"echo '${lastPath}'\"",
			  "outputTo": "cursorInsert",
			  "paths": [] }
},
{
	"caption": "cat the contents of sidebar selected files to new tab",
	"command": "shell_run_text_command",
	"args": { "shellCommand": "/usr/bin/bash -c \"cat ${files}\"",
			  "outputTo": "newTab",
			  "files": [] }
},

# Commands that spawn a shell process (shell_spawn_command)

Here are some examples and explanations of sidebar menu entries for the `shell_spawn_command` 

{
	"caption": "spawn totp and bash in urxvt",
	"command": "shell_spawn_command",
	"args": { "shellCommand": "/usr/bin/urxvt -e /usr/bin/bash -c '/usr/local/phscripts/totp; /usr/bin/bash'",
			  "initChangeDir": false, "paths": [], "dirs": [], "dirOnly": true }
},
{
	"caption": "spawn evince",
	"command": "shell_spawn_command",
	"args": { "shellCommand": "/usr/bin/evince",
			  "initChangeDir": false, "paths": [] }
},

## List of possible args for shell_run_text_command and shell_spawn_command:

### files, dirs, paths:

These arguments, if given, must be set to an empty list. Each setting enables lists of sidebar selected files/dirs/paths items to be used as substitution variables in the shellCommand argument. See 'Sidebar Variables' below for more details:

"files": [] // enables ${files} and ${lastFile} substitution variables.
"dirs": [] // enables ${dirs} and ${lastDir} substitution variables.
"paths": [] // enables ${paths} and ${lastPath} substitution variables. NB Paths are either files or dirs (no discrimination).

### args for both commands (shell_run_text_command and shell_spawn_command):

"shellCommand": "string" // the actual shell command you wish to run (mandatory). May include substitution variables (see below for options and syntax)
"targetExtns": [] // list of extensions e.g. ["jpg", "png"] for which this command is enabled (optional). N.B. either "files" or "dirs" arg must also be given so that file extensions can be checked.
"dirOnly": true/false // Allow this command only for directories. Defaults to false. N.B. "dirs" arg must also be given.
"initChangeDir": true/false // If true (default) change the working directory to that of the [???] before running the shellCommand

### Additional args for shell_run_text_command only:

"outputTo": ""
	String value to determine the destination of shellCommand output text. Can be one of:  'newTab', 'sublConsole', 'cursorInsert', 'clip', null (output is not sent anywhere). 

"textCmdStopOnErr": true/false
	Default = false. If 'true' then do not output any text if there is an error code returned from the shell command, but rather report the error code, in a Sublime Text message window, along with the stdout and stderr text received.

"textCmdCombineStdErrOut": true/false
	If false (the default) then capture only stdout text. If true then capture both stdout and stderr.

"textCmdTimeout": Integer
	The number of seconds (default 10) to wait for the shellCommand to complete.

### Substitution Variables for Commands

ShellRunner commands can contain placeholder variables. These will be substituted for the relevant value (if available) at command run time. The syntax for the placeholder variables is as per sublime-snippet syntax e.g. ${folder}. Placeholder variables are of two types: a) variables corresponding to the active window e.g. file under edit, and b) variables corresponding to the files or folders selected in the sidebar.

#### Active Window Variables

The following variables correspond to the sublime text environment and currently active edit window:

${packages}
${platform}
${file}
${file_path}
${file_name}
${file_base_name}
${project_extension}
${file_extension}
${folder}
${project}
${project_path}
${project_name}
${project_base_name}

Note: These variables do not have escaped spaces so may not be directly usable by the shell if they contain spaces.

#### Sidebar Variables

Accurate information concerning the selected items in the sidebar can be utilised, as follows, if one or more
or the following arguments are included in the command args to the ShellRunner command: 'paths': [], 'files': [], 'dirs': []

1) Available if the "paths": [] arg is contained in the command args:

* ${paths}		- a space separated list of all the files/folders selected in the sidebar
* ${lastPath}	- the most recently selected (and still selected) file/folder in the sidebar

2) Available if the "files": [] arg is contained in the command args:

* ${files}		- a space separated list of all the files selected in the sidebar
* ${lastFile}	- the most recently selected (and still selected) file in the sidebar

3) Available if the "dirs": [] arg is contained in the command args:

* ${dirs}		- a space separated list of all the folders selected in the sidebar
* ${lastDir}	- the most recently selected (and still selected) folder in the sidebar

Note: If the required arg is not passed as a command arg then the corresponding placeholder variables will be substituted with
an empty string.

Note: In contrast with the active window placeholder variables, the string replacements for the sidebar variables are shell escaped and so can be directly used in shell commands.


