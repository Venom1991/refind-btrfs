# region Licensing
# SPDX-FileCopyrightText: 2020 Luka Žaja <luka.zaja@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

""" refind-btrfs - Generate rEFInd manual boot stanzas from Btrfs snapshots
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
from collections import defaultdict
from functools import cached_property
from itertools import chain
from typing import DefaultDict, Generator, Iterable, List, Optional, Set, Tuple

from more_itertools import always_iterable, last

from refind_btrfs.common import BootFilesCheckResult, constants
from refind_btrfs.common.enums import (
    BootFilePathSource,
    GraphicsParameter,
    RefindOption,
)
from refind_btrfs.common.exceptions import RefindConfigError
from refind_btrfs.device import BlockDevice, Subvolume
from refind_btrfs.utility.helpers import (
    has_items,
    is_none_or_whitespace,
    none_throws,
    normalize_dir_separators_in,
)

from .boot_options import BootOptions
from .sub_menu import SubMenu


class BootStanza:
    def __init__(
        self,
        name: str,
        volume: Optional[str],
        loader_path: Optional[str],
        initrd_path: Optional[str],
        icon_path: Optional[str],
        os_type: Optional[str],
        graphics: Optional[bool],
        boot_options: BootOptions,
        firmware_bootnum: Optional[int],
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
        self._firmware_bootnum = firmware_bootnum
        self._is_disabled = is_disabled
        self._boot_files_check_result: Optional[BootFilesCheckResult] = None
        self._sub_menus: Optional[List[SubMenu]] = None

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True

        if isinstance(other, BootStanza):
            return self.volume == other.volume and self.loader_path == other.loader_path

        return False

    def __hash__(self):
        return hash((self.volume, self.loader_path))

    def __str__(self) -> str:
        result: List[str] = []
        main_indent = constants.EMPTY_STR
        option_indent = constants.TAB

        name = self.name
        result.append(f"{main_indent}{RefindOption.MENU_ENTRY.value} {name} {{")

        icon_path = self.icon_path

        if not is_none_or_whitespace(icon_path):
            result.append(f"{option_indent}{RefindOption.ICON.value} {icon_path}")

        volume = self.volume

        if not is_none_or_whitespace(volume):
            result.append(f"{option_indent}{RefindOption.VOLUME.value} {volume}")

        loader_path = self.loader_path

        if not is_none_or_whitespace(loader_path):
            result.append(f"{option_indent}{RefindOption.LOADER.value} {loader_path}")

        initrd_path = self.initrd_path

        if not is_none_or_whitespace(initrd_path):
            result.append(f"{option_indent}{RefindOption.INITRD.value} {initrd_path}")

        os_type = self.os_type

        if not is_none_or_whitespace(os_type):
            result.append(f"{option_indent}{RefindOption.OS_TYPE.value} {os_type}")

        graphics = self.graphics

        if graphics is not None:
            graphics_parameter = (
                GraphicsParameter.ON if graphics else GraphicsParameter.OFF
            )
            result.append(
                f"{option_indent}{RefindOption.GRAPHICS.value} {graphics_parameter.value}"
            )

        boot_options_str = str(self.boot_options)

        if not is_none_or_whitespace(boot_options_str):
            result.append(
                f"{option_indent}{RefindOption.BOOT_OPTIONS.value} {boot_options_str}"
            )

        firmware_bootnum = self.firmware_bootnum

        if firmware_bootnum is not None:
            result.append(
                f"{option_indent}{RefindOption.FIRMWARE_BOOTNUM.value} {firmware_bootnum:04x}"
            )

        sub_menus = self.sub_menus

        if has_items(sub_menus):
            result.extend(str(sub_menu) for sub_menu in none_throws(sub_menus))

        is_disabled = self.is_disabled

        if is_disabled:
            result.append(f"{option_indent}{RefindOption.DISABLED.value}")

        result.append(f"{main_indent}}}")

        return constants.NEWLINE.join(result)

    def with_boot_files_check_result(
        self, subvolume: Subvolume, include_sub_menus: bool
    ) -> BootStanza:
        normalized_name = self.normalized_name
        all_boot_file_paths = self.all_boot_file_paths
        logical_path = subvolume.logical_path
        matched_boot_files: List[str] = []
        unmatched_boot_files: List[str] = []
        sources = [BootFilePathSource.BOOT_STANZA]

        if include_sub_menus:
            sources.append(BootFilePathSource.SUB_MENU)

        for source in sources:
            boot_file_paths = always_iterable(all_boot_file_paths.get(source))

            for boot_file_path in boot_file_paths:
                append_func = (
                    matched_boot_files.append
                    if logical_path in boot_file_path
                    else unmatched_boot_files.append
                )

                append_func(boot_file_path)

        self._boot_files_check_result = BootFilesCheckResult(
            normalized_name, logical_path, matched_boot_files, unmatched_boot_files
        )

        return self

    def with_sub_menus(self, sub_menus: Iterable[SubMenu]) -> BootStanza:
        self._sub_menus = list(sub_menus)

        return self

    def is_matched_with(self, block_device: BlockDevice) -> bool:
        if self.can_be_used_for_bootable_snapshot():
            boot_options = self.boot_options

            if boot_options.is_matched_with(block_device):
                return True
            else:
                sub_menus = self.sub_menus

                if has_items(sub_menus):
                    return any(
                        sub_menu.is_matched_with(block_device)
                        for sub_menu in none_throws(sub_menus)
                    )

        return False

    def has_unmatched_boot_files(self) -> bool:
        boot_files_check_result = self.boot_files_check_result

        if boot_files_check_result is not None:
            return boot_files_check_result.has_unmatched_boot_files()

        return False

    def has_sub_menus(self) -> bool:
        return has_items(self.sub_menus)

    def can_be_used_for_bootable_snapshot(self) -> bool:
        volume = self.volume
        loader_path = self.loader_path
        initrd_path = self.initrd_path
        is_disabled = self.is_disabled

        return (
            not is_none_or_whitespace(volume)
            and not is_none_or_whitespace(loader_path)
            and not is_none_or_whitespace(initrd_path)
            and not is_disabled
        )

    def validate_boot_files_check_result(self) -> None:
        if self.has_unmatched_boot_files():
            boot_files_check_result = none_throws(self.boot_files_check_result)
            boot_stanza_name = boot_files_check_result.required_by_boot_stanza_name
            logical_path = boot_files_check_result.expected_logical_path
            unmatched_boot_files = boot_files_check_result.unmatched_boot_files

            raise RefindConfigError(
                f"Detected boot files required by the '{boot_stanza_name}' boot "
                f"stanza which are not matched with the '{logical_path}' subvolume: "
                f"{constants.DEFAULT_ITEMS_SEPARATOR.join(unmatched_boot_files)}!"
            )

    def _get_all_boot_file_paths(
        self,
    ) -> Generator[Tuple[BootFilePathSource, str], None, None]:
        source = BootFilePathSource.BOOT_STANZA
        is_disabled = self.is_disabled

        if not is_disabled:
            loader_path = self.loader_path
            initrd_path = self.initrd_path
            boot_options = self.boot_options

            if not is_none_or_whitespace(loader_path):
                yield (source, none_throws(loader_path))

            if not is_none_or_whitespace(initrd_path):
                yield (source, none_throws(initrd_path))

            yield from (
                (source, initrd_option) for initrd_option in boot_options.initrd_options
            )

            sub_menus = self.sub_menus

            if has_items(sub_menus):
                yield from chain.from_iterable(
                    sub_menu.all_boot_file_paths for sub_menu in none_throws(sub_menus)
                )

    @property
    def name(self) -> str:
        return self._name

    @property
    def normalized_name(self) -> str:
        return self.name.strip(constants.DOUBLE_QUOTE)

    @property
    def volume(self) -> Optional[str]:
        return self._volume

    @property
    def normalized_volume(self) -> Optional[str]:
        volume = self.volume

        if not is_none_or_whitespace(volume):
            return none_throws(volume).strip(constants.DOUBLE_QUOTE)

        return None

    @property
    def loader_path(self) -> Optional[str]:
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
    def firmware_bootnum(self) -> Optional[int]:
        return self._firmware_bootnum

    @property
    def is_disabled(self) -> bool:
        return self._is_disabled

    @property
    def boot_files_check_result(self) -> Optional[BootFilesCheckResult]:
        return self._boot_files_check_result

    @property
    def sub_menus(self) -> Optional[List[SubMenu]]:
        return self._sub_menus

    @cached_property
    def file_name(self) -> str:
        if self.can_be_used_for_bootable_snapshot():
            normalized_volume = self.normalized_volume
            dir_separator_pattern = re.compile(constants.DIR_SEPARATOR_PATTERN)
            split_loader_path = dir_separator_pattern.split(
                none_throws(self.loader_path)
            )
            loader = last(split_loader_path)
            extension = constants.CONFIG_FILE_EXTENSION

            return f"{normalized_volume}_{loader}{extension}".lower()

        return constants.EMPTY_STR

    @cached_property
    def all_boot_file_paths(self) -> DefaultDict[BootFilePathSource, Set[str]]:
        result = defaultdict(set)
        all_boot_file_paths = self._get_all_boot_file_paths()

        for boot_file_path_tuple in all_boot_file_paths:
            key = boot_file_path_tuple[0]
            value = normalize_dir_separators_in(boot_file_path_tuple[1])

            result[key].add(value)

        return result
