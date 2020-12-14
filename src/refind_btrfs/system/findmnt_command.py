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

import json
import subprocess
from subprocess import CalledProcessError
from typing import Any, Generator, cast

from more_itertools import always_iterable

from common import constants
from common.abc import BaseLoggerFactory, DeviceCommand
from common.enums import FindmntColumn, FindmntJsonKey
from common.exceptions import PartitionError
from device.block_device import BlockDevice
from device.filesystem import Filesystem
from device.partition import Partition
from device.partition_table import PartitionTable
from device.subvolume import Subvolume
from utility import helpers


class FindmntCommand(DeviceCommand):
    def __init__(self, logger_factory: BaseLoggerFactory) -> None:
        self._logger = logger_factory.logger(__name__)

    def get_block_devices(self) -> Generator[BlockDevice, None, None]:
        raise NotImplementedError(
            "Class 'FindmntCommand' does not implement method 'get_block_devices'!"
        )

    def save_partition_table(self, partition_table: PartitionTable) -> None:
        raise NotImplementedError(
            "Class 'FindmntCommand' does not implement method 'save_partition_table'!"
        )

    def _block_device_partition_table(
        self, block_device: BlockDevice
    ) -> PartitionTable:
        logger = self._logger
        findmnt_columns = [
            FindmntColumn.PART_UUID,
            FindmntColumn.PART_LABEL,
            FindmntColumn.FS_UUID,
            FindmntColumn.DEVICE_NAME,
            FindmntColumn.FS_TYPE,
            FindmntColumn.FS_LABEL,
            FindmntColumn.FS_MOUNT_POINT,
            FindmntColumn.FS_MOUNT_OPTIONS,
        ]
        device_name = block_device.name
        output = constants.COLUMN_SEPARATOR.join(
            [findmnt_column_key.value.upper() for findmnt_column_key in findmnt_columns]
        )
        findmnt_command = f"findmnt --json --mtab --real --nofsroot --output {output}"

        try:
            logger.info(
                f"Initializing live partition table for device '{device_name}' using findmnt."
            )
            logger.debug(f"Running command '{findmnt_command}'.")

            findmnt_process = subprocess.run(
                findmnt_command.split(), capture_output=True, check=True, text=True
            )
        except CalledProcessError as e:
            stderr = cast(str, e.stderr)

            if helpers.is_none_or_whitespace(stderr):
                message = "findmnt execution failed!"
            else:
                message = f"findmnt execution failed: '{stderr.rstrip()}'!"

            logger.exception(message)
            raise PartitionError(
                f"Could not initialize partition table for '{device_name}'!"
            ) from e

        findmnt_parsed_output = json.loads(findmnt_process.stdout)
        findmnt_partitions = always_iterable(
            findmnt_parsed_output.get(FindmntJsonKey.PARTITIONS.value)
        )

        return PartitionTable(
            constants.EMPTY_HEX_UUID, constants.MTAB_PT_TYPE
        ).with_partitions(
            FindmntCommand._map_to_partitions(findmnt_partitions, block_device.name)
        )

    def _subvolume_partition_table(self, subvolume: Subvolume) -> PartitionTable:
        raise NotImplementedError(
            "Class 'FindmntCommand' does not implement method '_subvolume_partition_table'!"
        )

    @staticmethod
    def _map_to_partitions(
        findmnt_partitions: Any, device_name: str
    ) -> Generator[Partition, None, None]:
        for findmnt_partition in findmnt_partitions:
            findmnt_part_columns = [
                findmnt_partition[findmnt_column_key.value]
                for findmnt_column_key in [
                    FindmntColumn.PART_UUID,
                    FindmntColumn.DEVICE_NAME,
                    FindmntColumn.PART_LABEL,
                ]
            ]
            findmnt_fs_columns = [
                findmnt_partition[findmnt_column_key.value]
                for findmnt_column_key in [
                    FindmntColumn.FS_UUID,
                    FindmntColumn.FS_LABEL,
                    FindmntColumn.FS_TYPE,
                    FindmntColumn.FS_MOUNT_POINT,
                ]
            ]

            partition = Partition(*findmnt_part_columns).with_filesystem(
                Filesystem(*findmnt_fs_columns).with_mount_options(
                    findmnt_partition[FindmntColumn.FS_MOUNT_OPTIONS.value]
                )
            )

            if partition.is_matched_with(device_name):
                yield partition
