/*
SPDX-FileCopyrightText: 2020-2022 Luka Žaja <luka.zaja@protonmail.com>

SPDX-License-Identifier: GPL-3.0-or-later

refind-btrfs - Generate rEFInd manual boot stanzas from Btrfs snapshots
Copyright (C) 2020-2022 Luka Žaja

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

parser grammar RefindConfigParser;

options { tokenVocab=RefindConfigLexer; }

refind : config_option* EOF ;

config_option
    : boot_stanza
    | include
    ;

// "menuentry" section
boot_stanza : menu_entry OPEN_BRACE main_option+ CLOSE_BRACE ;

menu_entry : MENU_ENTRY STRING ;
main_option
    : volume
    | loader
    | main_initrd
    | icon
    | os_type
    | graphics
    | main_boot_options
    | firmware_bootnum
    | disabled
    | sub_menu
    ;

volume : VOLUME STRING ;
loader : LOADER STRING ;
main_initrd : INITRD STRING ;
icon : ICON STRING ;
os_type : OS_TYPE OS_TYPE_PARAMETER ;
graphics : GRAPHICS GRAPHICS_PARAMETER ;
main_boot_options : BOOT_OPTIONS STRING ;
firmware_bootnum: FIRMWARE_BOOTNUM HEX_INTEGER ;
disabled : DISABLED;

// "submenuentry" section
sub_menu : menu_entry OPEN_BRACE sub_option+ CLOSE_BRACE ;

sub_option
    : loader
    | sub_initrd
    | graphics
    | sub_boot_options
    | add_boot_options
    | disabled
    ;

sub_initrd : INITRD STRING? ;
sub_boot_options : BOOT_OPTIONS STRING? ;
add_boot_options : ADD_BOOT_OPTIONS STRING ;

// "include" section
include : INCLUDE STRING ;
