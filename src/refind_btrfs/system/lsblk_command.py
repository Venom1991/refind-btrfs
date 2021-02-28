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

import json
import subprocess
from subprocess import CalledProcessError
from typing import Any, Generator, Iterable

from more_itertools import always_iterable, one

from refind_btrfs.common import constants
from refind_btrfs.common.abc.commands import DeviceCommand
from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.enums import LsblkColumn, LsblkJsonKey
from refind_btrfs.common.exceptions import PartitionError
from refind_btrfs.device import (
    BlockDevice,
    Filesystem,
    Partition,
    PartitionTable,
    Subvolume,
)
from refind_btrfs.utility.helpers import (
    checked_cast,
    default_if_none,
    is_none_or_whitespace,
)


class LsblkCommand(DeviceCommand):
    def __init__(self, logger_factory: BaseLoggerFactory) -> None:
        self._logger = logger_factory.logger(__name__)

    def get_block_devices(self) -> Generator[BlockDevice, None, None]:
        logger = self._logger
        lsblk_columns = [
            LsblkColumn.DEVICE_NAME,
            LsblkColumn.DEVICE_TYPE,
            LsblkColumn.MAJOR_MINOR,
        ]
        output = constants.COLUMN_SEPARATOR.join(
            [lsblk_column_key.value.upper() for lsblk_column_key in lsblk_columns]
        )
        lsblk_command = f"lsblk --json --merge --paths --output {output}"

        try:
            logger.info("Initializing the block devices using lsblk.")
            logger.debug(f"Running command '{lsblk_command}'.")

            lsblk_process = subprocess.run(
                lsblk_command.split(), capture_output=True, check=True, text=True
            )
        except CalledProcessError as e:
            stderr = checked_cast(str, e.stderr)

            if is_none_or_whitespace(stderr):
                message = "lsblk execution failed!"
            else:
                message = f"lsblk execution failed: '{stderr.rstrip()}'!"

            logger.exception(message)
            raise PartitionError("Could not initialize the block devices!") from e

        lsblk_parsed_output = json.loads(lsblk_process.stdout)
        lsblk_blockdevices = always_iterable(
            lsblk_parsed_output.get(LsblkJsonKey.BLOCKDEVICES.value)
        )

        yield from LsblkCommand._map_to_block_devices(lsblk_blockdevices)

    def save_partition_table(self, partition_table: PartitionTable) -> None:
        raise NotImplementedError(
            f"Class '{LsblkCommand.__name__}' does not implement the "
            f"'{DeviceCommand.save_partition_table.__name__}' method!"
        )

    def _block_device_partition_table(
        self, block_device: BlockDevice
    ) -> PartitionTable:
        logger = self._logger
        lsblk_columns = [
            LsblkColumn.PTABLE_UUID,
            LsblkColumn.PTABLE_TYPE,
            LsblkColumn.PART_UUID,
            LsblkColumn.PART_TYPE,
            LsblkColumn.PART_LABEL,
            LsblkColumn.FS_UUID,
            LsblkColumn.DEVICE_NAME,
            LsblkColumn.FS_TYPE,
            LsblkColumn.FS_LABEL,
            LsblkColumn.FS_MOUNT_POINT,
        ]
        device_name = block_device.name
        output = constants.COLUMN_SEPARATOR.join(
            [lsblk_column_key.value.upper() for lsblk_column_key in lsblk_columns]
        )
        lsblk_command = f"lsblk {device_name} --json --paths --tree --output {output}"

        try:
            logger.info(
                f"Initializing the physical partition table for device '{device_name}' using lsblk."
            )
            logger.debug(f"Running command '{lsblk_command}'.")

            lsblk_process = subprocess.run(
                lsblk_command.split(), check=True, capture_output=True, text=True
            )
        except CalledProcessError as e:
            stderr = checked_cast(str, e.stderr)

            if is_none_or_whitespace(stderr):
                message = "lsblk execution failed!"
            else:
                message = f"lsblk execution failed: '{stderr.rstrip()}'!"

            logger.exception(message)
            raise PartitionError(
                f"Could not initialize the physical partition table for '{device_name}'!"
            ) from e

        lsblk_parsed_output = json.loads(lsblk_process.stdout)
        lsblk_blockdevice = one(
            lsblk_parsed_output.get(LsblkJsonKey.BLOCKDEVICES.value)
        )
        lsblk_partition_table_columns = [
            default_if_none(
                lsblk_blockdevice.get(lsblk_column_key.value), constants.EMPTY_STR
            )
            for lsblk_column_key in [
                LsblkColumn.PTABLE_UUID,
                LsblkColumn.PTABLE_TYPE,
            ]
        ]
        lsblk_partitions = always_iterable(
            lsblk_blockdevice.get(LsblkJsonKey.CHILDREN.value)
        )

        return PartitionTable(*lsblk_partition_table_columns).with_partitions(
            LsblkCommand._map_to_partitions(lsblk_partitions)
        )

    def _subvolume_partition_table(self, subvolume: Subvolume) -> PartitionTable:
        raise NotImplementedError(
            f"Class '{LsblkCommand.__name__}' does not implement the "
            f"'{DeviceCommand._subvolume_partition_table.__name__}' method!"
        )

    @staticmethod
    def _map_to_block_devices(
        lsblk_blockdevices: Iterable[Any],
    ) -> Generator[BlockDevice, None, None]:
        for lsblk_blockdevice in lsblk_blockdevices:
            lsblk_blockdevice_columns = [
                default_if_none(
                    lsblk_blockdevice.get(lsblk_column_key.value), constants.EMPTY_STR
                )
                for lsblk_column_key in [
                    LsblkColumn.DEVICE_NAME,
                    LsblkColumn.DEVICE_TYPE,
                    LsblkColumn.MAJOR_MINOR,
                ]
            ]
            lsblk_dependencies = always_iterable(
                lsblk_blockdevice.get(LsblkJsonKey.CHILDREN.value)
            )

            yield (
                BlockDevice(*lsblk_blockdevice_columns).with_dependencies(
                    LsblkCommand._map_to_block_devices(lsblk_dependencies)
                )
            )

    @staticmethod
    def _map_to_partitions(
        lsblk_partitions: Iterable[Any],
    ) -> Generator[Partition, None, None]:
        for lsblk_partition in lsblk_partitions:
            lsblk_part_columns = [
                default_if_none(
                    lsblk_partition.get(lsblk_column_key.value), constants.EMPTY_STR
                )
                for lsblk_column_key in [
                    LsblkColumn.PART_UUID,
                    LsblkColumn.DEVICE_NAME,
                    LsblkColumn.PART_LABEL,
                ]
            ]
            lsblk_fs_columns = [
                default_if_none(
                    lsblk_partition.get(lsblk_column_key.value), constants.EMPTY_STR
                )
                for lsblk_column_key in [
                    LsblkColumn.FS_UUID,
                    LsblkColumn.FS_LABEL,
                    LsblkColumn.FS_TYPE,
                    LsblkColumn.FS_MOUNT_POINT,
                ]
            ]

            yield (
                Partition(*lsblk_part_columns)
                .with_part_type(
                    default_if_none(
                        lsblk_partition.get(LsblkColumn.PART_TYPE.value),
                        constants.EMPTY_STR,
                    )
                )
                .with_filesystem(Filesystem(*lsblk_fs_columns))
            )

            lsblk_nested_partitions = always_iterable(
                lsblk_partition.get(LsblkJsonKey.CHILDREN.value)
            )

            yield from LsblkCommand._map_to_partitions(lsblk_nested_partitions)
