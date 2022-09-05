# Generated from /home/luka/Projects/Python/refind-btrfs/src/refind_btrfs/boot/antlr4/RefindConfigParser.g4 by ANTLR 4.11.1
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,23,134,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,1,0,
        5,0,42,8,0,10,0,12,0,45,9,0,1,0,1,0,1,1,1,1,3,1,51,8,1,1,2,1,2,1,
        2,4,2,56,8,2,11,2,12,2,57,1,2,1,2,1,3,1,3,1,3,1,4,1,4,1,4,1,4,1,
        4,1,4,1,4,1,4,1,4,1,4,3,4,75,8,4,1,5,1,5,1,5,1,6,1,6,1,6,1,7,1,7,
        1,7,1,8,1,8,1,8,1,9,1,9,1,9,1,10,1,10,1,10,1,11,1,11,1,11,1,12,1,
        12,1,12,1,13,1,13,1,14,1,14,1,14,4,14,106,8,14,11,14,12,14,107,1,
        14,1,14,1,15,1,15,1,15,1,15,1,15,1,15,3,15,118,8,15,1,16,1,16,3,
        16,122,8,16,1,17,1,17,3,17,126,8,17,1,18,1,18,1,18,1,19,1,19,1,19,
        1,19,0,0,20,0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,
        38,0,0,133,0,43,1,0,0,0,2,50,1,0,0,0,4,52,1,0,0,0,6,61,1,0,0,0,8,
        74,1,0,0,0,10,76,1,0,0,0,12,79,1,0,0,0,14,82,1,0,0,0,16,85,1,0,0,
        0,18,88,1,0,0,0,20,91,1,0,0,0,22,94,1,0,0,0,24,97,1,0,0,0,26,100,
        1,0,0,0,28,102,1,0,0,0,30,117,1,0,0,0,32,119,1,0,0,0,34,123,1,0,
        0,0,36,127,1,0,0,0,38,130,1,0,0,0,40,42,3,2,1,0,41,40,1,0,0,0,42,
        45,1,0,0,0,43,41,1,0,0,0,43,44,1,0,0,0,44,46,1,0,0,0,45,43,1,0,0,
        0,46,47,5,0,0,1,47,1,1,0,0,0,48,51,3,4,2,0,49,51,3,38,19,0,50,48,
        1,0,0,0,50,49,1,0,0,0,51,3,1,0,0,0,52,53,3,6,3,0,53,55,5,18,0,0,
        54,56,3,8,4,0,55,54,1,0,0,0,56,57,1,0,0,0,57,55,1,0,0,0,57,58,1,
        0,0,0,58,59,1,0,0,0,59,60,5,19,0,0,60,5,1,0,0,0,61,62,5,6,0,0,62,
        63,5,21,0,0,63,7,1,0,0,0,64,75,3,10,5,0,65,75,3,12,6,0,66,75,3,14,
        7,0,67,75,3,16,8,0,68,75,3,18,9,0,69,75,3,20,10,0,70,75,3,22,11,
        0,71,75,3,24,12,0,72,75,3,26,13,0,73,75,3,28,14,0,74,64,1,0,0,0,
        74,65,1,0,0,0,74,66,1,0,0,0,74,67,1,0,0,0,74,68,1,0,0,0,74,69,1,
        0,0,0,74,70,1,0,0,0,74,71,1,0,0,0,74,72,1,0,0,0,74,73,1,0,0,0,75,
        9,1,0,0,0,76,77,5,7,0,0,77,78,5,21,0,0,78,11,1,0,0,0,79,80,5,8,0,
        0,80,81,5,21,0,0,81,13,1,0,0,0,82,83,5,9,0,0,83,84,5,21,0,0,84,15,
        1,0,0,0,85,86,5,10,0,0,86,87,5,21,0,0,87,17,1,0,0,0,88,89,5,11,0,
        0,89,90,5,22,0,0,90,19,1,0,0,0,91,92,5,12,0,0,92,93,5,23,0,0,93,
        21,1,0,0,0,94,95,5,13,0,0,95,96,5,21,0,0,96,23,1,0,0,0,97,98,5,15,
        0,0,98,99,5,20,0,0,99,25,1,0,0,0,100,101,5,16,0,0,101,27,1,0,0,0,
        102,103,3,6,3,0,103,105,5,18,0,0,104,106,3,30,15,0,105,104,1,0,0,
        0,106,107,1,0,0,0,107,105,1,0,0,0,107,108,1,0,0,0,108,109,1,0,0,
        0,109,110,5,19,0,0,110,29,1,0,0,0,111,118,3,12,6,0,112,118,3,32,
        16,0,113,118,3,20,10,0,114,118,3,34,17,0,115,118,3,36,18,0,116,118,
        3,26,13,0,117,111,1,0,0,0,117,112,1,0,0,0,117,113,1,0,0,0,117,114,
        1,0,0,0,117,115,1,0,0,0,117,116,1,0,0,0,118,31,1,0,0,0,119,121,5,
        9,0,0,120,122,5,21,0,0,121,120,1,0,0,0,121,122,1,0,0,0,122,33,1,
        0,0,0,123,125,5,13,0,0,124,126,5,21,0,0,125,124,1,0,0,0,125,126,
        1,0,0,0,126,35,1,0,0,0,127,128,5,14,0,0,128,129,5,21,0,0,129,37,
        1,0,0,0,130,131,5,17,0,0,131,132,5,21,0,0,132,39,1,0,0,0,8,43,50,
        57,74,107,117,121,125
    ]

class RefindConfigParser ( Parser ):

    grammarFileName = "RefindConfigParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "'volume'", 
                     "'loader'", "'initrd'", "'icon'", "<INVALID>", "<INVALID>", 
                     "'options'", "'add_options'", "'firmware_bootnum'", 
                     "'disabled'", "'include'", "'{'", "'}'" ]

    symbolicNames = [ "<INVALID>", "WHITESPACE", "NEWLINE", "EMPTY", "COMMENT", 
                      "IGNORED_OPTION", "MENU_ENTRY", "VOLUME", "LOADER", 
                      "INITRD", "ICON", "OS_TYPE", "GRAPHICS", "BOOT_OPTIONS", 
                      "ADD_BOOT_OPTIONS", "FIRMWARE_BOOTNUM", "DISABLED", 
                      "INCLUDE", "OPEN_BRACE", "CLOSE_BRACE", "HEX_INTEGER", 
                      "STRING", "OS_TYPE_PARAMETER", "GRAPHICS_PARAMETER" ]

    RULE_refind = 0
    RULE_config_option = 1
    RULE_boot_stanza = 2
    RULE_menu_entry = 3
    RULE_main_option = 4
    RULE_volume = 5
    RULE_loader = 6
    RULE_main_initrd = 7
    RULE_icon = 8
    RULE_os_type = 9
    RULE_graphics = 10
    RULE_main_boot_options = 11
    RULE_firmware_bootnum = 12
    RULE_disabled = 13
    RULE_sub_menu = 14
    RULE_sub_option = 15
    RULE_sub_initrd = 16
    RULE_sub_boot_options = 17
    RULE_add_boot_options = 18
    RULE_include = 19

    ruleNames =  [ "refind", "config_option", "boot_stanza", "menu_entry", 
                   "main_option", "volume", "loader", "main_initrd", "icon", 
                   "os_type", "graphics", "main_boot_options", "firmware_bootnum", 
                   "disabled", "sub_menu", "sub_option", "sub_initrd", "sub_boot_options", 
                   "add_boot_options", "include" ]

    EOF = Token.EOF
    WHITESPACE=1
    NEWLINE=2
    EMPTY=3
    COMMENT=4
    IGNORED_OPTION=5
    MENU_ENTRY=6
    VOLUME=7
    LOADER=8
    INITRD=9
    ICON=10
    OS_TYPE=11
    GRAPHICS=12
    BOOT_OPTIONS=13
    ADD_BOOT_OPTIONS=14
    FIRMWARE_BOOTNUM=15
    DISABLED=16
    INCLUDE=17
    OPEN_BRACE=18
    CLOSE_BRACE=19
    HEX_INTEGER=20
    STRING=21
    OS_TYPE_PARAMETER=22
    GRAPHICS_PARAMETER=23

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.11.1")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class RefindContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EOF(self):
            return self.getToken(RefindConfigParser.EOF, 0)

        def config_option(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RefindConfigParser.Config_optionContext)
            else:
                return self.getTypedRuleContext(RefindConfigParser.Config_optionContext,i)


        def getRuleIndex(self):
            return RefindConfigParser.RULE_refind

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRefind" ):
                return visitor.visitRefind(self)
            else:
                return visitor.visitChildren(self)




    def refind(self):

        localctx = RefindConfigParser.RefindContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_refind)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 43
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==6 or _la==17:
                self.state = 40
                self.config_option()
                self.state = 45
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 46
            self.match(RefindConfigParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Config_optionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def boot_stanza(self):
            return self.getTypedRuleContext(RefindConfigParser.Boot_stanzaContext,0)


        def include(self):
            return self.getTypedRuleContext(RefindConfigParser.IncludeContext,0)


        def getRuleIndex(self):
            return RefindConfigParser.RULE_config_option

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConfig_option" ):
                return visitor.visitConfig_option(self)
            else:
                return visitor.visitChildren(self)




    def config_option(self):

        localctx = RefindConfigParser.Config_optionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_config_option)
        try:
            self.state = 50
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [6]:
                self.enterOuterAlt(localctx, 1)
                self.state = 48
                self.boot_stanza()
                pass
            elif token in [17]:
                self.enterOuterAlt(localctx, 2)
                self.state = 49
                self.include()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Boot_stanzaContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def menu_entry(self):
            return self.getTypedRuleContext(RefindConfigParser.Menu_entryContext,0)


        def OPEN_BRACE(self):
            return self.getToken(RefindConfigParser.OPEN_BRACE, 0)

        def CLOSE_BRACE(self):
            return self.getToken(RefindConfigParser.CLOSE_BRACE, 0)

        def main_option(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RefindConfigParser.Main_optionContext)
            else:
                return self.getTypedRuleContext(RefindConfigParser.Main_optionContext,i)


        def getRuleIndex(self):
            return RefindConfigParser.RULE_boot_stanza

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBoot_stanza" ):
                return visitor.visitBoot_stanza(self)
            else:
                return visitor.visitChildren(self)




    def boot_stanza(self):

        localctx = RefindConfigParser.Boot_stanzaContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_boot_stanza)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 52
            self.menu_entry()
            self.state = 53
            self.match(RefindConfigParser.OPEN_BRACE)
            self.state = 55 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 54
                self.main_option()
                self.state = 57 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (((_la) & ~0x3f) == 0 and ((1 << _la) & 114624) != 0):
                    break

            self.state = 59
            self.match(RefindConfigParser.CLOSE_BRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Menu_entryContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def MENU_ENTRY(self):
            return self.getToken(RefindConfigParser.MENU_ENTRY, 0)

        def STRING(self):
            return self.getToken(RefindConfigParser.STRING, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_menu_entry

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMenu_entry" ):
                return visitor.visitMenu_entry(self)
            else:
                return visitor.visitChildren(self)




    def menu_entry(self):

        localctx = RefindConfigParser.Menu_entryContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_menu_entry)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 61
            self.match(RefindConfigParser.MENU_ENTRY)
            self.state = 62
            self.match(RefindConfigParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Main_optionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def volume(self):
            return self.getTypedRuleContext(RefindConfigParser.VolumeContext,0)


        def loader(self):
            return self.getTypedRuleContext(RefindConfigParser.LoaderContext,0)


        def main_initrd(self):
            return self.getTypedRuleContext(RefindConfigParser.Main_initrdContext,0)


        def icon(self):
            return self.getTypedRuleContext(RefindConfigParser.IconContext,0)


        def os_type(self):
            return self.getTypedRuleContext(RefindConfigParser.Os_typeContext,0)


        def graphics(self):
            return self.getTypedRuleContext(RefindConfigParser.GraphicsContext,0)


        def main_boot_options(self):
            return self.getTypedRuleContext(RefindConfigParser.Main_boot_optionsContext,0)


        def firmware_bootnum(self):
            return self.getTypedRuleContext(RefindConfigParser.Firmware_bootnumContext,0)


        def disabled(self):
            return self.getTypedRuleContext(RefindConfigParser.DisabledContext,0)


        def sub_menu(self):
            return self.getTypedRuleContext(RefindConfigParser.Sub_menuContext,0)


        def getRuleIndex(self):
            return RefindConfigParser.RULE_main_option

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMain_option" ):
                return visitor.visitMain_option(self)
            else:
                return visitor.visitChildren(self)




    def main_option(self):

        localctx = RefindConfigParser.Main_optionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_main_option)
        try:
            self.state = 74
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [7]:
                self.enterOuterAlt(localctx, 1)
                self.state = 64
                self.volume()
                pass
            elif token in [8]:
                self.enterOuterAlt(localctx, 2)
                self.state = 65
                self.loader()
                pass
            elif token in [9]:
                self.enterOuterAlt(localctx, 3)
                self.state = 66
                self.main_initrd()
                pass
            elif token in [10]:
                self.enterOuterAlt(localctx, 4)
                self.state = 67
                self.icon()
                pass
            elif token in [11]:
                self.enterOuterAlt(localctx, 5)
                self.state = 68
                self.os_type()
                pass
            elif token in [12]:
                self.enterOuterAlt(localctx, 6)
                self.state = 69
                self.graphics()
                pass
            elif token in [13]:
                self.enterOuterAlt(localctx, 7)
                self.state = 70
                self.main_boot_options()
                pass
            elif token in [15]:
                self.enterOuterAlt(localctx, 8)
                self.state = 71
                self.firmware_bootnum()
                pass
            elif token in [16]:
                self.enterOuterAlt(localctx, 9)
                self.state = 72
                self.disabled()
                pass
            elif token in [6]:
                self.enterOuterAlt(localctx, 10)
                self.state = 73
                self.sub_menu()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VolumeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def VOLUME(self):
            return self.getToken(RefindConfigParser.VOLUME, 0)

        def STRING(self):
            return self.getToken(RefindConfigParser.STRING, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_volume

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVolume" ):
                return visitor.visitVolume(self)
            else:
                return visitor.visitChildren(self)




    def volume(self):

        localctx = RefindConfigParser.VolumeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_volume)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 76
            self.match(RefindConfigParser.VOLUME)
            self.state = 77
            self.match(RefindConfigParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class LoaderContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LOADER(self):
            return self.getToken(RefindConfigParser.LOADER, 0)

        def STRING(self):
            return self.getToken(RefindConfigParser.STRING, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_loader

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLoader" ):
                return visitor.visitLoader(self)
            else:
                return visitor.visitChildren(self)




    def loader(self):

        localctx = RefindConfigParser.LoaderContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_loader)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 79
            self.match(RefindConfigParser.LOADER)
            self.state = 80
            self.match(RefindConfigParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Main_initrdContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INITRD(self):
            return self.getToken(RefindConfigParser.INITRD, 0)

        def STRING(self):
            return self.getToken(RefindConfigParser.STRING, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_main_initrd

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMain_initrd" ):
                return visitor.visitMain_initrd(self)
            else:
                return visitor.visitChildren(self)




    def main_initrd(self):

        localctx = RefindConfigParser.Main_initrdContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_main_initrd)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 82
            self.match(RefindConfigParser.INITRD)
            self.state = 83
            self.match(RefindConfigParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IconContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ICON(self):
            return self.getToken(RefindConfigParser.ICON, 0)

        def STRING(self):
            return self.getToken(RefindConfigParser.STRING, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_icon

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIcon" ):
                return visitor.visitIcon(self)
            else:
                return visitor.visitChildren(self)




    def icon(self):

        localctx = RefindConfigParser.IconContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_icon)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 85
            self.match(RefindConfigParser.ICON)
            self.state = 86
            self.match(RefindConfigParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Os_typeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def OS_TYPE(self):
            return self.getToken(RefindConfigParser.OS_TYPE, 0)

        def OS_TYPE_PARAMETER(self):
            return self.getToken(RefindConfigParser.OS_TYPE_PARAMETER, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_os_type

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOs_type" ):
                return visitor.visitOs_type(self)
            else:
                return visitor.visitChildren(self)




    def os_type(self):

        localctx = RefindConfigParser.Os_typeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_os_type)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 88
            self.match(RefindConfigParser.OS_TYPE)
            self.state = 89
            self.match(RefindConfigParser.OS_TYPE_PARAMETER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class GraphicsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def GRAPHICS(self):
            return self.getToken(RefindConfigParser.GRAPHICS, 0)

        def GRAPHICS_PARAMETER(self):
            return self.getToken(RefindConfigParser.GRAPHICS_PARAMETER, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_graphics

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitGraphics" ):
                return visitor.visitGraphics(self)
            else:
                return visitor.visitChildren(self)




    def graphics(self):

        localctx = RefindConfigParser.GraphicsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_graphics)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 91
            self.match(RefindConfigParser.GRAPHICS)
            self.state = 92
            self.match(RefindConfigParser.GRAPHICS_PARAMETER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Main_boot_optionsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def BOOT_OPTIONS(self):
            return self.getToken(RefindConfigParser.BOOT_OPTIONS, 0)

        def STRING(self):
            return self.getToken(RefindConfigParser.STRING, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_main_boot_options

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMain_boot_options" ):
                return visitor.visitMain_boot_options(self)
            else:
                return visitor.visitChildren(self)




    def main_boot_options(self):

        localctx = RefindConfigParser.Main_boot_optionsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_main_boot_options)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 94
            self.match(RefindConfigParser.BOOT_OPTIONS)
            self.state = 95
            self.match(RefindConfigParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Firmware_bootnumContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def FIRMWARE_BOOTNUM(self):
            return self.getToken(RefindConfigParser.FIRMWARE_BOOTNUM, 0)

        def HEX_INTEGER(self):
            return self.getToken(RefindConfigParser.HEX_INTEGER, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_firmware_bootnum

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFirmware_bootnum" ):
                return visitor.visitFirmware_bootnum(self)
            else:
                return visitor.visitChildren(self)




    def firmware_bootnum(self):

        localctx = RefindConfigParser.Firmware_bootnumContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_firmware_bootnum)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 97
            self.match(RefindConfigParser.FIRMWARE_BOOTNUM)
            self.state = 98
            self.match(RefindConfigParser.HEX_INTEGER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DisabledContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def DISABLED(self):
            return self.getToken(RefindConfigParser.DISABLED, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_disabled

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDisabled" ):
                return visitor.visitDisabled(self)
            else:
                return visitor.visitChildren(self)




    def disabled(self):

        localctx = RefindConfigParser.DisabledContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_disabled)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 100
            self.match(RefindConfigParser.DISABLED)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Sub_menuContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def menu_entry(self):
            return self.getTypedRuleContext(RefindConfigParser.Menu_entryContext,0)


        def OPEN_BRACE(self):
            return self.getToken(RefindConfigParser.OPEN_BRACE, 0)

        def CLOSE_BRACE(self):
            return self.getToken(RefindConfigParser.CLOSE_BRACE, 0)

        def sub_option(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RefindConfigParser.Sub_optionContext)
            else:
                return self.getTypedRuleContext(RefindConfigParser.Sub_optionContext,i)


        def getRuleIndex(self):
            return RefindConfigParser.RULE_sub_menu

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSub_menu" ):
                return visitor.visitSub_menu(self)
            else:
                return visitor.visitChildren(self)




    def sub_menu(self):

        localctx = RefindConfigParser.Sub_menuContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_sub_menu)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 102
            self.menu_entry()
            self.state = 103
            self.match(RefindConfigParser.OPEN_BRACE)
            self.state = 105 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 104
                self.sub_option()
                self.state = 107 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (((_la) & ~0x3f) == 0 and ((1 << _la) & 94976) != 0):
                    break

            self.state = 109
            self.match(RefindConfigParser.CLOSE_BRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Sub_optionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def loader(self):
            return self.getTypedRuleContext(RefindConfigParser.LoaderContext,0)


        def sub_initrd(self):
            return self.getTypedRuleContext(RefindConfigParser.Sub_initrdContext,0)


        def graphics(self):
            return self.getTypedRuleContext(RefindConfigParser.GraphicsContext,0)


        def sub_boot_options(self):
            return self.getTypedRuleContext(RefindConfigParser.Sub_boot_optionsContext,0)


        def add_boot_options(self):
            return self.getTypedRuleContext(RefindConfigParser.Add_boot_optionsContext,0)


        def disabled(self):
            return self.getTypedRuleContext(RefindConfigParser.DisabledContext,0)


        def getRuleIndex(self):
            return RefindConfigParser.RULE_sub_option

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSub_option" ):
                return visitor.visitSub_option(self)
            else:
                return visitor.visitChildren(self)




    def sub_option(self):

        localctx = RefindConfigParser.Sub_optionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_sub_option)
        try:
            self.state = 117
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [8]:
                self.enterOuterAlt(localctx, 1)
                self.state = 111
                self.loader()
                pass
            elif token in [9]:
                self.enterOuterAlt(localctx, 2)
                self.state = 112
                self.sub_initrd()
                pass
            elif token in [12]:
                self.enterOuterAlt(localctx, 3)
                self.state = 113
                self.graphics()
                pass
            elif token in [13]:
                self.enterOuterAlt(localctx, 4)
                self.state = 114
                self.sub_boot_options()
                pass
            elif token in [14]:
                self.enterOuterAlt(localctx, 5)
                self.state = 115
                self.add_boot_options()
                pass
            elif token in [16]:
                self.enterOuterAlt(localctx, 6)
                self.state = 116
                self.disabled()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Sub_initrdContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INITRD(self):
            return self.getToken(RefindConfigParser.INITRD, 0)

        def STRING(self):
            return self.getToken(RefindConfigParser.STRING, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_sub_initrd

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSub_initrd" ):
                return visitor.visitSub_initrd(self)
            else:
                return visitor.visitChildren(self)




    def sub_initrd(self):

        localctx = RefindConfigParser.Sub_initrdContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_sub_initrd)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 119
            self.match(RefindConfigParser.INITRD)
            self.state = 121
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==21:
                self.state = 120
                self.match(RefindConfigParser.STRING)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Sub_boot_optionsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def BOOT_OPTIONS(self):
            return self.getToken(RefindConfigParser.BOOT_OPTIONS, 0)

        def STRING(self):
            return self.getToken(RefindConfigParser.STRING, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_sub_boot_options

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSub_boot_options" ):
                return visitor.visitSub_boot_options(self)
            else:
                return visitor.visitChildren(self)




    def sub_boot_options(self):

        localctx = RefindConfigParser.Sub_boot_optionsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_sub_boot_options)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 123
            self.match(RefindConfigParser.BOOT_OPTIONS)
            self.state = 125
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==21:
                self.state = 124
                self.match(RefindConfigParser.STRING)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Add_boot_optionsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ADD_BOOT_OPTIONS(self):
            return self.getToken(RefindConfigParser.ADD_BOOT_OPTIONS, 0)

        def STRING(self):
            return self.getToken(RefindConfigParser.STRING, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_add_boot_options

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAdd_boot_options" ):
                return visitor.visitAdd_boot_options(self)
            else:
                return visitor.visitChildren(self)




    def add_boot_options(self):

        localctx = RefindConfigParser.Add_boot_optionsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_add_boot_options)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 127
            self.match(RefindConfigParser.ADD_BOOT_OPTIONS)
            self.state = 128
            self.match(RefindConfigParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IncludeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INCLUDE(self):
            return self.getToken(RefindConfigParser.INCLUDE, 0)

        def STRING(self):
            return self.getToken(RefindConfigParser.STRING, 0)

        def getRuleIndex(self):
            return RefindConfigParser.RULE_include

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInclude" ):
                return visitor.visitInclude(self)
            else:
                return visitor.visitChildren(self)




    def include(self):

        localctx = RefindConfigParser.IncludeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 38, self.RULE_include)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 130
            self.match(RefindConfigParser.INCLUDE)
            self.state = 131
            self.match(RefindConfigParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





