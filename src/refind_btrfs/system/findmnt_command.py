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

from more_itertools import always_iterable

from refind_btrfs.common import constants
from refind_btrfs.common.abc.commands import DeviceCommand
from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.enums import FindmntColumn, FindmntJsonKey
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


class FindmntCommand(DeviceCommand):
    def __init__(self, logger_factory: BaseLoggerFactory) -> None:
        self._logger = logger_factory.logger(__name__)

    def get_block_devices(self) -> Generator[BlockDevice, None, None]:
        raise NotImplementedError(
            f"Class '{FindmntCommand.__name__}' does not implement the "
            f"'{DeviceCommand.get_block_devices.__name__}' method!"
        )

    def save_partition_table(self, partition_table: PartitionTable) -> None:
        raise NotImplementedError(
            f"Class '{FindmntCommand.__name__}' does not implement the "
            f"'{DeviceCommand.save_partition_table.__name__}' method!"
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
                f"Initializing the live partition table for device '{device_name}' using findmnt."
            )
            logger.debug(f"Running command '{findmnt_command}'.")

            findmnt_process = subprocess.run(
                findmnt_command.split(), capture_output=True, check=True, text=True
            )
        except CalledProcessError as e:
            stderr = checked_cast(str, e.stderr)

            if is_none_or_whitespace(stderr):
                message = "findmnt execution failed!"
            else:
                message = f"findmnt execution failed: '{stderr.rstrip()}'!"

            logger.exception(message)
            raise PartitionError(
                f"Could not initialize the live partition table for '{device_name}'!"
            ) from e

        findmnt_parsed_output = json.loads(findmnt_process.stdout)
        findmnt_partitions = (
            findmnt_partition
            for findmnt_partition in always_iterable(
                findmnt_parsed_output.get(FindmntJsonKey.FILESYSTEMS.value)
            )
            if block_device.is_matched_with(
                default_if_none(
                    findmnt_partition.get(FindmntColumn.DEVICE_NAME.value),
                    constants.EMPTY_STR,
                )
            )
        )

        return PartitionTable(
            constants.EMPTY_HEX_UUID, constants.MTAB_PT_TYPE
        ).with_partitions(FindmntCommand._map_to_partitions(findmnt_partitions))

    def _subvolume_partition_table(self, subvolume: Subvolume) -> PartitionTable:
        raise NotImplementedError(
            f"Class '{FindmntCommand.__name__}' does not implement the "
            f"'{DeviceCommand._subvolume_partition_table.__name__}' method!"
        )

    @staticmethod
    def _map_to_partitions(
        findmnt_partitions: Iterable[Any],
    ) -> Generator[Partition, None, None]:
        for findmnt_partition in findmnt_partitions:
            findmnt_part_columns = [
                default_if_none(
                    findmnt_partition.get(findmnt_column_key.value), constants.EMPTY_STR
                )
                for findmnt_column_key in [
                    FindmntColumn.PART_UUID,
                    FindmntColumn.DEVICE_NAME,
                    FindmntColumn.PART_LABEL,
                ]
            ]
            findmnt_fs_columns = [
                default_if_none(
                    findmnt_partition.get(findmnt_column_key.value), constants.EMPTY_STR
                )
                for findmnt_column_key in [
                    FindmntColumn.FS_UUID,
                    FindmntColumn.FS_LABEL,
                    FindmntColumn.FS_TYPE,
                    FindmntColumn.FS_MOUNT_POINT,
                ]
            ]

            yield (
                Partition(*findmnt_part_columns).with_filesystem(
                    Filesystem(*findmnt_fs_columns).with_mount_options(
                        default_if_none(
                            findmnt_partition.get(FindmntColumn.FS_MOUNT_OPTIONS.value),
                            constants.EMPTY_STR,
                        )
                    )
                )
            )
