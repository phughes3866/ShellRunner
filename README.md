[![Package Control](https://img.shields.io/packagecontrol/dt/ShellRunner?style=flat-square)](https://packagecontrol.io/packages/ShellRunner)
[![GitHub tag (latest SemVer)](https://img.shields.io/github/tag/phughes3866/ShellRunner?style=flat-square&logo=github)](https://github.com/phughes3866/ShellRunner/tags)
[![Project license](https://img.shields.io/github/license/phughes3866/ShellRunner?style=flat-square&logo=github)](https://github.com/phughes3866/ShellRunner/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/phughes3866/ShellRunner?style=flat-square&logo=github)](https://github.com/phughes3866/ShellRunner/stargazers)

# ShellRunner Plugin README

> ShellRunner is a Sublime Text Plugin for running shell commands and using the returned text for editing purposes.

ShellRunner enables Sublime Text users to run user defined shell commands from the Sublime Text sidebar menu, context menu or key bindings, and to optionally output the text returned from these shell commands to one (or more) of the following five destinations: a new Sublime Text tab; the edit point(s) in the active document; a message box; the Sublime Text console; the clipboard. A wide variety of [substitution variables](#substitution-variables-for-commands) are available for building the shell commands, thus enabling aspects of Sublime Text to easily be used in the shell e.g. ${selText}, ${folder}, ${file}. Shell environment variables can also be erased, added or changed for the new command environment. As a separate feature to the 'command-running' commands ShellRunner has an 'Open Terminal Here' command, which can be configured to be displayed in the sidebar, tab and context menus. The 'Open Terminal Here' command can be configured to open a terminal emulator of your choice.

There are other Sublime Text plugins which can run Linux shell commands for you. None of them presently (Feb 2022) offer the range of configurability which ShellRunner provides.

Note: Currently the ShellRunner plugin is only operational on a Linux platform.

## Installation
Installation should be carried out via package control using the [Sublime Package Manager](http://wbond.net/sublime_packages/package_control). This can be accessed via the command palette as follows:

* `Ctrl+Shift+P` or `Cmd+Shift+P`
* type `install`, select `Package Control: Install Package`
* type `shell`, select `ShellRunner`

In the case that ShellRunner is not available in the standard packagecontrol.io repository it is also possible to clone from the [ShellRunner github repository](https://github.com/phughes3866/ShellRunner) directly into your Sublime Text *Packages* directory. Alternatively you can add this repo to Sublime's list of package repos (via command palette: Package Control: Add Repository) and install via the standard package control method (as above).

## Functional Overview

The command-running side of ShellRunner utilises two types of commands:

1. **Text Commands**: To capture the command's output text we can use either the `sidebar_shellrunner_text_command` (for the sidebar menu) or the `window_shellrunner_text_command` (for the context menu and key bindings). With these ShellRunner commands we can run a shell command from within the Sublime Text environment, capture its textual output and insert this in one or more user defined destinations e.g. at the insertion point(s) of the file under edit, or in the Sublime Text console, or to a new file/tab.
2. **Spawn Commands**: To spawn a command in a separate process we can use either the `sidebar_shellrunner_spawn_command` (for the sidebar menu) or the `window_shellrunner_spawn_command` (for the context menu and key bindings). These ShellRunner commands spawn a shell in the background, start a shell command there, and return control immediately to Sublime Text. These *spawn* commands are useful when you're not interested in capturing the output of the shell command e.g. you want to launch an svg editor on .svg files or open .html files in a browser or perform some sysadmin task.

Additionally ShellRunner provides an [Open Terminal Here](#the-open-terminal-here-command) command to give you swift, directory specific, command line shell access when required for additional tinkering.

## ShellRunner Configuration

After a user configures the main [settings file](#shellrunner-settings-file) it will be saved as ${packages}/User/ShellRunner.sublime-settings. Configuration of this file is essential unless you want to operate with ShellRunner's default settings.

Three other configuration files can be generated, depending on what you set up. These will all reside in the ${packages}/User/ShellRunner folder:

*Side Bar.sublime-menu*<br>
*Context.sublime-menu*<br>
*Default (${platform}).sublime-keymap*<br>

*Note:* If you uninstall ShellRunner you can safely delete all these four files and remove the ${packages}/User/ShellRunner folder. This is not necessary however, as leaving the files in place will do no harm to Sublime Text. If you consider that you might reinstall ShellRunner at some future date, it would be best to leave the config files in place so that you don't have to set them all up again when the reinstall takes place.

### Side Bar Menu ShellRunner Commands

Side Bar commands appear under the ShellRunner Commands heading in the side bar menu. What appears here is configurable in a dual panel edit window which can be opened via:

* Command Palette: Preferences: Shell Runner Side Bar Menu
* Main Menu: `Preferences` -> `Package Settings` -> `Shell Runner` -> `Side Bar Menu`
* Side Bar (right click) Menu: `ShellRunner Commands` -> `Edit Side Bar Menu Shell Commands…` (if enabled in settings)

On the left side of the dual panel edit window will be an inactive ExampleSideBar.sublime-menu file containing exemplar commands. On the right will be the active {Package Dir}/User/ShellRunner/Side Bar.sublime-menu file. On first time setup the active file will be empty. Using the inactive example file as a template you can select, copy across, edit and save any sidebar menu commands you wish to implement. You will notice that ShellRunner entries in the sidebar menu each utilise one of the 'sidebar' commands (sidebar_shellrunner_text_command, sidebar_shellrunner_spawn_command), one for returning text and one for spawning commands. 

### Context Menu ShellRunner Commands

Context menu commands appear under the ShellRunner Commands heading in the context menu. What appears here is configurable in a dual panel edit window which can be opened via:

* Command Palette: Preferences: Shell Runner Context Menu
* Main Menu: `Preferences` -> `Package Settings` -> `Shell Runner` -> `Context Menu`
* Context (right click) Menu: `ShellRunner Commands` -> `Edit Context Menu Shell Commands…` (if enabled in settings)

On the left side of the dual panel edit window will be an inactive ExampleContext.sublime-menu file containing exemplar commands. On the right will be the active {Package Dir}/User/ShellRunner/Context.sublime-menu file. On first time setup the active file will be empty. Using the inactive example file as a template you can select, copy across, edit and save any context menu commands you wish to implement. You will notice that ShellRunner entries in the context menu each utilise one of the 'window' commands (window_shellrunner_text_command, window_shellrunner_spawn_command), one for returning text and one for spawning commands.

### Key Bindings for ShellRunner Commands

These too are configurable in a dual panel edit window which can be opened via:

* Command Palette: Preferences: Shell Runner Key Bindings
* Main Menu: `Preferences` -> `Package Settings` -> `Shell Runner` -> `Key Bindings`

ShellRunner key bindings each utilise one of the 'window' commands (window_shellrunner_text_command, window_shellrunner_spawn_command). The dual panel edit window shows an inactive Example.sublime-keymap file on the left and the active {Package Dir}/User/ShellRunner/Default (${platform}).sublime-keymap file on the right. On first time setup the active file will be empty. Using the inactive example file as a template you can select, copy across, edit and save any key bindings you wish to implement.

## Example ShellRunner Commands

Some contrived examples of ShellRunner commands that might appear in your .sublime-menu or .sublime-keymap files::

#### Examples of sidebar menu entries 

	{
		"caption":	"spawn: open picture file in geeqie",
		"command":	"sidebar_shellrunner_spawn_command",
		"args":	{	"shellCommand": "geeqie '${lastFile}'",
				 	"targetExtensions": [".jpg", ".png", ".jpeg"],
				 	"files": [],
				}
	},
	{
		"caption":	"txt: insert stdout in current doc",
		"command":	"sidebar_shellrunner_text_command",
		"args":	{	"shellCommand": "/usr/bin/bash -c 'echo ShellRunner simple insert text demo'",
				 	"outputTo": "cursorInsert",
				}
	},

#### Examples of context menu entries 

	{
		"caption":	"txt: continue despite non-zero shell exit",
		"command":	"window_shellrunner_text_command",
		"args":	{	"shellCommand": "/usr/bin/bash -c 'echo Commands ordinarily fail on non-zero shell exit.; echo But with textCmdStopOnErr false, we do not fail.; exit 77;'",
				 	"outputTo": ["newTab", "clip"],
				 	"textCmdStopOnErr": false, // the default is true, so commands don't ordinarily insert text if they raise errors
					"consoleDebug": true, // send debug messages to console for this command
				}
	},
	{
		"caption":	"txt: send stdout AND stderr to new tab",
		"command":	"window_shellrunner_text_command",
		"args":	{	"shellCommand": ["/usr/bin/bash -c 'echo ShellRunner demo combining stdout and stderr:; ",
									 "echo Shell_stdout ; echo Shell_stderr 1>&2'"],
				 	"cmdCombineOutputStreams": true, // default is false, only capturing stdout
				 	"outputTo": "newTab",
				 	"outputTabName": "stdout-stderr-demo",
				}
	},

#### Examples of key bindings 

	{
		"keys":	["ctrl+alt+1"],
		"command":	"window_shellrunner_text_command",
		"args":	{	
					// This example shows how to use single and double quotes in Env and substitution vars
					"shellCommand": [ "/usr/bin/bash -c 'echo \"Subst VarA: ${Sstra}\"; ",
					                  "echo \"Subst VarB: ${Sstrb}\"; ",
					                  "printf \"Env VarA (as subst): ${Estra}\n\"; ",
					                  "printf \"Env VarB (as subst): ${Estrb}\n\"; ",
					                  "echo \"Env VarA (shell expanded): \\${Estra}\"; ",
					                  "echo \"Env VarB (shell expanded): \\${Estrb}\"; ",
					                  "'",
					                ],
					"outputTo": ["msgBox", "clip"],
					"extraCmdSubstVars":	{ 	"Sstra"	:	"This line's got single quotes. It's working fine.",
												"Sstrb" :   "This line has \\\"double\\\" quotes. They work \\\"fine\\\" too.",
											},
					"extraCmdShellEnvVars":	{ 	"Estra"	:	"BEST_USE_RESTRICTED_CHARSET_FOR_ENV_VARS",
												"Estrb"	:	"It's unclear how the mind's eye works."
											},
				}
	},	{
		"keys":	["ctrl+alt+2"],
		"command":	"window_shellrunner_text_command",
		"args":	{	
					// some special characters in strings e.g. quotes, backslashes, can cause problems with shell syntax
					// `- with the ${selText} substitution variable you can ensure these characters don't cause problems
					//  - by setting "selAsLiteralStr" to true - as follows
					"shellCommand": ["/usr/bin/bash -c '[ -z ${selText} ] && printf -- \"%s\" ",
									"\"Select some awkward text and run again.\n\" ",
									"|| printf -- \"%s\" ${selText};",
									"'"],
					"outputTo": ["msgBox", "clip"],
					"selAsLiteralStr": true,
					"multiSelSeparator": "--joiner--",
				}
	},

## Arguments Provided To ShellRunner commands

### args applicable to all commands

###### "shellCommand": "string" or [ "string", ... ]

This is the actual shell command you wish to run e.g. "ls -la", "echo hello". It can be a single string or a list of strings that will be combined into a single command at run time (this splitting is purely a display convenience to allow for long commands to be placed on multiple lines in the json configuration file, the strings can be split at any arbitrary point). The *shellCommand* may include substitution variables. The syntax for these is the same as for (most) shell variables and Sublime Text snippet variables e.g. ${selText}, ${HOME}. See the [substitution variables](#substitution-variables-for-commands) section below for details of substitution variables that are available for 'sidebar' and 'window' commands. This argument is mandatory and has no default or global settings-file fallback.

###### "targetExtns": []

A list of file extensions e.g. [".jpg", ".png"] for which this command will be enabled. The target extensions must begin with a dot/period and contain no other dots/periods i.e. multiple conjoined extensions, such as ".tar.gz", will not work. This is because the matching algorithm attempts to match the final chunk of the filename from the last dot/period to the end of the filename. For 'window' commands the 'match' check is made against the active window file. For 'sidebar' commands the check is made against the last file selected in the side bar (note that either the "files" or "paths" arg must also be given to ensure this 'sidebar' functionality). If "targetExtns" is unset then no file restrictions are placed on command enablement. This argument is optional and has no default or global settings-file fallback.

###### "initChangeDir": true/false

If true change the command's working directory to that of the last selected side bar file/dir (in the case of 'sidebar' commands), or to the active window file directory (in the case of 'window' commands), before running the *shellCommand*. If false, do not perform a directory change prior to running (this will run the *shellCommand* in the directory from which you launched your Sublime Text executable). This argument is optional and can be globally set in the ShellRunner settings file. If unset it defaults to true.

###### "multiSelSeparator": "string"

This setting influences the behaviour of the ${selText} [command substitution variable](#substitution-variables-for-commands), which substitutes selected text into the *shellCommand*. If there are multiple selections available when ${selText} is used, then they will be joined together into one string, separated by the *multiSelSelector* string. This argument is optional and can be globally set in the ShellRunner settings file. If unset it defaults to a single space.

###### "selAsLiteralStr": true/false

If set to true then translate ${selText} strings into literal shell strings e.g. $'I\'m the "selected" text'. This can save problems with the shell misinterpreting special characters. A 'true' setting should be used if your selections are likely to have a lot of character variation and you wish to represent your selection with high accuracy. This argument is optional and can be globally set in the ShellRunner settings file. If unset it defaults to false.

###### "consoleDebug": true/false

If true, print debug information to the Sublime Text console for a command throughout its enablement / argument checking / and run phases. This can be useful in getting tricky shell commands to work correctly. This argument is settable only in a command's set of arguments. If unset it defaults to false i.e. no debug information is printed.

###### "tabDebugReport": true/false

If true, output a final report of *shellCommand* debug information to a new tab. This provides more information than the *consoleDebug* setting (above), and is visually easier to digest. If unset it defaults to false i.e. no debug report is generated.

###### "extraCmdSubstVars": {"name": "value"}

An optional user defined dictionary of custom *shellCommand* substitution variables. A similar functionality global dictionary *extraGlobalSubstVars* can be defined in the ShellRunner settings file. ShellRunner will combine and use both of these dictionaries for substitution, according to their availability. In the case of both dictionaries being available, same named variables in the command argument **extraCmdSubstVars** dictionary will override those set in the *extraGlobalSubstVars* global dictionary. See the [substitution variables](#substitution-variables-for-commands) section below for more details.

###### "cleanShellEnv": true/false

If set to true then none of the current shell environment variables will be passed into the environment of our soon to be run *shellCommand*. This argument is optional and can be globally set in the ShellRunner settings file. If unset it defaults to false. 

###### "extraCmdShellEnvVars": {"name": "value"}

An optional user defined dictionary of custom environment variables which will be passed as 'extras' into the environment of our soon to be run *shellCommand*. These 'extras' will be passed even if the environment has been cleaned through setting *cleanShellEnv* to true. A similar functionality global dictionary *extraGlobalShellEnvVars* can be defined in the ShellRunner settings. ShellRunner will load environment variables from both dictionaries, if present. Same named variables in the command argument **extraCmdShellEnvVars** dictionary will override those set in the *extraGlobalShellEnvVars* global dictionary. Additionally these environment variables (along with the inherited shell environment variables- if *cleanShellEnv* is false) will be used as [substitution variables](#substitution-variables-for-commands) against the *shellCommand* prior to it being run.

### Additional args for 'text' capturing commands only:

###### "outputTo": "string" or [ "string", ... ]

One or several string values (in a list) to determine the destination(s) to which *shellCommand* output text will be sent. Acceptable **outputTo** destinations are: "newTab", "sublConsole", "msgBox", "cursorInsert", "clip" (the clipboard), and null (output is discarded). This argument must be set in the local args or globally set in the ShellRunner settings file. If left unset there is no default and an error will be generated. 

###### "outputTabName": "string"

A string by which to name new Sublime Text tabs that are generated by ShellRunner when the *outputTo* argument is set to "newTab". This argument can be globally set in the ShellRunner settings file. If unset then Sublime Text logic will determine the name of new tabs generated.

###### "cmdCombineOutputStreams": true/false

If false then capture only stdout text. If true then capture both stdout and stderr. This argument can be globally set in the ShellRunner settings file. If unset it defaults to false.

###### "textCmdTimeout": Integer 1..600

The number of seconds to wait for the *shellCommand* to complete. If the timeout is reached then the process running the *shellCommand* will be terminated and an error reported (no text will be processed). This argument can be globally set in the ShellRunner settings file. If unset it defaults to 10 seconds.

###### "textCmdStopOnErr": true/false

If true then do not output any text if there is an error code (non-zero) returned from the *shellCommand*, but rather report the error code, in a Sublime Text message window, along with the stdout and stderr text received. If **textCmdStopOnErr** is set to false however, then text processing will be implemented irrespective of the *shellCommand* return code. This argument can be globally set in the ShellRunner settings file. If unset it defaults to true.

### Additional args for 'sidebar' commands only:

###### "dirOnly": true/false

If true, enable this 'sidebar' command only when there is at least one directory selected in the side bar. Defaults to false. N.B. "dirs" arg must also be given for this argument to function correctly. If **dirOnly** is unset (or false) then no directory restrictions are placed on command enablement. This argument is optional and has no default or global settings-file fallback.

###### "files": [], "dirs": [], "paths": [] -- Side bar item selection details arguments 

If any of these three arguments is given, it must be set to an empty list. This will trigger Sublime Text to include a list of files, dirs, or paths (files or dirs) that were selected in the side bar at the time the command was activated. ShellRunner builds on this Sublime Text functionality and translates these lists into strings that can be utilised through [substitution variables](#substitution-variables-for-commands) in the *shellCommand* string. 

**"files": []**<br>
enables correct side bar information to be placed in the ${files} and ${lastFile} substitution variables.

**"dirs": []**<br>
enables correct side bar information to be placed in the ${dirs} and ${lastDir} substitution variables.

**"paths": []**<br>
enables correct side bar information to be placed in the ${paths} and ${lastPath} substitution variables. NB Paths may either be files or dirs (no discrimination).

***Note:***<br>
* The ${files}, ${dirs} and ${paths} strings are concatenated (space separated) strings of side bar items
* The ${lastFile}, ${lastDir} and ${lastPath} strings correspond to the last of that side bar item to be selected
* When no information available to fill these substitution variables they default to empty strings.
* When information is available, each file/dir/path name will be shell escaped for direct use in the shell.

### Substitution Variables for Commands

ShellRunner commands can contain substitution variables. These will be substituted for the relevant value (if available) at command run time. If a used substitution variable does not have an associated value, a zero length string will be inserted. The syntax for the substitution variables is as per sublime-snippet syntax e.g. ${folder}. Substitution variables are of three types: a) side bar substitution variables, which correspond to the files and folders selected in the sidebar (only valid for 'sidebar' commands), b) window substitution variables, which correspond to information about the active window and its open file (valid for all commands), c) miscellaneous substitution variables (valid for all commands)::

#### Sidebar Substitution Variables

Accurate information concerning the selected items in the sidebar can be made available to a ShellRunner command, as follows, if one or more of the following arguments are included in the command args: 'paths': [], 'files': [], 'dirs': []. These are [magic args](https://www.sublimetext.com/docs/menus.html) which Sublime Text fills with details of items selected.

1) Substitution variables made available to 'sidebar' commands when the "paths": [] arg is present in the command args:

* ${paths}		- a space separated list of all the files or folders selected in the sidebar
* ${lastPath}	- the most recently selected (and still selected) file or folder in the sidebar

2) Substitution variables made available to 'sidebar' commands when the "files": [] arg is present in the command args:

* ${files}		- a space separated list of all the files selected in the sidebar
* ${lastFile}	- the most recently selected (and still selected) file in the sidebar

3) Substitution variables made available to 'sidebar' commands when the "dirs": [] arg is present in the command args:

* ${dirs}		- a space separated list of all the folders selected in the sidebar
* ${lastDir}	- the most recently selected (and still selected) folder in the sidebar

#### Window Substitution Variables

The following variables substitute details of the Sublime Text project environment (if any) and the file that has the focus in the current window. Their names make them self-expanatory:

${packages}<br>
${platform}<br>
${file}<br>
${file_path}<br>
${file_name}<br>
${file_base_name}<br>
${project_extension}<br>
${file_extension}<br>
${folder}<br>
${project}<br>
${project_path}<br>
${project_name}<br>
${project_base_name}<br>

#### Miscellaneous Substitution Variables

##### ${selText}

A string corresponding to the selected text in the active document. If multiple regions are selected the corresponding selections will be concatenated with "**multiSelSeparator**" as the separating string. "**multiSelSeparator**" defaults to a single space if not set.

##### ${shellCommand}

A copy of the *shellCommand*, as a string, before any substitution variables have been replaced. This string is presented to the shell in a $'literal-string' format.

##### User Defined Substitution Variables

In addition to the above standard substitution variables a user can define an "**extraCmdSubstVars**" dictionary containing custom substitution variables. A global dictionary of substitution variables can also be defined in the [settings file](#shellrunner-settings-file). This goes by the name of "**extraGlobalSubstVars**". Substitutions defined at this global level will be available for all commands.

##### Shell Environment Variables as Substitution Variables

###### Inherited Shell Env variables
The generated *shellCommand* environment will inherit, by default, the shell environment variables exported by the parent shell (the same shell in which your Sublime Text instance was started). If this is the case, which will be so unless *cleanShellEnv* has been set to true, then these inherited shell environment variables, e.g. ${HOME}, can be used as substitution variables in the generation of the *shellCommand*. If the opposite applies, i.e. *cleanShellEnv* is set to true, then none of the parent shell environment variables will be usable for command substitution purposes.

###### User defined Shell Env variables
The custom ShellRunner (user generated) environment variables, which will always be exported to the *shellCommand* shell, will always be available to use as command substitution variables. These custom ShellRunner environment variables are those defined in either the *extraCmdShellEnvVars* or *extraGlobalShellEnvVars* dictionaries (command args based and settings file based respectively).

Note: There will be cases when you do not want ShellRunner to expand an environment substitution variable at command build time, but leave it for the shell itself to expand at command run time. In such cases you can preceed (escape) the substitution variable with a double backslash. For example, the *shellCommand* "/usr/bin/bash -c 'echo ${PWD}; cd /; echo \\${PWD}'" will print different (and accurate) directory names, yet if the double backlash were omitted then the same directory name would be printed twice (which would be inaccurate). The various command example files show a number of cases of delayed environment variable expansion.

## Selective command enablement

All 'sidebar' and 'window' commands can be enabled for certain file types, and disabled for all others, by including an appropriately defined *targetExtns* setting in the command's arguments. Additionally the 'sidebar' commands can utilise the "dirOnly" argument so as to be enabled only when one or more directories are selected in the side bar.

Information on how to implement selective command enablement with *targetExtns* and *dirOnly* is given above, but what might not be clear is how command enablement manifests in different situations. Here we clarify this:

When a currently disabled command is viewed in a menu (Side Bar or Context), it will be greyed out and un-triggerable. When the command is enabled it will be displayed as an ordinary menu entry and be triggerable.

When a currently disabled 'window' command is triggered by a key binding, it simply will not run. If it is enabled, it will run normally. Note: All ShellRunner commands that are tied to a key binding should be one of the 'window' commands (window_shellrunner_text_command, window_shellrunner_spawn_command).

## The Open Terminal Here Command

Aside from the shell command running capabilities detailed above, the ShellRunner plugin has an "Open Terminal Here" menu entry which can be set to appear in the sidebar menu and/or the context menu. When activated from the sidebar menu the working directory of the terminal will be set to that of the last sidebar selected item (be it a file or folder). When activated from the context menu the terminal will start in the directory of the currently active window file.

To determine which terminal emulator will open, the *openTerminalCmd* needs to be set. To determine whether the `Open Terminal Here` command is visible in each of the menus, two (boolean) settings are available: *showSidebarTerminalCmd*, *showContextTerminalCmd*. All three of these settings can be found in the [global settings file](#shellrunner-settings-file).

## ShellRunner Settings File

Global ShellRunner settings are configurable in a dual panel edit window which can be opened via:

* Command Palette: Preferences: Shell Runner Settings
* Main Menu: `Preferences` -> `Package Settings` -> `Shell Runner` -> `Settings`

The user settings file (*${packages}/User/ShellRunner.sublime-settings*) will appear in the right hand panel. Settings can be copied over to here from the standard (default) plugin settings file, which will appear on the left, and then edited/saved to suit user preferences.

##### .sublime-project file overrides for ShellRunner settings

Additionally, if you're working in a Sublime Text project, ShellRunner settings can be defined in a named section of the .sublime-project file. Thes project settings can be opened from the `Project` -> `Edit Project` menu. 

	{
		"folders":
		[
			{
				"path": "/home/me/myprojects/thisproject"
			}
		],
		"ShellRunner": {
			 "outputTabName": "ShellRunner_projdef.txt"
		},
	}

The following ShellRunner options can be configured in any of the above settings files:

Note: Unless otherwise stated, the options below do not have an equivalent in the [command arguments](#arguments-provided-to-shellrunner-commands).

###### "openTerminalCmd": ""

The terminal emulator program which ShellRunner will call. Set this to your preferred emulator that is on your system e.g. "/usr/bin/urxvt", or leave as an empty string (the default) and ShellRunner will attempt to 'best guess' your terminal emulator.


###### "showSidebarTerminalCmd": true / false,  "showContextTerminalCmd": true / false

These two settings can be used to show (true) or hide (false) the *Open Terminal Here* command in the menus. The default (installation) settings are to show the command in the Side Bar but to hide it in the Context Menu.

###### "showSidebarEditMenu": true / false, "showContextEditMenu": true / false

These two settings can be used to show (true) or hide (false) the *ShellRunner Commands* entry in the menus. The default (installation) settings are to show the command in the Side Bar but to hide it in the Context Menu. Unless you are a puritan key bindings type of person, you will probably want the *ShellRunner Commands* entry to appear in at least one of these menus, as it is a quick visual way of running and editing your shell commands.

###### "initChangeDir": true

Change directory (cd) to the target file/folder directory before running a shell command. If left unset, this defaults to 'true', which is usually useful. This global setting can be overriden on an individual *shellCommand* basis, through a same named variable in the [command arguments](#arguments-provided-to-shellrunner-commands) settings.

###### "outputTo": "string" or [ "string", ... ]

One or several string values (in a list) to determine the destination(s) to which *shellCommand* output text will be sent. Acceptable "outputTo" destinations are: "newTab", "sublConsole", "msgBox", "cursorInsert", "clip" (the clipboard), and null (output is discarded). This global setting can be overriden on an individual *shellCommand* basis, through a same named variable in the [command arguments](#arguments-provided-to-shellrunner-commands) settings.

###### "outputTabName": ""

The default new tab name when 'outputTo' is set to 'newTab'. If this is not defined, new ShellRunner tabs will be untitled (whereby they'll be given a title according to Sublime Text's own logic). This global setting can be overriden on an individual *shellCommand* basis, through a same named variable in the [command arguments](#arguments-provided-to-shellrunner-commands) settings.

###### "cmdCombineOutputStreams": false

If you want to capture both stdErr and stdOut, set **cmdCombineOutputStreams** to true. The default value is false, which only captures stdOut. This global setting can be overriden on an individual *shellCommand* basis, through a same named variable in the [command arguments](#arguments-provided-to-shellrunner-commands) settings.

###### "textCmdTimeout": 10,

The length of time (in seconds) before a shell text command will timeout if not completed. If left unset, it defaults to 10 seconds. Can be set within a range of 1..600 seconds. This global setting can be overriden on an individual *shellCommand* basis, through a same named variable in the [command arguments](#arguments-provided-to-shellrunner-commands) settings.

###### "textCmdStopOnErr": true,

To continue processing text when a shell command returns an error code, set this to false. If left unset, the setting defaults to true. This means that text processing will not be carried out when the *shellCommand* errors, and an information pop-up box will appear with details of the error. This global setting can be overriden on an individual *shellCommand* basis, through a same named variable in the [command arguments](#arguments-provided-to-shellrunner-commands) settings.

###### "multiSelSeparator": " "

When conjoined multiple selections are used in a *shellCommand*, e.g. via the ${selText} substitution variable, they are concatenated into one string using **multiSelSeparator** as the junction string. When left unset, **multiSelSeparator** defaults to being a single space. This global setting can be overriden on an individual *shellCommand* basis, through a same named variable in the [command arguments](#arguments-provided-to-shellrunner-commands) settings.

###### "selAsLiteralStr": false
When selected text is used in a *shellCommand*, e.g. via the ${selText} substitution variable, you may want to represent this text as a literal string variable i.e. $'...' notation. This can avoid hassles with quotation marks and escape characters, and help you represent your selected text verbatim in your commands. This global setting can be overriden on an individual *shellCommand* basis, through a same named variable in the [command arguments](#arguments-provided-to-shellrunner-commands) settings.

###### "cleanShellEnv": false

Ordinarily the *shellCommand* shell inherits the environment variables of its parent, and this is ShellRunner's default behaviour when **cleanShellEnv** is left unset or is set to false. To run a *shellCommand* with a clean environment, i.e. no parental environment variables get inherited, you should set **cleanShellEnv** to true. This global setting can be overriden on an individual *shellCommand* basis, through a same named variable in the [command arguments](#arguments-provided-to-shellrunner-commands) settings.

###### "extraGlobalShellEnvVars": {dict}

In this dictionary you can set extra, user defined environment variables that will be exported to the *shellCommand* shell. For example:
	
	"extraGlobalShellEnvVars": {"HOME": "/home/override", "CAPPUCINO": "splendid"}

These variables are exported to a *shellCommand* shell irrespective of the value of *cleanShellEnv*. The settings in this dictionary can be added to (not overriden!) on an individual *shellCommand* basis, through a dictionary named *extraCmdShellEnvVars* in the [command arguments](#arguments-provided-to-shellrunner-commands) settings.

###### "extraGlobalSubstVars"

In this dictionary you can set extra, user defined [substitution variables](#substitution-variables-for-commands) that can be used in building a *shellCommand*. For example:

	"extraGlobalSubstVars": 	{ 	"drink"	:	"tea", "dunk"	:	"biscuits" } 

The settings in this dictionary can be added to (not overriden!) on an individual *shellCommand* basis, through a dictionary named *extraCmdSubstVars* in the [command arguments](#arguments-provided-to-shellrunner-commands) settings.

## Uninstalling ShellRunner

ShellRunner should be uninstalled using Package Control:

* `Ctrl+Shift+P` or `Cmd+Shift+P`
* type `remove`, select `Package Control: Remove Package`
* select the ShellRunner package

If the ShellRunner user settings directory still exists following the uninstall (${packages}/User/ShellRunner) it can be safely removed manually.