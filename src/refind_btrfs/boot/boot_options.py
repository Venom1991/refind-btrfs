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

from typing import Iterable, List, Optional, Tuple

from more_itertools import last

from refind_btrfs.common import constants
from refind_btrfs.common.exceptions import RefindConfigError
from refind_btrfs.device import BlockDevice, MountOptions, Subvolume
from refind_btrfs.utility.helpers import (
    has_items,
    is_none_or_whitespace,
    none_throws,
    replace_root_part_in,
)


class BootOptions:
    def __init__(self, raw_options: Optional[str]) -> None:
        root_location: Optional[Tuple[int, str]] = None
        root_mount_options: Optional[Tuple[int, MountOptions]] = None
        initrd_options: List[Tuple[int, str]] = []
        other_options: List[Tuple[int, str]] = []

        if not is_none_or_whitespace(raw_options):
            split_options = (
                none_throws(raw_options).strip(constants.DOUBLE_QUOTE).split()
            )

            for position, option in enumerate(split_options):
                if not is_none_or_whitespace(option):
                    if option.startswith(constants.ROOT_PREFIX):
                        normalized_option = option.removeprefix(constants.ROOT_PREFIX)

                        if root_location is not None:
                            root_option = constants.ROOT_PREFIX.rstrip(
                                constants.PARAMETERIZED_OPTION_SEPARATOR
                            )

                            raise RefindConfigError(
                                f"The '{root_option}' boot option "
                                f"cannot be defined multiple times!"
                            )

                        root_location = (position, normalized_option)
                    elif option.startswith(constants.ROOTFLAGS_PREFIX):
                        normalized_option = option.removeprefix(
                            constants.ROOTFLAGS_PREFIX
                        )

                        if root_mount_options is not None:
                            rootflags_option = constants.ROOTFLAGS_PREFIX.rstrip(
                                constants.PARAMETERIZED_OPTION_SEPARATOR
                            )

                            raise RefindConfigError(
                                f"The '{rootflags_option}' boot option "
                                f"cannot be defined multiple times!"
                            )

                        root_mount_options = (position, MountOptions(normalized_option))
                    elif option.startswith(constants.INITRD_PREFIX):
                        normalized_option = option.removeprefix(constants.INITRD_PREFIX)

                        initrd_options.append((position, normalized_option))
                    else:
                        other_options.append((position, option))

        self._root_location = root_location
        self._root_mount_options = root_mount_options
        self._initrd_options = initrd_options
        self._other_options = other_options

    def __str__(self) -> str:
        root_location = self._root_location
        root_mount_options = self._root_mount_options
        initrd_options = self._initrd_options
        other_options = self._other_options
        result: List[str] = [constants.EMPTY_STR] * (
            sum((len(initrd_options), len(other_options)))
            + (1 if root_location is not None else 0)
            + (1 if root_mount_options is not None else 0)
        )

        if root_location is not None:
            result[root_location[0]] = constants.ROOT_PREFIX + root_location[1]

        if root_mount_options is not None:
            result[root_mount_options[0]] = constants.ROOTFLAGS_PREFIX + str(
                root_mount_options[1]
            )

        if has_items(initrd_options):
            for initrd_option in initrd_options:
                result[initrd_option[0]] = constants.INITRD_PREFIX + initrd_option[1]

        if has_items(other_options):
            for other_option in other_options:
                result[other_option[0]] = other_option[1]

        if has_items(result):
            joined_options = constants.BOOT_OPTION_SEPARATOR.join(result)

            return constants.DOUBLE_QUOTE + joined_options + constants.DOUBLE_QUOTE

        return constants.EMPTY_STR

    def is_matched_with(self, block_device: BlockDevice) -> bool:
        if block_device.has_root():
            root_location = self.root_location

            if root_location is not None:
                root_partition = none_throws(block_device.root)
                filesystem = none_throws(root_partition.filesystem)
                normalized_root_location = last(
                    root_location.strip(constants.DOUBLE_QUOTE).split(
                        constants.PARAMETERIZED_OPTION_SEPARATOR
                    )
                )
                root_location_comparers = [
                    root_partition.label,
                    root_partition.uuid,
                    filesystem.label,
                    filesystem.uuid,
                ]

                if (
                    normalized_root_location in root_location_comparers
                    or block_device.is_matched_with(normalized_root_location)
                ):
                    root_mount_options = self.root_mount_options
                    subvolume = none_throws(filesystem.subvolume)

                    return (
                        root_mount_options.is_matched_with(subvolume)
                        if root_mount_options is not None
                        else False
                    )

        return False

    def migrate_from_to(
        self,
        source_subvolume: Subvolume,
        destination_subvolume: Subvolume,
        include_paths: bool,
    ) -> None:
        root_mount_options = self.root_mount_options

        if root_mount_options is not None:
            root_mount_options.migrate_from_to(source_subvolume, destination_subvolume)

        if include_paths:
            initrd_options = self._initrd_options

            if has_items(initrd_options):
                source_logical_path = source_subvolume.logical_path
                destination_logical_path = destination_subvolume.logical_path

                self._initrd_options = [
                    (
                        initrd_option[0],
                        replace_root_part_in(
                            initrd_option[1],
                            source_logical_path,
                            destination_logical_path,
                            (
                                constants.FORWARD_SLASH,
                                constants.BACKSLASH,
                            ),
                        ),
                    )
                    for initrd_option in initrd_options
                ]

    @classmethod
    def merge(cls, all_boot_options: Iterable[BootOptions]) -> BootOptions:
        all_boot_options_str = [
            str(boot_options).strip(constants.DOUBLE_QUOTE)
            for boot_options in all_boot_options
        ]

        return cls(constants.SPACE.join(all_boot_options_str).strip())

    @property
    def root_location(self) -> Optional[str]:
        root_location = self._root_location

        if root_location is not None:
            return root_location[1]

        return None

    @property
    def root_mount_options(self) -> Optional[MountOptions]:
        root_mount_options = self._root_mount_options

        if root_mount_options is not None:
            return root_mount_options[1]

        return None

    @property
    def initrd_options(self) -> List[str]:
        return [initrd_option[1] for initrd_option in self._initrd_options]

    @property
    def other_options(self) -> List[str]:
        return [other_option[1] for other_option in self._other_options]
