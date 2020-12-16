/*
SPDX-FileCopyrightText: 2020 Luka Žaja <luka.zaja@protonmail.com>

SPDX-License-Identifier: GPL-3.0-or-later

refind-btrfs - Generate rEFInd manual boot stanzas from Btrfs snapshots
Copyright (C) 2020  Luka Žaja

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

lexer grammar RefindConfigLexer;

WHITESPACE : [ \t]+ -> skip ;
NEWLINE : '\r'?'\n' ->  skip ;
EMPTY : WHITESPACE? NEWLINE -> skip ;
COMMENT : '#' (~[\n])* NEWLINE? -> skip ;
IGNORED_OPTION
    : (
          'timeout'
        | 'shutdown_after_timeout'
        | 'use_nvram'
        | 'screensaver'
        | 'hideui'
        | 'icons_dir'
        | 'banner'
        | 'banner_scale'
        | 'big_icon_size'
        | 'small_icon_size'
        | 'selection_big'
        | 'selection_small'
        | 'showtools'
        | 'font'
        | 'textonly'
        | 'textmode'
        | 'resolution'
        | 'enable_touch'
        | 'enable_mouse'
        | 'mouse_size'
        | 'mouse_speed'
        | 'use_graphics_for'
        | 'scan_driver_dirs'
        | 'scanfor'
        | 'uefi_deep_legacy_scan'
        | 'scan_delay'
        | 'also_scan_dirs'
        | 'dont_scan_volumes'
        | 'don\'t_scan_volumes'
        | 'dont_scan_dirs'
        | 'don\'t_scan_dirs'
        | 'dont_scan_files'
        | 'don\'t_scan_files'
        | 'dont_scan_tools'
        | 'don\'t_scan_tools'
        | 'windows_recovery_files'
        | 'scan_all_linux_kernels'
        | 'fold_linux_kernels'
        | 'extra_kernel_version_strings'
        | 'max_tags'
        | 'default_selection'
        | 'enable_and_lock_vmx'
        | 'spoof_osx_version'
        | 'csr_values'
      ) (~[\n])* NEWLINE? -> skip ;

MENU_ENTRY : (MAIN_MENU_ENTRY | SUB_MENU_ENTRY) ;
fragment MAIN_MENU_ENTRY : 'menuentry' ;
fragment SUB_MENU_ENTRY : 'submenuentry' ;

VOLUME : 'volume' ;
LOADER : 'loader' ;
INITRD : 'initrd' ;
ICON : 'icon' ;
OS_TYPE : 'ostype' WHITESPACE -> pushMode(STRICT_PARAMETER_MODE) ;
GRAPHICS : 'graphics' WHITESPACE -> pushMode(STRICT_PARAMETER_MODE) ;
BOOT_OPTIONS : 'options' ;
ADD_BOOT_OPTIONS : 'add_options' ;
DISABLED : 'disabled' ;

INCLUDE : 'include' ;

OPEN_BRACE : '{' ;
CLOSE_BRACE : '}' ;

STRING: (QUOTED_STRING | UNQUOTED_STRING) ;
fragment QUOTED_STRING : '"' (~[\n])+ '"' ;
fragment UNQUOTED_STRING : (~[ \t\n])+ ;

mode STRICT_PARAMETER_MODE;

OS_TYPE_PARAMETER : ('MacOS' | 'Linux' | 'ELILO' | 'Windows' | 'XOM') -> popMode ;
GRAPHICS_PARAMETER : ('on' | 'off') -> popMode ;
