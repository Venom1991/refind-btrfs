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

import re
from typing import Dict, List, Tuple

from refind_btrfs.common import constants
from refind_btrfs.common.exceptions import PartitionError
from refind_btrfs.utility.helpers import (
    checked_cast,
    has_items,
    is_none_or_whitespace,
    try_parse_int,
)

from .subvolume import Subvolume


class MountOptions:
    def __init__(self, raw_mount_options: str) -> None:
        split_mount_options = [
            option.strip()
            for option in raw_mount_options.split(constants.COLUMN_SEPARATOR)
        ]
        simple_options: List[Tuple[int, str]] = []
        parameterized_options: Dict[str, Tuple[int, str]] = {}
        parameterized_option_prefix_pattern = re.compile(
            constants.PARAMETERIZED_OPTION_PREFIX_PATTERN
        )

        for position, option in enumerate(split_mount_options):
            if not is_none_or_whitespace(option):
                if parameterized_option_prefix_pattern.match(option):
                    split_parameterized_option = option.split(
                        constants.PARAMETERIZED_OPTION_SEPARATOR
                    )
                    option_name = checked_cast(str, split_parameterized_option[0])
                    option_value = checked_cast(str, split_parameterized_option[1])

                    if option_name in parameterized_options:
                        raise PartitionError(
                            f"The '{option_name}' mount option "
                            f"cannot be defined multiple times!"
                        )

                    parameterized_options[option_name] = (position, option_value)
                else:
                    simple_options.append((position, option))

        self._simple_options = simple_options
        self._parameterized_options = parameterized_options

    def __str__(self) -> str:
        simple_options = self._simple_options
        parameterized_options = self._parameterized_options
        result: List[str] = [constants.EMPTY_STR] * sum(
            (len(simple_options), len(parameterized_options))
        )

        if has_items(simple_options):
            for simple_option in simple_options:
                result[simple_option[0]] = simple_option[1]

        if has_items(parameterized_options):
            for option_name, option_value in parameterized_options.items():
                result[option_value[0]] = constants.PARAMETERIZED_OPTION_SEPARATOR.join(
                    (option_name, option_value[1])
                )

        if has_items(result):
            return constants.COLUMN_SEPARATOR.join(result)

        return constants.EMPTY_STR

    def is_matched_with(self, subvolume: Subvolume) -> bool:
        parameterized_options = self._parameterized_options
        subvol_tuple = parameterized_options.get(constants.SUBVOL_OPTION)
        subvolid_tuple = parameterized_options.get(constants.SUBVOLID_OPTION)
        subvol_matched: bool = False
        subvolid_matched: bool = False

        if subvol_tuple is not None:
            subvol_value = subvol_tuple[1]
            logical_path = subvolume.logical_path
            subvol_prefix_pattern = re.compile(f"^{constants.DIR_SEPARATOR_PATTERN}")

            subvol_matched = subvol_prefix_pattern.sub(
                constants.EMPTY_STR, subvol_value
            ) == subvol_prefix_pattern.sub(constants.EMPTY_STR, logical_path)

        if subvolid_tuple is not None:
            subvolid_value = subvolid_tuple[1]
            num_id = subvolume.num_id

            subvolid_matched = try_parse_int(subvolid_value) == num_id

        return subvol_matched or subvolid_matched

    def migrate_from_to(
        self, source_subvolume: Subvolume, destination_subvolume: Subvolume
    ) -> None:
        if not self.is_matched_with(source_subvolume):
            raise PartitionError(
                "The mount options are not matched with the "
                "'source_subvolume' parameter (by 'subvol' or 'subvolid')!"
            )

        parameterized_options = self._parameterized_options
        subvol_tuple = parameterized_options.get(constants.SUBVOL_OPTION)
        subvolid_tuple = parameterized_options.get(constants.SUBVOLID_OPTION)

        if subvol_tuple is not None:
            subvol_value = subvol_tuple[1]
            source_logical_path = source_subvolume.logical_path
            destination_logical_path = destination_subvolume.logical_path
            subvol_pattern = re.compile(
                rf"(?P<prefix>^{constants.DIR_SEPARATOR_PATTERN}?){source_logical_path}$"
            )

            parameterized_options[constants.SUBVOL_OPTION] = (
                subvol_tuple[0],
                subvol_pattern.sub(
                    rf"\g<prefix>{destination_logical_path}", subvol_value
                ),
            )

        if subvolid_tuple is not None:
            num_id = destination_subvolume.num_id

            parameterized_options[constants.SUBVOLID_OPTION] = (
                subvolid_tuple[0],
                str(num_id),
            )

    @property
    def simple_options(self) -> List[str]:
        return [simple_option[1] for simple_option in self._simple_options]

    @property
    def parameterized_options(self) -> Dict[str, str]:
        return {
            option_name: option_value[1]
            for option_name, option_value in self._parameterized_options.items()
        }
