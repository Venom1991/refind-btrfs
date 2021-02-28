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

import fileinput
from typing import Generator, TextIO

from refind_btrfs.common import constants
from refind_btrfs.common.abc.commands import DeviceCommand
from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.enums import FstabColumn
from refind_btrfs.common.exceptions import PartitionError
from refind_btrfs.device import (
    BlockDevice,
    Filesystem,
    Partition,
    PartitionTable,
    Subvolume,
)
from refind_btrfs.utility.helpers import (
    default_if_none,
    none_throws,
    try_parse_int,
)


class FstabCommand(DeviceCommand):
    def __init__(self, logger_factory: BaseLoggerFactory) -> None:
        self._logger = logger_factory.logger(__name__)

    def get_block_devices(self) -> Generator[BlockDevice, None, None]:
        raise NotImplementedError(
            f"Class '{FstabCommand.__name__}' does not implement the "
            f"'{DeviceCommand.get_block_devices.__name__}' method!"
        )

    def _block_device_partition_table(
        self, block_device: BlockDevice
    ) -> PartitionTable:
        raise NotImplementedError(
            f"Class '{FstabCommand.__name__}' does not implement the "
            f"'{DeviceCommand._block_device_partition_table.__name__}' method!"
        )

    def save_partition_table(self, partition_table: PartitionTable) -> None:
        logger = self._logger
        fstab_file_path = none_throws(partition_table.fstab_file_path)

        try:
            logger.info(f"Modifying the '{fstab_file_path}' file.")

            with fileinput.input(str(fstab_file_path), inplace=True) as fstab_file:
                for fstab_line in fstab_file:
                    transformed_fstab_line = partition_table.transform_fstab_line(
                        fstab_line
                    )

                    print(transformed_fstab_line, end=constants.EMPTY_STR)
        except OSError as e:
            logger.exception("fileinput.input() call failed!")
            raise PartitionError(
                f"Could not modify the '{fstab_file_path}' file!"
            ) from e

    def _subvolume_partition_table(self, subvolume: Subvolume) -> PartitionTable:
        filesystem_path = subvolume.filesystem_path
        fstab_file_path = filesystem_path / constants.FSTAB_FILE

        if not fstab_file_path.exists():
            raise PartitionError(f"The '{fstab_file_path}' file does not exist!")

        logger = self._logger
        logical_path = subvolume.logical_path

        try:
            logger.info(
                "Initializing the static partition table for "
                f"subvolume '{logical_path}' from its fstab file."
            )

            with fstab_file_path.open("r") as fstab_file:
                return (
                    PartitionTable(constants.EMPTY_HEX_UUID, constants.FSTAB_PT_TYPE)
                    .with_fstab_file_path(fstab_file_path)
                    .with_partitions(FstabCommand._map_to_partitions(fstab_file))
                )
        except OSError as e:
            logger.exception("Path.open('r') call failed!")
            raise PartitionError(
                f"Could not read from the '{fstab_file_path}' file!"
            ) from e

    @staticmethod
    def _map_to_partitions(
        fstab_file: TextIO,
    ) -> Generator[Partition, None, None]:
        for fstab_line in fstab_file:
            if PartitionTable.is_valid_fstab_entry(fstab_line):
                split_fstab_entry = fstab_line.split()
                fs_dump = try_parse_int(split_fstab_entry[FstabColumn.FS_DUMP.value])
                fs_fsck = try_parse_int(split_fstab_entry[FstabColumn.FS_FSCK.value])
                filesystem = (
                    Filesystem(
                        constants.EMPTY_STR,
                        constants.EMPTY_STR,
                        split_fstab_entry[FstabColumn.FS_TYPE.value],
                        split_fstab_entry[FstabColumn.FS_MOUNT_POINT.value],
                    )
                    .with_dump_and_fsck(
                        default_if_none(fs_dump, 0),
                        default_if_none(fs_fsck, 0),
                    )
                    .with_mount_options(
                        split_fstab_entry[FstabColumn.FS_MOUNT_OPTIONS.value]
                    )
                )
                partition = Partition(
                    constants.EMPTY_STR,
                    split_fstab_entry[FstabColumn.DEVICE_NAME.value],
                    constants.EMPTY_STR,
                ).with_filesystem(filesystem)

                yield partition
