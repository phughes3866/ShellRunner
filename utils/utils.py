import os
import shlex

def buildPathFileDirSidebarItemStrings(argsDict):
    """
    Build space separated string lists of 'files', 'dirs', 'paths' from same-named lists available in args passed
    Sublime Text fills these optional sidebar menu args appropriately when they are given in a sidebar menu command:
    `- e.g. a list arg "dirs": [] will be filled in with a list of dirs currently selected in the sidebar
    Additionally 'lastFile', 'lastDir' and 'lastPath' strings are made which correspond to the most recent selected
    If any of the lists required is not available, the appropriate strings are set to zero length strings.
    """
    addDict = {}
    for addList in ['files', 'dirs', 'paths']:
        gotList = argsDict.get(addList)
        lastSelectedKey = "last" + addList[:-1].capitalize()
        if gotList:
            escapedList = [shlex.quote(a) for a in gotList]
            addDict[addList] = " ".join(escapedList)
            addDict[lastSelectedKey] = escapedList[0]
        else:
            addDict[addList] = ""
            addDict[lastSelectedKey] = ""
    return addDict


class splitCommand():
    def __init__(self, cmdStr):
        self.cmdStr = cmdStr
        self.OK = False
        self.errorStr = ""
        try:
            self.tokens = shlex.split(self.cmdStr, posix=True)
            self.OK = True
        except Exception as err:
            self.tokens = ['']
            self.errorStr = ("An unexpected exception occurred in splitting/tokenising your command for the shell. "
                              "Please check your command is formatted correctly.\n\n"
                              "Split attempted on:: {}\n\n"
                              "Details:: {}\n\n{}").format(self.cmdStr, err.__class__.__name__, err)

def truncateStr(thisStr: str, chopFromStart=False, replacementStr="...", outputLength=35) -> str:
    lenny = len(thisStr)
    if lenny > outputLength:
        chopLen = outputLength - len(replacementStr)
        if chopFromStart:
            chopLen = lenny - chopLen
            thisStr = (replacementStr + thisStr[chopLen:])
        else:
            thisStr = (thisStr[:chopLen] + replacementStr)
    return thisStr


def deListCmd(cmdMightBeList):
    if isinstance(cmdMightBeList, list):
        return " ".join(cmdMightBeList)
    else:
        return cmdMightBeList

class cmdManips():
    def shellCmdAsStr(self, rawCmd):
        """

        """
        if isinstance(rawCmd, list):
            typeMarker = rawCmd[0]
            if typeMarker in ["string", "tokens"]:
                if typeMarker == "string":
                    return "".join(rawCmd[1:])
                else:
                    return " ".join(rawCmd[1:])
            else:
                return "".join(rawCmd)
        else:
            return rawCmd

    def shellCmdAsTokens(self, rawCmd):
        """

        """
        if isinstance(rawCmd, list):
            typeMarker = rawCmd[0]
            if typeMarker in ["string", "tokens"]:
                if typeMarker == "string":
                    oneStr = "".join(rawCmd[1:])
                else:
                    return rawCmd[1:], ""
            else:
                oneStr = "".join(rawCmd)
        else:
            oneStr = rawCmd
        tokenObj = splitCommand(oneStr)
        if tokenObj.errorStr:
            # self.console_message(f'Error splitting command into shell tokens: {tokenObj.errorStr}')
            return [], tokenObj.errorStr
        else:
            return tokenObj.tokens, ""

def makeLiteralStr(normStr: str) -> str:
    # first replace single backslash with double
    # `- note that the single backslash is represented as an escaped backslash
    #  - and a backslash is used to represent the escape
    morphingStr = normStr.replace("\\", "\\\\") 
    # a shell $'literal string' is thus enclosed, and it is necessary
    # `- only to 'escape' contained single quotes
    return "$'" + morphingStr.replace("'", "\\'") + "'" 

class cmdEnabledInMenu():
    def __init__(self, cmdArgs, windowVars):
        """
        Determines whether a command should be enabled or not (greyed out in menus, disabled on keybind)
        Returns true if enabled false if not.
        We have 2 args that can disable a command, these are: targetExtns and dirOnly
        For the enablement logic to work we first need to work out whether our command was sidebar launched or not
        `- this is because sidebar commands can work on directories and lists of files, rather than just the active file
        """
        self.cmdArgs = cmdArgs
        self.windowVars = windowVars
        self.disabledReason = ""

    def is_enabled(self):
        fullCmd = self.cmdArgs.get('shellCommand')
        if fullCmd is not None:
            self.targetCmdShortStr = truncateStr(deListCmd(fullCmd))
        else:
            return True # show visible if no command, errors will show elsewhere
        # windowVars = self.window.extract_variables()

        # def noShowReason(self, reason):
        #     self.console_message(f'CMD DISABLED::{reason}')

        targetExtns = self.cmdArgs.get('targetExtensions', False)
        # We we are in sidebar (sbMode) mode if no 'x-y' coordinates given for mouse click event
        sbMode = 'x' not in self.cmdArgs.get('event', {})
        if sbMode:
            # DEBUG and buildRep("- Sidebar Menu Mode Check\n")
            dirOnly = self.cmdArgs.get('dirOnly', False)
            # extraForDirs = "(or dir) "
        else:
            # DEBUG and buildRep("- Context Menu or Key Bind Mode Check\n")
            # the 'dirOnly' arg has no place in a non-sidebar 'window' command, ignore it if is set
            dirOnly = False
            # extraForDirs = ""
            
        sideBarItems = buildPathFileDirSidebarItemStrings(self.cmdArgs)
        if targetExtns:
            # DEBUG and buildRep("- File extension match required\n")
            # DEBUG and buildRep("- Extensions to match = {}\n".format(targetExtns))
            # visMe = False  # until proven otherwise
            # NB: the initial dot/period must be included for each of targetExtensions e.g. ".jpg" not "jpg"
            #    ` multipart extensions are not catered for e.g. ".tar.gz" will never match, but ".gz" will
            if sbMode:
                lastSelectedSidebarPath = ""
                # DEBUG and buildRep("-- Looking for last selected sidebar file via [files] arg\n")
                # sbFiles = self.visArgs.get('files', False)
                if sideBarItems.get('lastFile'):
                    lastSelectedSidebarPath = sideBarItems.get('lastFile')
                    # DEBUG and buildRep('-- Last selected sidebar file to match = {}\n'.format(truncateStr(lastSelectedSidebarPath, outputLength=25, chopFromStart=True)))
                elif sideBarItems.get('lastPath'):
                    # DEBUG and buildRep("-- [files] arg not available, looking via [paths] arg\n")
                    # sbPaths = self.visArgs.get('paths', False)
                    # if sbPaths:
                    #     lastSelectedSidebarPath = sbPaths[0]
                    #     DEBUG and buildRep('-- Last selected sidebar path to match = {}\n'.format(truncateStr(lastSelectedSidebarPath, outputLength=25, chopFromStart=True)))
                    if os.path.isfile(sideBarItems.get('lastPath')):
                        # DEBUG and buildRep('-- Path found is a file\n')
                        lastSelectedSidebarPath = sideBarItems.get('lastPath')
                    # else:
                    #     DEBUG and buildRep('Path found is NOT a file\n')
                # else:
                #     self.dBug("-- WARNING: No sidebar 'files':[] or 'paths': [] args via which to acquire file to match\n")
                fileToCheckExtn = lastSelectedSidebarPath
            else:  # not sidebar mode i.e. key bind or context menu
                fileToCheckExtn = windowVars.get('file')
                # DEBUG and buildRep('-- Active window file to match = {}\n'.format(truncateStr(fileToCheckExtn, outputLength=25, chopFromStart=True)))
            
            if fileToCheckExtn:
                # targetExtn entries must be preceeded by a dot to work
                haveExtn = os.path.splitext(fileToCheckExtn)[1]
                if haveExtn in targetExtns:
                    # DEBUG and buildRep('-- Target file extension ({}) matches\n'.format(haveExtn))
                    return True
                else:
                    self.disabledReason = f'Target file extension ({haveExtn}) is not in {targetExtns}'
                    return False
            else:
                self.disabledReason = 'No target file found on which to perform match check.'
                return False
        elif dirOnly:
            # DEBUG and buildRep('- Command valid only for directories i.e. "dirOnly" set in args (must be sidebar mode)\n')
            # visMe = False
            if sideBarItems.get('lastDir'):
                # DEBUG and buildRep('- Directory detected in sidebar selections (via [dirs] arg)\n')
                # If any directory is selected
                return True
            else:
                self.disabledReason = 'No sidebar directory selection detected (is [dirs] arg provided)\n'
                return False
        else:
            return True
