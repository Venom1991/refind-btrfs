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

from abc import ABC, abstractmethod
from functools import singledispatchmethod
from typing import Any, Generator

from refind_btrfs.device import BlockDevice, PartitionTable, Subvolume


class DeviceCommand(ABC):
    @abstractmethod
    def get_block_devices(self) -> Generator[BlockDevice, None, None]:
        pass

    @singledispatchmethod
    def get_partition_table_for(self, argument: Any) -> PartitionTable:
        raise NotImplementedError(
            f"Cannot get the partition table for parameter of type '{type(argument).__name__}'!"
        )

    @abstractmethod
    def save_partition_table(self, partition_table: PartitionTable) -> None:
        pass

    @get_partition_table_for.register(BlockDevice)
    def _block_device_overload(self, argument: BlockDevice) -> PartitionTable:
        return self._block_device_partition_table(argument)

    @get_partition_table_for.register(Subvolume)
    def _subvolume_overload(self, argument: Subvolume) -> PartitionTable:
        return self._subvolume_partition_table(argument)

    @abstractmethod
    def _block_device_partition_table(
        self, block_device: BlockDevice
    ) -> PartitionTable:
        pass

    @abstractmethod
    def _subvolume_partition_table(self, subvolume: Subvolume) -> PartitionTable:
        pass
