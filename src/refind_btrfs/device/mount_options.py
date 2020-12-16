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
from typing import Dict, List, Tuple, cast

from more_itertools import first, last

from refind_btrfs.common import constants
from refind_btrfs.common.exceptions import PartitionError
from refind_btrfs.utility import helpers

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
            if not helpers.is_none_or_whitespace(option):
                if parameterized_option_prefix_pattern.match(option):
                    split_parameterized_option = option.split(
                        constants.PARAMETERIZED_OPTION_SEPARATOR
                    )
                    option_name = cast(str, first(split_parameterized_option))
                    option_value = cast(str, last(split_parameterized_option))
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

        if helpers.has_items(simple_options):
            for value in simple_options:
                position = value[0]
                option = value[1]
                result[position] = option

        if helpers.has_items(parameterized_options):
            for key, value in parameterized_options.items():
                position = value[0]
                option = value[1]
                result[position] = constants.PARAMETERIZED_OPTION_SEPARATOR.join(
                    (key, option)
                )

        if helpers.has_items(result):
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

            subvolid_matched = helpers.try_parse_int(subvolid_value) == num_id

        return subvol_matched or subvolid_matched

    def migrate_from_to(
        self, current_subvolume: Subvolume, replacement_subvolume: Subvolume
    ) -> None:
        if not self.is_matched_with(current_subvolume):
            raise PartitionError(
                "Mount options are not matched with the current subvolume!"
            )

        parameterized_options = self._parameterized_options
        subvol_tuple = parameterized_options.get(constants.SUBVOL_OPTION)
        subvolid_tuple = parameterized_options.get(constants.SUBVOLID_OPTION)

        if subvol_tuple is not None:
            subvol_value = subvol_tuple[1]
            current_logical_path = current_subvolume.logical_path
            replacement_logical_path = replacement_subvolume.logical_path
            subvol_pattern = re.compile(
                rf"(?P<prefix>^{constants.DIR_SEPARATOR_PATTERN}?){current_logical_path}$"
            )

            parameterized_options[constants.SUBVOL_OPTION] = (
                subvol_tuple[0],
                subvol_pattern.sub(
                    rf"\g<prefix>{replacement_logical_path}", subvol_value
                ),
            )

        if subvolid_tuple is not None:
            num_id = replacement_subvolume.num_id

            parameterized_options[constants.SUBVOLID_OPTION] = (
                subvolid_tuple[0],
                str(num_id),
            )

    @property
    def simple_options(self) -> List[str]:
        return [value[1] for value in self._simple_options]

    @property
    def parameterized_options(self) -> Dict[str, str]:
        return {key: value[1] for key, value in self._parameterized_options.items()}
