import sublime
import sublime_plugin
import subprocess
import os
from inspect import getframeinfo, stack

SDframeworkName = 'SaltyDog'

# ===================================================================================
# ======================== Settings Test Classes ====================================
                           #####################

class is_bool():
    def __init__(self, boolToCheck):
        self.boolToCheck = boolToCheck

    def failStr(self):
        return 'Must be type: boolean'

    def testPasses(self):
        return isinstance(self.boolToCheck, bool)

class is_str():
    def __init__(self, strToCheck):
        self.strToCheck = strToCheck

    def failStr(self):
        return 'Must be type: str'

    def testPasses(self):
        return isinstance(self.strToCheck, str)

class is_str_or_list():
    def __init__(self, itemToCheck):
        self.itemToCheck = itemToCheck

    def failStr(self):
        return 'Must be type: str or list'

    def testPasses(self):
        return isinstance(self.itemToCheck, (str, list))

class is_dict():
    def __init__(self, dct, mustHaveItems=False, itemType=None):
        self.dct = dct
        self.itemType = itemType
        self.checkItems = itemType is not None
        self.isComplex = mustHaveItems or self.checkItems
        self.mustHaveItems = mustHaveItems
        itemTypeStr = ['elements', str(itemType)][self.checkItems]
        # self.checkItems = checkItems
        self.failMsgSimple = 'Must be a dictionary'
        self.failMsgComplex = f"Must be a dictionary of {['zero', 'one'][mustHaveItems]} or more {itemTypeStr}"
    def failStr(self):
        return [self.failMsgSimple, self.failMsgComplex][self.isComplex]
    def testPasses(self):
        if not isinstance(self.dct, dict):
            return False
        if self.isComplex:
            contentsOK = all(isinstance(elem, self.itemType) for key, elem in self.dct.items()) if self.checkItems else True
            if self.mustHaveItems:
                return bool(self.dct) and contentsOK
            else:
                return contentsOK
        return True

class is_list():
    def __init__(self, lst, mustHaveItems=False, itemType=None):
        self.lst = lst
        self.itemType = itemType
        self.checkItems = itemType is not None
        self.isComplex = mustHaveItems or self.checkItems
        self.mustHaveItems = mustHaveItems
        itemTypeStr = ['elements', str(itemType)][self.checkItems]
        self.failMsgSimple = 'Must be a list'
        self.failMsgComplex = f"Must be a list of {['zero', 'one'][mustHaveItems]} or more {itemTypeStr}"
    def failStr(self):
        return [self.failMsgSimple, self.failMsgComplex][self.isComplex]
    def testPasses(self):
        if not isinstance(self.lst, list):
            return False
        if self.isComplex:
            contentsOK = all(isinstance(elem, self.itemType) for elem in self.lst) if self.checkItems else True
            if self.mustHaveItems:
                return bool(self.lst) and contentsOK
            else:
                return contentsOK
        return True

class _is_empty_obj():
    def __init__(self, testObj, itemType):
        self.testObj = testObj
        self.itemType = itemType
    def failStr(self):
        return f'Must be an empty {self.itemType}'
    def testPasses(self):
        return isinstance(self.testObj, self.itemType) and not bool(self.testObj)

class is_empty_str(_is_empty_obj):
    def __init__(self, str_):
        super().__init__(str_, str)

class is_empty_dict(_is_empty_obj):
    def __init__(self, dict_):
        super().__init__(dict_, dict)

class is_empty_list(_is_empty_obj):
    def __init__(self, list_):
        super().__init__(list_, list)

class is_list_of_oom_strings(is_list):
    def __init__(self, lst):
        super().__init__(lst, mustHaveItems=True, itemType=str)

class is_list_of_zom_strings(is_list):
    def __init__(self, lst):
        super().__init__(lst, itemType=str)

class is_dict_of_zom_strings(is_dict):
    def __init__(self, dct):
        super().__init__(dct, itemType=str)

class is_dict_of_oom_strings(is_dict):
    def __init__(self, dct):
        super().__init__(dct, mustHaveItems=True, itemType=str)


testMap = {
    "is_bool":                  is_bool,
    "is_str":                   is_str,
    "is_str_or_list":           is_str_or_list,
    "is_empty_str":             is_empty_str,
    "is_dict":                  is_dict,
    "is_empty_dict":            is_empty_dict,
    "is_list":                  is_list,
    "is_empty_list":            is_empty_list,
    "is_list_of_oom_strings":   is_list_of_oom_strings,
    "is_list_of_zom_strings":   is_list_of_zom_strings,
    "is_dict_of_oom_strings":   is_dict_of_oom_strings,
    "is_dict_of_zom_strings":   is_dict_of_zom_strings
}

# ===================================================================================
# ======================== Messaging Utils ==========================================
                           ###############

class MessageOutputUtilsClassAddin():

    def msgBoxTitleAndCallerClass(self, stackPassed):

        # if hasattr(self, 'pluginName'):
        #     foundPluginName = self.pluginName
        # else:
        #     caller = getframeinfo(stack()[2][0])
        #     print(f'{SDframeworkName} config error: self.pluginName unset [in {caller.filename}::{caller.lineno}??]')
        #     foundPluginName = '!!pluginName-not-set!!'
        # titleStr = f'{__package__} (Plugin)'
        titleStr = f'{self.pluginName} (Plugin)'
        # if oneLine:
        #     errorLabel = ["", " error"][msgIsError]
        #     pluspart = ['', f'[{fromCommand}{errorLabel}]'][fromCommand is not None]
        # else:
        #     errorLabel = ["", "Error "][msgIsError]
        #     pluspart = ['', f'\n[{errorLabel}message from {fromCommand}]'][fromCommand is not None]
        stackVars = stackPassed[1][0].f_locals
        if "self" in stackVars:
            rawClassName = stackVars["self"].__class__.__name__
            classStr = f'\n\n[from {rawClassName} code]'
        else:
            rawClassName = ""
            classStr = ""
        return titleStr, classStr, rawClassName

    def msgBox(self, msg):
        # stack = inspect.stack()
        # the_class = stack()[1][0].f_locals["self"].__class__.__name__
        # print(f'msgBox called by class: {the_class}')
        msgBoxTitle, callerClass, rawClass = self.msgBoxTitleAndCallerClass(stack()) 
        # if fromCommand is None: fromCommand = self.name()
        sublime.message_dialog(f'{msgBoxTitle}\n\n{msg}{callerClass}')

    def ok_cancel_dialog(self, msg):
        # if fromCommand is None: fromCommand = self.name()
        msgBoxTitle, callerClass, rawClass = self.msgBoxTitleAndCallerClass(stack()) 
        return sublime.ok_cancel_dialog(f'{msgBoxTitle}\n\n{msg}{callerClass}')

    def status_message(self, msg):
        msgBoxTitle, callerClass, rawClass = self.msgBoxTitleAndCallerClass(stack()) 
        # if fromCommand is None: fromCommand = self.name()
        classInfo = [f'[{rawClass}]', ''][rawClass == '']
        sublime.status_message(f'{msgBoxTitle}{classInfo}: {msg}')
        # status_message(msg, self.name())

    def error_message(self, msg):
        msgBoxTitle, callerClass, rawClass = self.msgBoxTitleAndCallerClass(stack()) 
        # if fromCommand is None: fromCommand = self.name()
        sublime.error_message(f'{msgBoxTitle} Error Message:\n\n{msg}{callerClass}')
        # error_message(msg, self.name())

    def console_message(self, msg):
        msgBoxTitle, callerClass, rawClass = self.msgBoxTitleAndCallerClass(stack()) 
        classInfo = [f'[{rawClass}]', ''][rawClass == '']
        # if fromCommand is None: fromCommand = self.name()
        print(f'{msgBoxTitle}{classInfo}: {msg}')
        # console_message(msg, self.name())

    def xcept_message(self, msg, xceptObj):
        # msgBoxTitle, callerClass, rawClass = self.msgBoxTitleAndCallerClass(stack()) 
        # if fromCommand is None: fromCommand = self.name()
        caller = getframeinfo(stack()[1][0])
        msgStr = (f'{self.pluginName} Plugin:\n{msg}\n\nException: {xceptObj.__class__.__name__}::\n\n{str(xceptObj)}\n\n'
                 f'[{caller.filename}::{caller.lineno}]')
        sublime.error_message(msgStr)
        # xcept_message(msg, xceptObj, self.name())

    def dBug(self, msg):
        # if fromCommand is None: fromCommand = self.name()
        if self.pluginEnv.get('doDebug'):
            caller = getframeinfo(stack()[1][0])
            print(f'{self.pluginName}:DEBUG: {msg} [{caller.filename}::{caller.lineno}]')

# governorDictSettingsKey = {
#     "default"     : "default setting - omit and setting will be user defined only",
#     "mand"        : "True = setting must be defined (defaults to default anyhow, if not present)",
#     "baseDOnly"   : "True = base dict only, erroneous in user dict",
#     "mergeDOnly"  : "True = user dict only, erroneous in base dict",
#     "baseOvr"     : "True if this baseDict setting has priority over the equiv mergeDict setting (contrary to default behaviour)",
#     "merge"       : "Set True for user/base settings to be merged (for lists or dicts)",
#     "checks"      : "list of check names (as strings) to validate the setting e.g. is_bool",
# }

def testViewForScopes(view, checkTheseScopes=[]):
    """
    Returns True only if a scope in the checkTheseScopes list can be found in the full scope string at the view's cursorpos
    A utility function designed for use with the is_visible() and/or is_enabled() methods in text and window commands
    """
    cursor = view.sel()[0].begin()
    curr_scope = view.scope_name(cursor)
    # print(f'checking if current scope: [{curr_scope}] contains any of these target scopes: {checkTheseScopes}')
    scopeHit = False
    for targetScope in checkTheseScopes:
        if sublime.score_selector(curr_scope, targetScope) > 0:
            # print(f'have scope hit score of {sublime.score_selector(curr_scope, targetScope)}')
            scopeHit = True
            break
    return scopeHit

governorDictSchema = {
    "ID": {
    "outputDictDesc"    : str, # "Description of the output dictionary",
    "_baseOvr"          : bool # "set to True if all baseDict values always override mergeDict values (contrary to default behaviour)"
    },
    "Settings": {
    "__multiVarNames": {
        "_default"     : "various types",  # "default setting - omit and setting will be user defined only",
        "_mand"        : bool, # "True = setting must be defined (defaults to default anyhow, if not present)",
        "_baseDOnly"   : bool, # "True = base dict only, erroneous in user dict",
        "_mergeDOnly"  : bool, # "True = user dict only, erroneous in base dict",
        "_baseOvr"     : bool, # "True if this baseDict setting has priority over the equiv mergeDict setting (contrary to default behaviour)",
        "_merge"       : bool, # "Set True for user/base settings to be merged (for lists or dicts)",
        "_checks"      : list, # "list of check names (as strings) to validate the setting e.g. is_bool",
        }
    }
}


class dictGovernor(MessageOutputUtilsClassAddin):
    """
    Merges and parses one or two dictionaries (baseDict and the optional mergeDict)
    according to rules and checks supplied in a governing dict (govDict)
    """

    className = "Dictionary Governor"
    def __init__(self, govDict, baseDict, mergeDict=None):
        try:
            self.IDDict = govDict["ID"]
            self.outputDictName = self.IDDict["outputDictDesc"]
            self.govDict = govDict["Settings"]
            self.globalBaseOverride = self.IDDict.get("baseOvr", False)
            self.fatalInitErr = False
            self.fatalInitErrStr = ""
        except Exception as exerr:
            self.fatalInitErr = True
            self.fatalInitErrStr = f'Exception parsing governor dict:\n{govDict}\n\n{exerr.__class__.__name__}::\n\n{str(exerr)}'
        self.fatalParseErr = False
        self.fatalParseErrStr = ""
        self.baseDictErrors = []
        self.mergeDictErrors = []
        self.jointDictErrors = []
        self.baseDict = baseDict
        self.mergeDict = mergeDict

    def name(self):
        return dictGovernor.className

    def resetBaseDict(self, baseDict=None):
        if isinstance(baseDict, dict):
            self.baseDict = baseDict

    def resetMergeDict(self, mergeDict=None):
        if isinstance(mergeDict, dict):
            self.mergeDict = mergeDict

    def getFullDict(self):
        return self._makeOutputDict()

    def hasErrors(self):
        return bool(self.baseDictErrors or self.mergeDictErrors or self.jointDictErrors)

    def getErrors(self):
        return (self.baseDictErrors, self.mergeDictErrors, self.jointDictErrors)

    def _makeOutputDict(self):
        """
        Always return a dictionary - even an empty one if there are errors and nothing valid can be output
        """
        fatalParseErrFlag = False
        fatalParseErrInfo = ""
        self.baseDictErrors = []
        self.mergeDictErrors = []
        self.jointDictErrors = []
        _opd = {} # output dictionary

        # Step 1: baseDict processing
        # `- Parse the baseDict into the outputDictionary, according to govDict rules
        for k, v in self.govDict.items():
            if k in self.baseDict:
                if self.govDict[k].get('mergeDOnly', False):
                    self.baseDictErrors.append((k, "not a valid setting here"))
                    continue
                testPassed = True
                for thisCheckStr in self.govDict[k].get('checks', []):
                    checkObj = testMap[thisCheckStr](self.baseDict[k])
                    testPassed = checkObj.testPasses()
                    if not testPassed:
                        self.baseDictErrors.append((k, checkObj.failStr()))
                        break
                if testPassed:
                    _opd[k] = self.baseDict[k]

        # Step 2: mergeDict processing
        # `- Parse the mergeDict (if set) into the outputDictionary, according to govDict rules
        if isinstance(self.mergeDict, dict):
            for k, v in self.govDict.items():
                if k in self.mergeDict:
                    if self.govDict[k].get('baseDOnly', False):
                        self.mergeDictErrors.append((k, "not a valid setting here"))
                        continue
                    testPassedFlag = True
                    for thisCheckStr in self.govDict[k].get('checks', []):
                        checkObj = testMap[thisCheckStr](self.mergeDict[k])
                        testPassedFlag = checkObj.testPasses()
                        if not testPassedFlag:
                            self.mergeDictErrors.append((k, checkObj.failStr()))
                            # report first error of a setting only (ignore any further tests)
                            break
                    if testPassedFlag:
                        # Note: nothing further is done in this stage if all tests did not pass
                        if not self.govDict[k].get('merge', False):
                            # no complicated merge reqd., just a straightforward setting
                            if self.govDict[k].get('baseOvr', self.globalBaseOverride):
                                # baseDict value takes priority if present
                                _opd.setdefault(k, self.mergeDict[k])
                            else:
                                # mergeDict value takes priority
                                _opd[k] = self.mergeDict[k]
                        else:
                            mergeDoneFlag = False
                            if not isinstance(_opd.get(k), (list, dict)):
                                self.baseDictErrors.append((k, f'cannot merge a {type(_opd.get(k).__name__)} type variable'))
                            else:
                                # we can only merge two lists, or two dicts
                                expectedMutualMergeType = type(_opd.get(k))
                                if not type(self.mergeDict[k]) == expectedMutualMergeType:
                                    self.jointDictErrors.append((k, (f'cannot merge a {type(_opd.get(k).__name__)} '
                                                                     f'variable with a {type(self.mergeDict.get(k).__name__)}')))
                                else:
                                    if expectedMutualMergeType == list: # have two lists, merge avoiding duplicates
                                        _opd[k] = list(set(_opd[k] + self.mergeDict[k]))
                                    else: # have two dictionaries, priorities come into play when merging
                                        if self.govDict[k].get('baseOvr', self.globalBaseOverride):
                                            # baseDict entries take priority
                                            _opd[k] = dict(self.mergeDict[k], **_opd[k])
                                        else:
                                            # mergeDict entries take priority
                                            _opd[k] = dict(_opd[k], **self.mergeDict[k])
                                    mergeDoneFlag = True
                            if not mergeDoneFlag:
                                # as merge was requested but not possible, clear any value present for this setting
                                # `- this ensures a default value (if present) will be inserted in Step 3:
                                _opd.pop(k, None)


        # Step 3: combined Dict processing
        # We now have a dictionary that's been made by combining the baseDict with the mergeDict (if the latter is set)
        # `- according to the rules and checks given in the governing dict (self.govDict)
        # This 'joint' dictionary we now parse to:
        #   a) check if any mandatory settings are missing (generates an error)
        #   b) set any defaults for missing values
        for k, v in self.govDict.items():
            if k not in _opd:
                if "mand" in  v:
                    if not fatalParseErrFlag:
                        fatalParseErrFlag = True
                        fatalParseErrInfo = f'Mandatory setting [{k}] has not been (correctly?) set.'
                    self.jointDictErrors.append((k, "mandatory setting must be correctly defined"))
                if "default" in v:
                    _opd[k] = v["default"]

        self.fatalParseErr = fatalParseErrFlag
        self.fatalParseErrStr = fatalParseErrInfo
        # Finally return the fully constructed output dictionary
        return _opd

    # the following staticmethods are utility functions designed to help external routines
    # generate error reports from dictGovernor object error tuples
    @staticmethod
    def errorCounts(triTupleOfListsOfErrors):
        errorsTotal = 0
        singleErrorCountsX3 = []
        # print(f'tri tuple list: {triTupleOfListsOfErrors}')
        for i in [0,1,2]:
            singleErrorCountsX3.append(len(triTupleOfListsOfErrors[i]))
            errorsTotal += len(triTupleOfListsOfErrors[i])
            # print(f'totalerrs={errorsTotal}----list={singleErrorCountsX3}')
        return (errorsTotal, tuple(singleErrorCountsX3))

    @staticmethod
    def getErrorReport(trisomyErrTuples, titleStrOrTupleOf3):
        """
        Build error report from the dictGovernor format of error output
        - trisomyErrTuples e.g. = ([('varname','errStr'),('v','e')...],[('v','e'),('v','e')...],[('v','e'),('v','e')...])
        - of the 3 lists of tuple errors: [0]=baseDict errs, [1]=mergeDict errs, [2]=joint errs
        The second input 'titleStrOrTupleOf3' contains a single str (one title) or tuple of 3 strings (3 titles):
        - 1 string: implies we want a report for a single input governed dictionary (base dict only)
        - 3 string: implies we want a report for a dual input governed dictionary (combining base and merge dicts)
        """
        # print(f'trisomy tuples: {trisomyErrTuples}')
        def oneErrRep(listOfErrTuples, errGroupTitle):
            def paddedVarErr(varStr, errStr):
                # paddedNamedArg = (varStr[:23] + '..') if len(varStr) > 25 else varStr.rjust(25)
                return f'>> {varStr} >> {errStr}'
            joinStr = "\n  "
            singleGroupErrList = [paddedVarErr('SETTING NAME', 'ERROR')]
            # print(f'errtuple = {errTuple}')
            for couplet in listOfErrTuples:
                singleGroupErrList.append(paddedVarErr(couplet[0], couplet[1]))
            return f'{errGroupTitle}{joinStr}{joinStr.join(singleGroupErrList)}\n\n'
        if type(titleStrOrTupleOf3) is str:
            # A report for a single input governed dictionary is implied
            # `- under such circumstances we can combine the base errors with the 'joint' errors
            #  - and report them all as base errors (no mergeDict = no mergeDict errors)
            combinedErrors = trisomyErrTuples[0] + trisomyErrTuples[2]
            if combinedErrors:
                return oneErrRep(combinedErrors, titleStrOrTupleOf3)
        else:
            # A report for a dual input governed dictionary is implied
            # `- under these circumstances we can report the 3 groups of errors (base, merge and joint)
            #  - under three headings supplied in 'titleStrOrTupleOf3'
            threeReports = ""
            for i in [0,1,2]:
                if trisomyErrTuples[i]:
                    threeReports += oneErrRep(trisomyErrTuples[i], titleStrOrTupleOf3[i])
            if threeReports:
                return threeReports

# ===================================================================================
# =============== Settings Handler Class and Support Code ===========================
                  #######################################

class pluginCentraliser(MessageOutputUtilsClassAddin):
    """
    Handles all the settings. A callback method is added for each setting, it 
    gets called by ST if that setting is changed in the settings file.
    """
    objName = 'SaltyDog Settings Handler'
    pluginEnvGovDict = {
        "ID":       { "outputDictDesc": "Plugin Env Settings Gov Dict" },
        "Settings": {
            "pluginName": {"mand": True, "checks": ["is_str"]},
            "docsWeb": {"default": "", "checks": ["is_str"]},
            "pluginMainReloadModule": {"default": "", "checks": ["is_str"]},
            "reloadPluginWhenTheseSettingsChange": {"default": [], "checks": ["is_list_of_zom_strings"]},
            "reloadPluginWhenAnySettingsChange": {"default": False, "checks": ["is_bool"]},
            "doDebug": {"default": False, "checks": ["is_bool"]}
            }}

    def __init__(self, pluginSettingsGuvnor, setupEnv, defaultPluginName='NameNotSet'):
        # set self.pluginName' early on, as msg utils use this by preference
        self.pluginName = setupEnv.get('pluginName', defaultPluginName)
        self.storedWindowID = None
        self.fatalParseErr = False
        self.fatalParseErrStr = ""

        # setup pluginEnv from setupEnv
        # any errors here cause 'fatalInitErr'
        pluginEnvParser = dictGovernor(pluginCentraliser.pluginEnvGovDict, setupEnv)
        if pluginEnvParser.fatalInitErr or pluginEnvParser.fatalParseErr:
            self.fatalInitErr = True
            self.fatalInitErrStr = [pluginEnvParser.fatalParseErrStr, pluginEnvParser.fatalInitErrStr][pluginEnvParser.fatalInitErr]
            return
        else:
            self.pluginEnv = pluginEnvParser.getFullDict()
            if pluginEnvParser.fatalParseErr:
                self.fatalInitErr = True
                self.fatalInitErrStr = pluginEnvParser.fatalParseErrStr
                return
            elif pluginEnvParser.hasErrors():
                errTuple = pluginEnvParser.getErrors()
                errCounts = dictGovernor.errorCounts(errTuple)
                anESS = ['', 's'][(errCounts[0] > 1)] 
                titleStr = f'Programmatic error{anESS} found in plugin environment settings (plugin: {self.pluginName})'
                sectionStr = f"pluginEnv dictionary error{anESS}"
                errRep = f"{titleStr}\n\n{dictGovernor.getErrorReport(errTuple, sectionStr)}\n"
                self.fatalInitErr = True
                self.fatalInitErrStr = errRep
                return
                #***************************************************
                # if pluginEnvParser.fatalErr:
                #     self.fatalErr = True
                #     self.fatalErrReason = pluginEnvParser.fatalErrReason
                #     errRep += f'The error(s) is/are fatal. The plugin will no longer function correctly::\n\n{pluginEnvParser.fatalErrReason}.'
                # else:
                #     errRep += f'The plugin will attempt to operate despite the error(s)'
                # self.error_message(errRep)

        # add extra values to our self.pluginEnv dict
        self.pluginEnv['pluginSettingsFile'] = f"{self.pluginName}.sublime-settings"
        # We append 'PS' to define the project settings file section we will utilise
        # `- this separates it from sublime's own, buggy system, which self updates from a same-named section
        self.pluginEnv['projectFileSettingsSection'] = f"{self.pluginName}PS"
        # print(f'plugin env dict = {self.pluginEnv}')

        # load the plugin.sublime-settings values
        self.settings = sublime.load_settings(self.pluginEnv['pluginSettingsFile'])
        dcopy = self.settings.to_dict()
        self.DGov = dictGovernor(pluginSettingsGuvnor, dcopy)
        if self.DGov.fatalInitErr:
            self.fatalInitErr = True
            self.fatalInitErrStr = self.DGov.fatalParseErrStr
            return
        else:
            self.activeProjectFileName = None
            # print(f'project setts at init: {self.getProjectSettings()}')
            self.DGov.resetMergeDict(self.getProjectSettings())
            self.activeSettings = {}
            # don't want to report parse errors at setup stage and annoy user
            self.loadActiveSettings(reportErrors=False)
            # loadActiveSettings sets self.fatalParseErr/Str accordingly
            # if self.DGov.fatalParseErr:
            #     self.fatalParseErr = True
            #     self.fatalParseErrStr = self.DGov.fatalParseErrStr

        # implement a callback on the settings object
        # this will run 'self.setter' if any plugin.sublime-settings file is changed
        self.callbackName = f"{self.pluginName}WITH{SDframeworkName}"
        self.settings.clear_on_change(self.callbackName)
        self.settings.add_on_change(self.callbackName, self.setter)

        self.fatalInitErr = False
        self.fatalInitErrStr = ""
        #     else:
        #         self.fatalErr = True
        #         self.fatalErrReason = self.DGov.fatalErrReason
        # else:
        #     self.fatalErr = True
        #     self.fatalErrReason = pluginEnvParser.fatalErrReason

    # def name(self):
    #     return pluginCentraliser.objName + f'::{self.pluginName}'

    def loadActiveSettings(self, reportErrors=True):
        self.activeSettings = self.DGov.getFullDict()
        if reportErrors:
            self.reportErrors()
        self.fatalParseErr = self.DGov.fatalParseErr
        self.fatalParseErrStr = self.DGov.fatalParseErrStr
        # print(f'active settings = {self.activeSettings}')

    def reportErrors(self):
        if self.DGov.hasErrors():
            errTuple = self.DGov.getErrors()
            errCountMatrix = dictGovernor.errorCounts(errTuple)
            print(f'error count = {errCountMatrix}')
            if self.activeProjectFileName is None: # no project file data
                basePluralErrs = errCountMatrix[1][0] + errCountMatrix[1][2] > 1
                anESS = ('', 's')[basePluralErrs] 
                errRepTitle = f"{self.pluginName}: Error{anESS} found in settings:"
                sectionStr = f"Error{anESS} in {self.pluginEnv['pluginSettingsFile']} file:"
                remedyStr = f"Please correct above error{anESS} to ensure correct plugin functionality."
                errRep = f"{errRepTitle}\n\n{dictGovernor.getErrorReport(errTuple, sectionStr)}\n\n{remedyStr}"
            else: # we have project (merge) data to consider with the base settings
                basePluralErrs = errCountMatrix[1][0] > 1
                mergePluralErrs = errCountMatrix[1][1] > 1
                jointPluralErrs = errCountMatrix[1][2] > 1
                anESS = ('', 's')[basePluralErrs] 
                baseDictErrSource = f"{self.pluginEnv['pluginSettingsFile']} file error{anESS}:"
                anESS = ('', 's')[mergePluralErrs] 
                mergeDictErrSource = (f"{self.activeProjectFileName} file ({self.pluginEnv['projectFileSettingsSection']} "
                                      f"section) error{anESS}:")
                anESS = ('', 's')[jointPluralErrs] 
                jointDictErrSource = (f"Error{anESS} combining settings files ({self.pluginEnv['pluginSettingsFile']} "
                                      f"with {self.activeProjectFileName}):")
                errSources = (baseDictErrSource, mergeDictErrSource, jointDictErrSource)
                pluralityErrs = ('(1) error was', f'({errCountMatrix[0]}) errors were')[errCountMatrix[0] > 1] 
                errRepTitle = f'The following {pluralityErrs} found in the user configurable settings for this plugin:'
                remedyStr = f"Please correct the above to ensure correct plugin functionality."
                errRep = f"{errRepTitle}\n\n{dictGovernor.getErrorReport(errTuple, errSources)}\n\n{remedyStr}"
            self.msgBox(errRep)

    def getProjectSettings(self, window=None):
        thisPluginsSection = {} # return an empty dict if no project settings found, this resets any previous project settings
        if window is None:
            window = sublime.active_window()
        try:
            self.activeProjectFileName = os.path.basename(window.project_file_name())
        except:
            self.activeProjectFileName = None
        if self.activeProjectFileName is not None:
            try:
                settingsSection = window.project_data().get('settings')
                thisPluginsSection = settingsSection.get(self.pluginEnv['projectFileSettingsSection'], {})
                hasOrigPluginNameSection = self.pluginName in settingsSection
            except:
                thisPluginsSection = {}
                hasOrigPluginNameSection = False

            if self.activeProjectFileName and hasOrigPluginNameSection:
                self.error_message((f'WARNING: a [{self.pluginName}] section exists in your [{self.activeProjectFileName}] file. '
                    f'This should be removed to prevent conflicts.\n\n'
                    f'EXPLANATION: The {self.pluginName} plugin now uses the {SDframeworkName} framework to manage settings, '
                    f'and so storing project-file settings in the settings [{self.pluginName}] section is deprecated. '
                    f'This is because the {SDframeworkName} framework deals with project-file settings outside of sublime text\'s '
                    f'native management of these settings. Please put any project settings for the {self.pluginName} plugin '
                    f'into a [{self.pluginEnv["projectFileSettingsSection"]}] section beneath the "settings" section.'))

        return thisPluginsSection

        # if sublime.active_window().project_data():
        #     # get the 'settings' section from the active sublime project file
        #     # `- return None if there's no project file, or no settings section defined
        #     pluginSettingsOverides = sublime.active_window().project_data().get('settings')
        #     if pluginSettingsOverides:
        #         return pluginSettingsOverides.get(self.pluginEnv['projectFileSettingsSection'])

    def allowCommandsToRun(self):
        if self.fatalInitErr or self.fatalParseErr:
            try:
                safePluginName = f'The {self.pluginEnv["pluginName"]} plugin'
            except:
                try:
                    safePluginName = f'The command class [{stack()[1][0].f_locals["self"].__class__.__name__}]'
                except:
                    safePluginName = "The selected command"
            
            if self.fatalInitErr:
                print('deny commands due to fatalInitErr')
                titleStr = f'{safePluginName} is not currently operating due to a fatal plugin initialisation error:\n\n'
                errorStr = f'ERROR DESCRIPTION: {self.fatalInitErrStr}\n\n'
                remedyStr = 'Please correct this error and then RESTART Sublime Text to fix this issue.'
            elif self.fatalParseErr:
                print('deny commands due to fatalParseErr')
                titleStr = f'{safePluginName} is not currently operating due to a fatal plugin settings error:\n\n'
                errorStr = f'ERROR DESCRIPTION: {self.fatalParseErrStr}\n\n'
                remedyStr = 'Please correct this error to fix this issue.'
            sublime.message_dialog(f'{titleStr}{errorStr}{remedyStr}')
            return False
        else:
            return True

    def newProjectHook(self, window):
        if self.fatalInitErr:
            print('deny newProjectHook due to fatalInitErr')
            return
        try:
            if window.active_view().file_name().endswith('.sublime-project'):
                doShowErrs = True
            else:
                doShowErrs = False
        except:
            doShowErrs = False
        self.console_message(f'refreshing project settings due to project file reload (error disply = {doShowErrs})')
        self.freshWindowProjectReload(window, doShowErrs)

    def setStoredWindowID(self, view=None):
        try:
            if view is None:
                self.storedWindowID = sublime.active_window().id()
            else:
                self.storedWindowID = view.window().id()
        except:
            self.storedWindowID = None

    def newViewHook(self, view):
        if self.fatalInitErr:
            print('deny newViewHook due to fatalInitErr')
            return
        if view.window() is not None:
            if self.storedWindowID is None:
                self.setStoredWindowID()
            elif self.storedWindowID != view.window().id():
                # We only refresh the project settings if the new view is in a new window
                self.console_message('attempting to refresh project settings due to new window focus')
                self.freshWindowProjectReload(view.window())
                self.setStoredWindowID(view)

    def setter(self):
        """
        Callback function for settings changes,
        """
        resetFromSettingChange = False
        if self.pluginEnv['reloadPluginWhenAnySettingsChange']:
            resetFromSettingChange = True
        elif self.pluginEnv['reloadPluginWhenTheseSettingsChange']:
            theseVarsWereChanged = []
            for k, v in self.settings.to_dict().items():
                if k in self.activeSettings.keys():
                    if v != self.activeSettings[k]:
                        # an active setting has been changed on disk
                        theseVarsWereChanged.append(k)
                else:
                    # a not-previously-defined setting has been found
                    theseVarsWereChanged.append(k)
            resetFromSettingChange = False
            for reactiveSetting in self.pluginEnv['reloadPluginWhenTheseSettingsChange']:
                if reactiveSetting in theseVarsWereChanged:
                    resetFromSettingChange = True
                    break

        if resetFromSettingChange and self.pluginEnv['pluginMainReloadModule']:
            self.console_message(f"Settings change has prompted reload of plugin: {self.pluginEnv.get('pluginMainReloadModule')}")
            sublime_plugin.reload_plugin(self.pluginEnv['pluginMainReloadModule'])
        else:
            self.DGov.resetBaseDict(self.settings.to_dict())
            self.loadActiveSettings()

    def freshWindowProjectReload(self, window, displayErrs=True):
        self.DGov.resetMergeDict(self.getProjectSettings(window))
        self.loadActiveSettings(displayErrs)

    def settingsAsDict(self):
        return dict(self.activeSettings)

class runSafeSubprocess():

    def __init__(self, cmdTokens: list, **processArgs):
        self.metaOK = False
        self.processOK = False
        self.cmdResult = None
        self.processArgs = processArgs
        # self.processArgs.update(runSafeSubprocess.captureArgs)
        self.metaFailStr = ""
        self.processFailStr = ""
        try:
            self.cmdResult = subprocess.run(cmdTokens, **self.processArgs)
            self.metaOK = True
        except subprocess.TimeoutExpired:
            self.metaFailStr = (f'The given shell command timed out after {processArgs.get("timeout", "excess")} seconds.\n\n'
                             'The timeout can be set in the range 1-600 seconds.')
        except Exception as err:
            self.metaFailStr = ("Shell command failed as an unexpected exception occurred.\n\n"
                              "Details:: {}\n\n{}".format(err.__class__.__name__, err))
        if self.cmdResult:
            self.processOK = self.cmdResult.returncode == 0
            self.processFailStr = self.cmdResult.stderr

    @classmethod
    def getBinary(cls, cmdTokens: list, **processArgs):
        captureArgs = {
            "capture_output"    : True,
        }
        processArgs.update(captureArgs)
        obj = cls(cmdTokens, **processArgs)
        return obj

    @classmethod
    def getText(cls, cmdTokens: list, **processArgs):
        captureArgs = {
            "capture_output"    : True,
            "text"              : True
        }
        processArgs.update(captureArgs)
        obj = cls(cmdTokens, **processArgs)
        return obj

    def allOK(self):
        return self.metaOK and self.processOK

