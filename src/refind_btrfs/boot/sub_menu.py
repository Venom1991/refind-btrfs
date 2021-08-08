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

from functools import cached_property
from typing import Generator, List, Optional, Set, Tuple

from refind_btrfs.common import constants
from refind_btrfs.common.enums import (
    BootFilePathSource,
    GraphicsParameter,
    RefindOption,
)
from refind_btrfs.device import BlockDevice
from refind_btrfs.utility.helpers import is_empty, is_none_or_whitespace, none_throws

from .boot_options import BootOptions


class SubMenu:
    def __init__(
        self,
        name: str,
        loader_path: Optional[str],
        initrd_path: Optional[str],
        graphics: Optional[bool],
        boot_options: Optional[BootOptions],
        add_boot_options: BootOptions,
        is_disabled: bool,
    ) -> None:
        self._name = name
        self._loader_path = loader_path
        self._initrd_path = initrd_path
        self._graphics = graphics
        self._boot_options = boot_options
        self._add_boot_options = add_boot_options
        self._is_disabled = is_disabled

    def __str__(self) -> str:
        main_indent = constants.TAB
        option_indent = main_indent * 2
        result: List[str] = []

        name = self.name

        result.append(f"{main_indent}{RefindOption.SUB_MENU_ENTRY.value} {name} {{")

        loader_path = self.loader_path

        if not is_none_or_whitespace(loader_path):
            result.append(f"{option_indent}{RefindOption.LOADER.value} {loader_path}")

        initrd_path = self.initrd_path

        if not is_none_or_whitespace(initrd_path):
            result.append(f"{option_indent}{RefindOption.INITRD.value} {initrd_path}")

        graphics = self.graphics

        if graphics is not None:
            value = (
                GraphicsParameter.ON.value if graphics else GraphicsParameter.OFF.value
            )
            result.append(f"{option_indent}{RefindOption.GRAPHICS.value} {value}")

        boot_options = self.boot_options

        if not boot_options is None:
            boot_options_str = str(boot_options)

            if not is_none_or_whitespace(boot_options_str):
                result.append(
                    f"{option_indent}{RefindOption.BOOT_OPTIONS.value} {boot_options_str}"
                )

        add_boot_options_str = str(self.add_boot_options)

        if not is_none_or_whitespace(add_boot_options_str):
            result.append(
                f"{option_indent}{RefindOption.ADD_BOOT_OPTIONS.value} {add_boot_options_str}"
            )

        is_disabled = self.is_disabled

        if is_disabled:
            result.append(f"{option_indent}{RefindOption.DISABLED.value}")

        result.append(f"{main_indent}}}")

        return constants.NEWLINE.join(result)

    def is_matched_with(self, block_device: BlockDevice) -> bool:
        boot_options = self.boot_options

        return (
            boot_options.is_matched_with(block_device)
            if boot_options is not None
            else False
        )

    def can_be_used_for_bootable_snapshot(self) -> bool:
        loader_path = self.loader_path
        initrd_path = self.initrd_path
        boot_options = self.boot_options
        is_disabled = self.is_disabled

        return (
            is_none_or_whitespace(loader_path)
            and (initrd_path is None or not is_empty(initrd_path))
            and boot_options is None
            and not is_disabled
        )

    def _get_all_boot_file_paths(
        self,
    ) -> Generator[Tuple[BootFilePathSource, str], None, None]:
        source = BootFilePathSource.SUB_MENU
        is_disabled = self.is_disabled

        if not is_disabled:
            loader_path = self.loader_path
            initrd_path = self.initrd_path
            boot_options = self.boot_options
            add_boot_options = self.add_boot_options

            if not is_none_or_whitespace(loader_path):
                yield (source, none_throws(loader_path))

            if not is_none_or_whitespace(initrd_path):
                yield (source, none_throws(initrd_path))

            if not boot_options is None:
                yield from (
                    (source, initrd_option)
                    for initrd_option in boot_options.initrd_options
                )

            yield from (
                (source, initrd_option)
                for initrd_option in add_boot_options.initrd_options
            )

    @property
    def name(self) -> str:
        return self._name

    @property
    def normalized_name(self) -> str:
        return self.name.strip(constants.DOUBLE_QUOTE)

    @property
    def loader_path(self) -> Optional[str]:
        return self._loader_path

    @property
    def initrd_path(self) -> Optional[str]:
        return self._initrd_path

    @property
    def graphics(self) -> Optional[bool]:
        return self._graphics

    @property
    def boot_options(self) -> Optional[BootOptions]:
        return self._boot_options

    @property
    def add_boot_options(self) -> BootOptions:
        return self._add_boot_options

    @property
    def is_disabled(self) -> bool:
        return self._is_disabled

    @cached_property
    def all_boot_file_paths(self) -> Set[Tuple[BootFilePathSource, str]]:
        return set(self._get_all_boot_file_paths())
