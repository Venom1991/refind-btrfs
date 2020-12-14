# region Licensing
# SPDX-FileCopyrightText: 2020 Luka Žaja <luka.zaja@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

""" refind-btrfs - Generate rEFInd manual boot stanzas from btrfs snapshots
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
"""
# endregion

from __future__ import annotations

import re
from typing import Iterable, List, Optional

from more_itertools import last

from refind_btrfs.common import constants
from refind_btrfs.common.enums import RefindOption
from refind_btrfs.device.partition import Partition
from refind_btrfs.utility import helpers

from .boot_options import BootOptions
from .sub_menu import SubMenu


class BootStanza:
    def __init__(
        self,
        name: str,
        volume: Optional[str],
        loader_path: str,
        initrd_path: Optional[str],
        icon_path: Optional[str],
        os_type: Optional[str],
        graphics: Optional[bool],
        boot_options: BootOptions,
        is_disabled: bool,
    ) -> None:
        self._name = name
        self._volume = volume
        self._loader_path = loader_path
        self._initrd_path = initrd_path
        self._icon_path = icon_path
        self._os_type = os_type
        self._graphics = graphics
        self._boot_options = boot_options
        self._is_disabled = is_disabled
        self._sub_menus: Optional[List[SubMenu]] = None

    def __str__(self) -> str:
        result: List[str] = []
        main_indent = constants.EMPTY_STR
        option_indent = constants.TAB

        name = self.name
        result.append(f"{main_indent}{RefindOption.MENU_ENTRY.value} {name} {{")

        icon_path = self.icon_path

        if not helpers.is_none_or_whitespace(icon_path):
            result.append(f"{option_indent}{RefindOption.ICON.value} {icon_path}")

        volume = self.volume

        if not helpers.is_none_or_whitespace(volume):
            result.append(f"{option_indent}{RefindOption.VOLUME.value} {volume}")

        loader_path = self._loader_path
        result.append(f"{option_indent}{RefindOption.LOADER.value} {loader_path}")

        initrd_path = self.initrd_path

        if not helpers.is_none_or_whitespace(initrd_path):
            result.append(f"{option_indent}{RefindOption.INITRD.value} {initrd_path}")

        os_type = self.os_type

        if not helpers.is_none_or_whitespace(os_type):
            result.append(f"{option_indent}{RefindOption.OS_TYPE.value} {os_type}")

        graphics = self.graphics

        if graphics is not None:
            value = "on" if graphics else "off"
            result.append(f"{option_indent}{RefindOption.GRAPHICS.value} {value}")

        boot_options_str = str(self.boot_options)

        if not helpers.is_none_or_whitespace(boot_options_str):
            result.append(
                f"{option_indent}{RefindOption.BOOT_OPTIONS.value} {boot_options_str}"
            )

        sub_menus = self.sub_menus

        if helpers.has_items(sub_menus):
            result.extend([str(sub_menu) for sub_menu in sub_menus])

        result.append(f"{main_indent}}}")

        return constants.NEWLINE.join(result)

    def with_sub_menus(self, sub_menus: Iterable[SubMenu]) -> BootStanza:
        self._sub_menus = list(sub_menus)

        return self

    def is_matched_with(self, partition: Partition) -> bool:
        is_disabled = self.is_disabled

        if is_disabled:
            return False

        volume = self.volume

        if helpers.is_none_or_whitespace(volume):
            return False

        filesystem = helpers.none_throws(partition.filesystem)
        volume_comparers = [partition.uuid, partition.label, filesystem.label]

        if volume not in volume_comparers:
            return False

        boot_options = self.boot_options
        subvolume = helpers.none_throws(filesystem.subvolume)

        return boot_options.is_matched_with(subvolume)

    @property
    def name(self) -> str:
        return self._name

    @property
    def volume(self) -> Optional[str]:
        return self._volume

    @property
    def loader_path(self) -> str:
        return self._loader_path

    @property
    def initrd_path(self) -> Optional[str]:
        return self._initrd_path

    @property
    def icon_path(self) -> Optional[str]:
        return self._icon_path

    @property
    def os_type(self) -> Optional[str]:
        return self._os_type

    @property
    def graphics(self) -> Optional[bool]:
        return self._graphics

    @property
    def boot_options(self) -> BootOptions:
        return self._boot_options

    @property
    def is_disabled(self) -> bool:
        return self._is_disabled

    @property
    def sub_menus(self) -> Optional[List[SubMenu]]:
        return self._sub_menus

    @property
    def file_name(self) -> str:
        volume = self.volume

        if not helpers.is_none_or_whitespace(volume):
            loader_path = self.loader_path
            dir_separator_pattern = re.compile(constants.DIR_SEPARATOR_PATTERN)
            split_loader_path = dir_separator_pattern.split(loader_path)
            loader = last(split_loader_path)
            extension = constants.CONFIG_FILE_EXTENSION

            return f"{volume}_{loader}{extension}".lower()

        return constants.EMPTY_STR
