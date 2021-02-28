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
from functools import cached_property
from pathlib import Path
from typing import Iterable, List, Optional

from more_itertools import only

from refind_btrfs.common import constants
from refind_btrfs.common.enums import FstabColumn
from refind_btrfs.utility.helpers import has_items, is_none_or_whitespace, none_throws

from .partition import Partition
from .subvolume import Subvolume


class PartitionTable:
    def __init__(self, uuid: str, pt_type: str) -> None:
        self._uuid = uuid
        self._pt_type = pt_type
        self._fstab_file_path: Optional[Path] = None
        self._partitions: Optional[List[Partition]] = None

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True

        if isinstance(other, PartitionTable):
            return self.uuid == other.uuid

        return False

    def __hash__(self) -> int:
        return hash(self.uuid)

    def with_fstab_file_path(self, fstab_file_path: Path) -> PartitionTable:
        self._fstab_file_path = fstab_file_path

        return self

    def with_partitions(self, partitions: Iterable[Partition]) -> PartitionTable:
        self._partitions = list(partitions)

        return self

    def is_matched_with(self, subvolume: Subvolume) -> bool:
        root = self.root

        if root is not None:
            filesystem = none_throws(root.filesystem)
            mount_options = none_throws(filesystem.mount_options)

            return mount_options.is_matched_with(subvolume)

        return False

    def has_partitions(self) -> bool:
        return has_items(self.partitions)

    def migrate_from_to(
        self, source_subvolume: Subvolume, destination_subvolume: Subvolume
    ) -> None:
        root = none_throws(self.root)
        filesystem = none_throws(root.filesystem)
        mount_options = none_throws(filesystem.mount_options)
        destination_filesystem_path = destination_subvolume.filesystem_path

        mount_options.migrate_from_to(source_subvolume, destination_subvolume)

        self._fstab_file_path = destination_filesystem_path / constants.FSTAB_FILE

    def transform_fstab_line(self, fstab_line: str) -> str:
        if PartitionTable.is_valid_fstab_entry(fstab_line):
            root = none_throws(self.root)
            filesystem = none_throws(root.filesystem)
            root_mount_point = filesystem.mount_point
            split_fstab_entry = fstab_line.split()
            fstab_mount_point = split_fstab_entry[FstabColumn.FS_MOUNT_POINT.value]

            if root_mount_point == fstab_mount_point:
                fstab_mount_options = split_fstab_entry[
                    FstabColumn.FS_MOUNT_OPTIONS.value
                ]
                pattern = re.compile(
                    r"(?P<whitespace_before>\s+)"
                    f"{fstab_mount_options}"
                    r"(?P<whitespace_after>\s+)"
                )
                root_mount_options = str(filesystem.mount_options)

                return pattern.sub(
                    r"\g<whitespace_before>"
                    f"{root_mount_options}"
                    r"\g<whitespace_after>",
                    fstab_line,
                )

        return fstab_line

    @staticmethod
    def is_valid_fstab_entry(value: Optional[str]) -> bool:
        if is_none_or_whitespace(value):
            return False

        fstab_line = none_throws(value)
        comment_pattern = re.compile(r"^\s*#.*")

        if not comment_pattern.match(fstab_line):
            split_fstab_entry = fstab_line.split()

            return has_items(split_fstab_entry) and len(split_fstab_entry) == len(
                FstabColumn
            )

        return False

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def pt_type(self) -> str:
        return self._pt_type

    @property
    def fstab_file_path(self) -> Optional[Path]:
        return self._fstab_file_path

    @property
    def partitions(self) -> Optional[List[Partition]]:
        return self._partitions

    @cached_property
    def esp(self) -> Optional[Partition]:
        if self.has_partitions():
            return only(
                partition
                for partition in none_throws(self.partitions)
                if partition.is_esp()
            )

        return None

    @cached_property
    def root(self) -> Optional[Partition]:
        if self.has_partitions():
            return only(
                partition
                for partition in none_throws(self.partitions)
                if partition.is_root()
            )

        return None

    @cached_property
    def boot(self) -> Optional[Partition]:
        if self.has_partitions():
            return only(
                partition
                for partition in none_throws(self.partitions)
                if partition.is_boot()
            )

        return None
