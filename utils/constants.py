from .saltydog import testMap

# pluginName should ideally match the top level directory name for the plugin
pluginEnv = {
    "pluginName":       "ShellRunner",
    "pluginMainReloadModule": "ShellRunner.main",
    "docsWeb":          "",
    "docsSublime":      "",
    "doDebug":          True
}
pluginSettingsKey = {
    "initChangeDir": {"default": True, "checks": ["is_bool"]},
    "sideBarMenuOn": {"default": True, "checks": ["is_bool"]},
    "contextMenuOn": {"default": True, "checks": ["is_bool"]},
    "outputTo": {"default": [""], "checks": ["is_list_of_strings"]},
    "outputTabName": {"default": "", "checks": ["is_str"]},
    "cmdCombineOutputStreams": {"default": False, "checks": ["is_bool"]},
    "cmdTimeout": {"default": 10, "checks": []},
    "textCmdStopOnErr": {"default": True, "checks": ["is_bool"]},
    "multiSelSeparator": {"default": " ", "checks": ["is_str"]},
    "selAsLiteralStr": {"default": False, "checks": ["is_bool"]},
    "cleanShellEnv": {"default": False, "checks": ["is_bool"]},
    "extraGlobalShellEnvVars": {"default": {}, "checks": []},
    "extraGlobalSubstVars": {"default": {}, "checks": []}, 
}

pluginSettingsGovernor = {
    "ID": {
        "outputDictDesc": f"{pluginEnv['pluginName']} Plugin Settings"
    },
    "Settings": {
        "initChangeDir": {"default": True, "checks": ["is_bool"]},
        "sideBarMenuOn": {"default": True, "checks": ["is_bool"]},
        "contextMenuOn": {"default": True, "checks": ["is_bool"]},
        "outputTo": {"default": [""], "checks": ["is_list_of_strings"]},
        "outputTabName": {"default": "", "checks": ["is_str"]},
        "cmdCombineOutputStreams": {"default": False, "checks": ["is_bool"]},
        "cmdTimeout": {"default": 10, "checks": []},
        "textCmdStopOnErr": {"default": True, "checks": ["is_bool"]},
        "multiSelSeparator": {"default": " ", "checks": ["is_str"]},
        "selAsLiteralStr": {"default": False, "checks": ["is_bool"]},
        "cleanShellEnv": {"default": False, "checks": ["is_bool"]},
        "extraGlobalShellEnvVars": {"default": {}, "checks": []},
        "extraGlobalSubstVars": {"default": {}, "checks": []} 
    }
}

settingsGovernorDict = { "ShellRunner Settings": {
    "initChangeDir": {"default": True, "checks": ["is_bool"]},
    "sideBarMenuOn": {"default": True, "checks": ["is_bool"]},
    "contextMenuOn": {"default": True, "checks": ["is_bool"]},
    "outputTo": {"default": [""], "checks": ["is_list_of_strings"]},
    "outputTabName": {"default": "", "checks": ["is_str"]},
    "cmdCombineOutputStreams": {"default": False, "checks": ["is_bool"]},
    "cmdTimeout": {"default": 10, "checks": []},
    "textCmdStopOnErr": {"default": True, "checks": ["is_bool"]},
    "multiSelSeparator": {"default": " ", "checks": ["is_str"]},
    "selAsLiteralStr": {"default": False, "checks": ["is_bool"]},
    "cleanShellEnv": {"default": False, "checks": ["is_bool"]},
    "extraGlobalShellEnvVars": {"default": {}, "checks": []},
    "extraGlobalSubstVars": {"default": {}, "checks": []}, 
}}

# outputToPythonValues = ['newTab', 'sublConsole', 'cursorInsert', 'msgBox', 'clip', None]
# outputToJsonValues = [ value if value is not None else 'null' for value in outputToPythonValues ]
# outputToJsonKeyStr = str(outputToJsonValues)
outputDests = ['newTab', 'sublConsole', 'cursorInsert', 'msgBox', 'clip']

shellCommandArgs = {
    "shellCommand": {"m": True, "checks": ["loc_is_string_or_list_of_oom_strings"]},
    "targetExtns": {"default": [], "checks": ["is_list_of_strings"]},
    "initChangeDir": {"default": True, "checks": ["is_bool"]},
    "multiSelSeparator": {"default": " ", "checks": ["is_string"]},
    "selAsLiteralStr": {"default": False, "checks": ["is_bool"]},
    # "consoleDebug": {"default": False, "checks": ["is_bool"]},
    # "tabDebugReport": {"default": False, "checks": ["is_bool"]},
    "consoleDebug": {"default": False, "checks": ["is_bool"]},
    "tabDebugReport": {"default": False, "checks": ["is_bool"]},
    "extraCmdSubstVars": {"default": {}, "checks": ["is_dict_of_zom_strings"]},
    "cleanShellEnv": {"default": True, "checks": ["is_bool"]},
    "extraCmdShellEnvVars": {"default": {}, "checks": ["is_dict_of_zom_strings"]},
    # Additional args for 'text' capturing commands only:
    "outputTo": {"checks": ["loc_is_list_of_outputs"]},
    "outputTabName": {"default": None, "checks": ["is_str"]},
    "cmdCombineOutputStreams": {"default": False, "checks": ["is_bool"]},
    "cmdTimeout": {"default": 10, "checks": ["loc_is_timeout_int"]},
    "textCmdStopOnErr": {"default": True, "checks": ["is_bool"]},
    # Additional args for 'sidebar' commands only:
    "dirOnly": {"checks": ["is_bool"]},
    # dirs/files/paths are written as empty lists in the command, where reqd
    # sublime auto-fills these with the dirs/files/paths of all selected sidebar objects 
    "dirs": {"checks": ["is_list"]},
    "files": {"checks": ["is_list"]},
    "paths": {"checks": ["is_list"]},
}

commandArgsOnly = [ k for k in shellCommandArgs.keys() if k not in pluginSettingsKey]

menuFileDefaultString = """[{"id": "shell_runner_context_commands_parent",  "children": [
    { "caption" : "-", "id": "shell_runner_context_commands_below_here"},
    // Insert custom context menu commands here.
    // See -> Command Palette: ShellRunner README for shellCommand syntax details
    // For example:
    {
        "caption":  "ShellRunner Context Menu Command Demo",
        "command":  "window_shellrunner_text_command",
        "args": {   "shellCommand": ["/usr/bin/bash -c 'echo Hello $\{platform\} Sublime Text user.; ",
                                        "printf \"Welcome to some ShellRunner plugin functionality.\\n\\n\\";",
                                        "printf \"You should now comment out this demo command \";",
                                        "printf \"and set about configuring ShellRunner to meet your needs (\";",
                                        "printf \"configuration instructions can be found in the ShellRunner README \";",
                                        "printf \", which is available via the Sublime Text command palette).\";",
                                        "'"],
                    "outputTo": "msgBox", 
                }
    },
    ]}]
"""

class is_timeout_int():
    def __init__(self, timeOut):
        self.timeOut = timeOut
    def failStr(self):
        return 'Must be an integer, in range 1..10'
    def testPasses(self):
        return isinstance(self.timeOut, int) and self.timeOut in range(1,11)

class is_list_of_outputs():
    def __init__(self, outputList):
        self.outputList = outputList
    def failStr(self):
        return 'Must be a list of one or more valid outputs'
    def testPasses(self):
        print(f'is list = {isinstance(self.outputList, list)}')
        print(f'has valid contents = {all(elem in outputDests for elem in self.outputList)}')
        return isinstance(self.outputList, list) and all(elem in outputDests for elem in self.outputList)

class is_string_or_list_of_oom_strings():
    def __init__(self, givenCmd):
        self.givenCmd = givenCmd
    def failStr(self):
        return 'Must be a non-zero length string or list thereof'
    def testPasses(self):
        if isinstance(self.givenCmd, str):
            return bool(self.givenCmd)
        elif isinstance(self.givenCmd, list):
            return all(isinstance(elem, str) and bool(elem) for elem in self.givenCmd)
        else:
            return False



locTestMap = {
    "loc_is_timeout_int":                   is_timeout_int,
    "loc_is_list_of_outputs":               is_list_of_outputs,
    "loc_is_string_or_list_of_oom_strings": is_string_or_list_of_oom_strings
}

def honeRunArgs(rawArgs):
    def formatErrStr(namedArg, faultWith):
        return f'{namedArg.ljust(24)} :: {faultWith}\n'
    honedArgs = {}
    errorRep = ""
    for argName, argDetails in shellCommandArgs.items():
        print(f'checking {argName}')
        if argName not in rawArgs:
            if argDetails.get('m'):
                errorRep += formatErrStr(argName, 'Argument must be provided')
            if 'default' in argDetails:
                honedArgs[argName] = argDetails['default']
            continue
        for thisCheckStr in argDetails.get('checks', []):
            if thisCheckStr.startswith('loc'):
                print(f'\n\n\nthis test str = {thisCheckStr}\n\n\n')
                checkObj = locTestMap[thisCheckStr](rawArgs[argName])
            else:
                checkObj = testMap[thisCheckStr](rawArgs[argName])
            if not checkObj.testPasses():
                errorRep += formatErrStr(argName, checkObj.failStr())
        honedArgs[argName] = rawArgs[argName]

    return honedArgs, errorRep


