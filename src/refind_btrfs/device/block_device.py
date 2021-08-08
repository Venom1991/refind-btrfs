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
from typing import Iterable, List, Optional, Union

from refind_btrfs.common.abc.factories import BaseDeviceCommandFactory
from refind_btrfs.utility.helpers import has_items, none_throws

from .partition import Partition
from .partition_table import PartitionTable


class BlockDevice:
    def __init__(self, name: str, d_type: str, major_minor: str) -> None:
        self._name = name
        self._d_type = d_type

        major_minor_parsed = BlockDevice.try_parse_major_minor(major_minor)

        self._major_number = major_minor_parsed[0]
        self._minor_number = major_minor_parsed[1]
        self._physical_partition_table: Optional[PartitionTable] = None
        self._live_partition_table: Optional[PartitionTable] = None
        self._dependencies: Optional[List[BlockDevice]] = None

    def with_dependencies(self, dependencies: Iterable[BlockDevice]) -> BlockDevice:
        self._dependencies = list(dependencies)

        return self

    def initialize_partition_tables_using(
        self,
        device_comand_factory: BaseDeviceCommandFactory,
    ) -> None:
        if not self.has_physical_partition_table():
            physical_device_command = device_comand_factory.physical_device_command()

            self._physical_partition_table = (
                physical_device_command.get_partition_table_for(self)
            )

        if not self.has_live_partition_table():
            live_device_command = device_comand_factory.live_device_command()

            self._live_partition_table = live_device_command.get_partition_table_for(
                self
            )

    def is_matched_with(self, name: str) -> bool:
        if self.name == name:
            return True
        else:
            dependencies = self.dependencies

            if has_items(dependencies):
                return any(
                    dependency.is_matched_with(name)
                    for dependency in none_throws(dependencies)
                )

        return False

    def has_physical_partition_table(self) -> bool:
        return self.physical_partition_table is not None

    def has_live_partition_table(self) -> bool:
        return self.live_partition_table is not None

    def has_esp(self) -> bool:
        return self.esp is not None

    def has_root(self) -> bool:
        return self.root is not None

    def has_boot(self) -> bool:
        return self.boot is not None

    @staticmethod
    def try_parse_major_minor(value: str) -> Union[List[int], List[None]]:
        match = re.fullmatch(r"\d+:\d+", value)

        if match:
            return [int(split_number) for split_number in match.group().split(":")]

        return [None, None]

    @property
    def name(self) -> str:
        return self._name

    @property
    def d_type(self) -> str:
        return self._d_type

    @property
    def major_number(self) -> Optional[int]:
        return self._major_number

    @property
    def minor_number(self) -> Optional[int]:
        return self._minor_number

    @property
    def physical_partition_table(
        self,
    ) -> Optional[PartitionTable]:
        return self._physical_partition_table

    @property
    def live_partition_table(
        self,
    ) -> Optional[PartitionTable]:
        return self._live_partition_table

    @property
    def dependencies(self) -> Optional[List[BlockDevice]]:
        return self._dependencies

    @property
    def esp(self) -> Optional[Partition]:
        if self.has_physical_partition_table():
            return none_throws(self.physical_partition_table).esp

        return None

    @property
    def root(self) -> Optional[Partition]:
        if self.has_live_partition_table():
            return none_throws(self.live_partition_table).root

        return None

    @property
    def boot(self) -> Optional[Partition]:
        if self.has_live_partition_table():
            return none_throws(self.live_partition_table).boot

        return None
