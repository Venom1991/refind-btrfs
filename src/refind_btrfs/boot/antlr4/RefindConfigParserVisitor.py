# Generated from /home/luka/Projects/Python/refind-btrfs/src/refind_btrfs/boot/antlr4/RefindConfigParser.g4 by ANTLR 4.9.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .RefindConfigParser import RefindConfigParser
else:
    from RefindConfigParser import RefindConfigParser

# This class defines a complete generic visitor for a parse tree produced by RefindConfigParser.

class RefindConfigParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by RefindConfigParser#refind.
    def visitRefind(self, ctx:RefindConfigParser.RefindContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#config_option.
    def visitConfig_option(self, ctx:RefindConfigParser.Config_optionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#boot_stanza.
    def visitBoot_stanza(self, ctx:RefindConfigParser.Boot_stanzaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#menu_entry.
    def visitMenu_entry(self, ctx:RefindConfigParser.Menu_entryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#main_option.
    def visitMain_option(self, ctx:RefindConfigParser.Main_optionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#volume.
    def visitVolume(self, ctx:RefindConfigParser.VolumeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#loader.
    def visitLoader(self, ctx:RefindConfigParser.LoaderContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#main_initrd.
    def visitMain_initrd(self, ctx:RefindConfigParser.Main_initrdContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#icon.
    def visitIcon(self, ctx:RefindConfigParser.IconContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#os_type.
    def visitOs_type(self, ctx:RefindConfigParser.Os_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#graphics.
    def visitGraphics(self, ctx:RefindConfigParser.GraphicsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#main_boot_options.
    def visitMain_boot_options(self, ctx:RefindConfigParser.Main_boot_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#firmware_bootnum.
    def visitFirmware_bootnum(self, ctx:RefindConfigParser.Firmware_bootnumContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#disabled.
    def visitDisabled(self, ctx:RefindConfigParser.DisabledContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#sub_menu.
    def visitSub_menu(self, ctx:RefindConfigParser.Sub_menuContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#sub_option.
    def visitSub_option(self, ctx:RefindConfigParser.Sub_optionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#sub_initrd.
    def visitSub_initrd(self, ctx:RefindConfigParser.Sub_initrdContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#sub_boot_options.
    def visitSub_boot_options(self, ctx:RefindConfigParser.Sub_boot_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#add_boot_options.
    def visitAdd_boot_options(self, ctx:RefindConfigParser.Add_boot_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RefindConfigParser#include.
    def visitInclude(self, ctx:RefindConfigParser.IncludeContext):
        return self.visitChildren(ctx)



del RefindConfigParser