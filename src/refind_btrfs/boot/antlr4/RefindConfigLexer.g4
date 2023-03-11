/*
SPDX-FileCopyrightText: 2020-2023 Luka Žaja <luka.zaja@protonmail.com>

SPDX-License-Identifier: GPL-3.0-or-later

refind-btrfs - Generate rEFInd manual boot stanzas from Btrfs snapshots
Copyright (C) 2020-2023 Luka Žaja

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
        | 'also_scan_dirs'
        | 'banner'
        | 'banner_scale'
        | 'big_icon_size'
        | 'csr_values'
        | 'default_selection'
        | 'don\'t_scan_dirs'
        | 'don\'t_scan_files'
        | 'don\'t_scan_firmware'
        | 'don\'t_scan_tools'
        | 'don\'t_scan_volumes'
        | 'dont_scan_dirs'
        | 'dont_scan_files'
        | 'dont_scan_firmware'
        | 'dont_scan_tools'
        | 'dont_scan_volumes'
        | 'enable_and_lock_vmx'
        | 'enable_mouse'
        | 'enable_touch'
        | 'extra_kernel_version_strings'
        | 'fold_linux_kernels'
        | 'font'
        | 'hideui'
        | 'icons_dir'
        | 'log_level'
        | 'max_tags'
        | 'mouse_size'
        | 'mouse_speed'
        | 'resolution'
        | 'scan_all_linux_kernels'
        | 'scan_delay'
        | 'scan_driver_dirs'
        | 'scanfor'
        | 'screensaver'
        | 'selection_big'
        | 'selection_small'
        | 'showtools'
        | 'shutdown_after_timeout'
        | 'small_icon_size'
        | 'spoof_osx_version'
        | 'textmode'
        | 'textonly'
        | 'uefi_deep_legacy_scan'
        | 'use_graphics_for'
        | 'use_nvram'
        | 'windows_recovery_files'
        | 'write_systemd_vars'
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
FIRMWARE_BOOTNUM : 'firmware_bootnum' ;
DISABLED : 'disabled' ;

INCLUDE : 'include' ;

OPEN_BRACE : '{' ;
CLOSE_BRACE : '}' ;

HEX_INTEGER : HEX_DIGIT+ ;
fragment HEX_DIGIT: [0-9a-fA-F] ;

STRING: (SINGLE_QUOTED_STRING | DOUBLE_QUOTED_STRING | UNQUOTED_STRING) ;
fragment SINGLE_QUOTED_STRING : '\'' (~[\n])+ '\'' ;
fragment DOUBLE_QUOTED_STRING : '"' (~[\n])+ '"' ;
fragment UNQUOTED_STRING : (~[ \t\n])+ ;

mode STRICT_PARAMETER_MODE;

OS_TYPE_PARAMETER : ('MacOS' | 'Linux' | 'ELILO' | 'Windows' | 'XOM') -> popMode ;
GRAPHICS_PARAMETER : ('on' | 'off') -> popMode ;
