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
import re
from io import TextIOWrapper
from pathlib import Path
from typing import Dict, Generator
from uuid import uuid4

from refind_btrfs.common import constants
from refind_btrfs.common.abc import BaseLoggerFactory, DeviceCommand
from refind_btrfs.common.enums import FstabColumn
from refind_btrfs.common.exceptions import PartitionError
from refind_btrfs.device.block_device import BlockDevice
from refind_btrfs.device.filesystem import Filesystem
from refind_btrfs.device.partition import Partition
from refind_btrfs.device.partition_table import PartitionTable
from refind_btrfs.device.subvolume import Subvolume
from refind_btrfs.utility import helpers


class FstabCommand(DeviceCommand):
    all_fstab_paths: Dict[PartitionTable, Path] = {}

    def __init__(self, logger_factory: BaseLoggerFactory) -> None:
        self._logger = logger_factory.logger(__name__)

    def get_block_devices(self) -> Generator[BlockDevice, None, None]:
        raise NotImplementedError(
            "Class 'FstabCommand' does not implement method 'get_block_devices'!"
        )

    def _block_device_partition_table(
        self, block_device: BlockDevice
    ) -> PartitionTable:
        raise NotImplementedError(
            "Class 'FstabCommand' does not implement method '_block_device_partition_table'!"
        )

    def save_partition_table(self, partition_table: PartitionTable) -> None:
        fstab_path = FstabCommand.all_fstab_paths.get(partition_table)

        if fstab_path is None:
            raise PartitionError(
                "The partition table must be read from the fstab file before saving it!"
            )

        logger = self._logger
        root = helpers.none_throws(partition_table.root)
        filesystem = helpers.none_throws(root.filesystem)

        try:
            logger.info(f"Writing to the '{fstab_path}' file.")

            with fileinput.input(str(fstab_path), inplace=True) as fstab_file:
                for line in fstab_file:
                    if FstabCommand._is_line_matched_with_filesystem(line, filesystem):
                        split_line = line.split()
                        current_mount_options = split_line[
                            FstabColumn.FS_MOUNT_OPTIONS.value
                        ]
                        pattern = re.compile(
                            r"(?P<whitespace_before>\s+)"
                            f"{current_mount_options}"
                            r"(?P<whitespace_after>\s+)"
                        )
                        match = pattern.search(line)

                        if not match:
                            raise PartitionError(
                                f"Could not find the root partition's expected "
                                f"mount options in the '{fstab_path}' file!"
                            )

                        modified_mount_options = str(filesystem.mount_options)
                        line = pattern.sub(
                            r"\g<whitespace_before>"
                            f"{modified_mount_options}"
                            r"\g<whitespace_after>",
                            line,
                        )

                    print(line, end=constants.EMPTY_STR)
        except OSError as e:
            logger.exception("fileinput.input() call failed!")
            raise PartitionError(f"Could not write to the '{fstab_path}' file!") from e

    def _subvolume_partition_table(self, subvolume: Subvolume) -> PartitionTable:
        filesystem_path = subvolume.filesystem_path
        fstab_path = filesystem_path / constants.FSTAB_FILE

        if not fstab_path.exists():
            raise PartitionError(f"The '{fstab_path}' file does not exist!")

        logger = self._logger
        logical_path = subvolume.logical_path

        try:
            logger.info(
                "Initializing the static partition table for "
                f"subvolume '{logical_path}' from the '{fstab_path}' file."
            )

            with fstab_path.open("r") as fstab_file:
                uuid = str(uuid4())
                partition_table = PartitionTable(
                    uuid, constants.FSTAB_PT_TYPE
                ).with_partitions(FstabCommand._map_to_partitions(fstab_file))
                root = partition_table.root

                if root is None:
                    raise PartitionError(
                        f"Could not find a mount point matched with "
                        f"the root partition in the '{fstab_path}' file!"
                    )

                FstabCommand.all_fstab_paths[partition_table] = fstab_path

                return partition_table
        except OSError as e:
            logger.exception("Path.open('r') call failed!")
            raise PartitionError(f"Could not read from the '{fstab_path}' file!") from e

    @staticmethod
    def _is_line_matched_with_filesystem(line: str, filesystem: Filesystem) -> bool:
        comment_pattern = re.compile(constants.COMMENT_PATTERN)

        if helpers.is_none_or_whitespace(line) or comment_pattern.match(line):
            return False

        split_line = line.split()
        fstab_mount_point = split_line[FstabColumn.FS_MOUNT_POINT.value]

        return fstab_mount_point == filesystem.mount_point

    @staticmethod
    def _map_to_partitions(
        fstab_file: TextIOWrapper,
    ) -> Generator[Partition, None, None]:
        comment_pattern = re.compile(constants.COMMENT_PATTERN)

        for line in fstab_file:
            if helpers.is_none_or_whitespace(line) or comment_pattern.match(line):
                continue

            split_line = line.split()
            fs_dump = helpers.try_parse_int(split_line[FstabColumn.FS_DUMP.value])
            fs_fsck = helpers.try_parse_int(split_line[FstabColumn.FS_FSCK.value])
            filesystem = (
                Filesystem(
                    constants.EMPTY_STR,
                    constants.EMPTY_STR,
                    split_line[FstabColumn.FS_TYPE.value],
                    split_line[FstabColumn.FS_MOUNT_POINT.value],
                )
                .with_dump_and_fsck(
                    helpers.default_if_none(fs_dump, 0),
                    helpers.default_if_none(fs_fsck, 0),
                )
                .with_mount_options(split_line[FstabColumn.FS_MOUNT_OPTIONS.value])
            )
            partition = Partition(
                constants.EMPTY_STR,
                split_line[FstabColumn.DEVICE_NAME.value],
                None,
            ).with_filesystem(filesystem)

            yield partition
