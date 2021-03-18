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

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, List, NamedTuple, Optional, Set
from uuid import UUID

from more_itertools import take

from refind_btrfs.common import BootFilesCheckResult, constants
from refind_btrfs.common.abc.factories import BaseDeviceCommandFactory
from refind_btrfs.common.enums import PathRelation
from refind_btrfs.common.exceptions import SubvolumeError
from refind_btrfs.utility.helpers import (
    discern_path_relation_of,
    has_items,
    is_none_or_whitespace,
    none_throws,
    replace_root_part_in,
)

if TYPE_CHECKING:
    from refind_btrfs.boot import BootStanza

    from .partition_table import PartitionTable


class NumIdRelation(NamedTuple):
    self_id: int
    parent_id: int


class UuidRelation(NamedTuple):
    self_uuid: UUID
    parent_uuid: UUID


class Subvolume:
    def __init__(
        self,
        filesystem_path: Path,
        logical_path: str,
        time_created: datetime,
        uuid_relation: UuidRelation,
        num_id_relation: NumIdRelation,
        is_read_only: bool,
    ) -> None:
        self._name: Optional[str] = None
        self._filesystem_path = filesystem_path
        self._logical_path = logical_path
        self._time_created = time_created
        self._uuid = uuid_relation.self_uuid
        self._parent_uuid = uuid_relation.parent_uuid
        self._num_id = num_id_relation.self_id
        self._parent_num_id = num_id_relation.parent_id
        self._is_read_only = is_read_only
        self._created_from: Optional[Subvolume] = None
        self._static_partition_table: Optional[PartitionTable] = None
        self._boot_files_check_result: Optional[BootFilesCheckResult] = None
        self._snapshots: Optional[Set[Subvolume]] = None

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True

        if isinstance(other, Subvolume):
            return self.uuid == other.uuid

        return False

    def __hash__(self) -> int:
        return hash(self.uuid)

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Subvolume):
            attributes_for_comparison = [
                none_throws(subvolume.created_from).time_created
                if subvolume.is_newly_created()
                else subvolume.time_created
                for subvolume in (self, other)
            ]

            return attributes_for_comparison[0] < attributes_for_comparison[1]

        return False

    def with_boot_files_check_result(self, boot_stanza: BootStanza) -> Subvolume:
        boot_stanza_check_result = boot_stanza.boot_files_check_result

        if boot_stanza_check_result is not None:
            self_filesystem_path_str = str(self.filesystem_path)
            self_logical_path = self.logical_path
            boot_stanza_name = boot_stanza_check_result.required_by_boot_stanza_name
            expected_logical_path = boot_stanza_check_result.expected_logical_path
            required_file_paths = boot_stanza_check_result.matched_boot_files
            matched_boot_files: List[str] = []
            unmatched_boot_files: List[str] = []

            for file_path in required_file_paths:
                replaced_file_path = Path(
                    replace_root_part_in(
                        file_path, expected_logical_path, self_filesystem_path_str
                    )
                )
                append_func = (
                    matched_boot_files.append
                    if replaced_file_path.exists()
                    else unmatched_boot_files.append
                )

                append_func(replaced_file_path.name)

            self._boot_files_check_result = BootFilesCheckResult(
                boot_stanza_name,
                self_logical_path,
                matched_boot_files,
                unmatched_boot_files,
            )

        return self

    def with_snapshots(self, snapshots: Iterable[Subvolume]) -> Subvolume:
        self._snapshots = set(snapshots)

        return self

    def as_named(self) -> Subvolume:
        type_prefix = "ro" if self.is_read_only else "rw"
        type_prefix += "snap" if self.is_snapshot() else "subvol"

        if self.is_newly_created():
            created_from = none_throws(self.created_from)
            time_created = created_from.time_created
            num_id = created_from.num_id
        else:
            time_created = self.time_created
            num_id = self.num_id

        formatted_time_created = time_created.strftime("%Y-%m-%d_%H-%M-%S")

        self._name = f"{type_prefix}_{formatted_time_created}_ID{num_id}"

        return self

    def as_located_in(self, parent_directory: Path) -> Subvolume:
        if not self.is_named():
            raise ValueError("The '_name' attribute must be initialized!")

        name = none_throws(self.name)

        self._filesystem_path = parent_directory / name

        return self

    def as_writable(self) -> Subvolume:
        self._is_read_only = False

        return self

    def as_newly_created_from(self, other: Subvolume) -> Subvolume:
        self._created_from = other

        if other.has_static_partition_table():
            self._static_partition_table = deepcopy(
                none_throws(other.static_partition_table)
            )

        return self

    def to_destination(self, directory: Path) -> Subvolume:
        return (
            Subvolume(
                constants.EMPTY_PATH,
                constants.EMPTY_STR,
                datetime.min,
                UuidRelation(constants.EMPTY_UUID, self.uuid),
                NumIdRelation(0, self.num_id),
                False,
            )
            .as_newly_created_from(self)
            .as_named()
            .as_located_in(directory)
        )

    def initialize_partition_table_using(
        self, device_command_factory: BaseDeviceCommandFactory
    ) -> None:
        if not self.has_static_partition_table():
            static_device_command = device_command_factory.static_device_command()

            self._static_partition_table = (
                static_device_command.get_partition_table_for(self)
            )

    def is_named(self) -> bool:
        return not is_none_or_whitespace(self.name)

    def is_snapshot(self) -> bool:
        return self.parent_uuid != constants.EMPTY_UUID

    def is_snapshot_of(self, subvolume: Subvolume) -> bool:
        return self.is_snapshot() and self.parent_uuid == subvolume.uuid

    def is_located_in(self, parent_directory: Path) -> bool:
        if self.is_newly_created():
            created_from = none_throws(self.created_from)
            filesystem_path = created_from.filesystem_path
        else:
            filesystem_path = self.filesystem_path

        path_relation = discern_path_relation_of((parent_directory, filesystem_path))
        expected_results: List[PathRelation] = [
            PathRelation.SAME,
            PathRelation.SECOND_NESTED_IN_FIRST,
        ]

        return path_relation in expected_results

    def is_newly_created(self) -> bool:
        return self.created_from is not None

    def is_static_partition_table_matched_with(self, subvolume: Subvolume) -> bool:
        if self.has_static_partition_table():
            static_partition_table = none_throws(self.static_partition_table)

            return static_partition_table.is_matched_with(subvolume)

        return False

    def has_static_partition_table(self) -> bool:
        return self.static_partition_table is not None

    def has_unmatched_boot_files(self) -> bool:
        boot_files_check_result = self.boot_files_check_result

        if boot_files_check_result is not None:
            return boot_files_check_result.has_unmatched_boot_files()

        return False

    def has_snapshots(self) -> bool:
        return has_items(self.snapshots)

    def can_be_added(self, comparison_iterable: Iterable[Subvolume]) -> bool:
        if self not in comparison_iterable:
            return not any(
                subvolume.is_newly_created() and subvolume.is_snapshot_of(self)
                for subvolume in comparison_iterable
            )

        return False

    def can_be_removed(self, comparison_iterable: Iterable[Subvolume]) -> bool:
        if self not in comparison_iterable:
            if self.is_newly_created():
                return not any(
                    self.is_snapshot_of(subvolume) for subvolume in comparison_iterable
                )

            return True

        return False

    def select_snapshots(self, count: int) -> Optional[List[Subvolume]]:
        if self.has_snapshots():
            snapshots = none_throws(self.snapshots)

            return take(count, sorted(snapshots, reverse=True))

        return None

    def modify_partition_table_using(
        self,
        source_subvolume: Subvolume,
        device_command_factory: BaseDeviceCommandFactory,
    ) -> None:
        self.initialize_partition_table_using(device_command_factory)

        static_partition_table = none_throws(self.static_partition_table)

        if not static_partition_table.is_matched_with(self):
            static_device_command = device_command_factory.static_device_command()

            static_partition_table.migrate_from_to(source_subvolume, self)
            static_device_command.save_partition_table(static_partition_table)

    def validate_static_partition_table(self, subvolume: Subvolume) -> None:
        logical_path = self.logical_path

        if not self.has_static_partition_table():
            raise SubvolumeError(
                f"The '{logical_path}' subvolume's static "
                "partition table is not initialized!"
            )

        static_partition_table = none_throws(self.static_partition_table)
        root = static_partition_table.root

        if root is None:
            raise SubvolumeError(
                f"Could not find the root partition in the '{logical_path}' "
                "subvolume's static partition table!"
            )

        if not static_partition_table.is_matched_with(subvolume):
            raise SubvolumeError(
                f"The '{logical_path}' subvolume's static partition table is not "
                "matched with the root subvolume (by 'subvol' or 'subvolid')!"
            )

    def validate_boot_files_check_result(self) -> None:
        if self.has_unmatched_boot_files():
            boot_files_check_result = none_throws(self.boot_files_check_result)
            boot_stanza_name = boot_files_check_result.required_by_boot_stanza_name
            logical_path = boot_files_check_result.expected_logical_path
            unmatched_boot_files = boot_files_check_result.unmatched_boot_files

            raise SubvolumeError(
                f"Detected boot files required by the '{boot_stanza_name}' boot "
                f"stanza which do not exist in the '{logical_path}' subvolume: "
                f"{constants.DEFAULT_ITEMS_SEPARATOR.join(unmatched_boot_files)}!"
            )

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def filesystem_path(self) -> Path:
        return self._filesystem_path

    @property
    def logical_path(self) -> str:
        return self._logical_path

    @property
    def time_created(self) -> datetime:
        return self._time_created

    @property
    def uuid(self) -> UUID:
        return self._uuid

    @property
    def parent_uuid(self) -> UUID:
        return self._parent_uuid

    @property
    def num_id(self) -> int:
        return self._num_id

    @property
    def parent_num_id(self) -> int:
        return self._parent_num_id

    @property
    def is_read_only(self) -> bool:
        return self._is_read_only

    @property
    def created_from(self) -> Optional[Subvolume]:
        return self._created_from

    @property
    def static_partition_table(self) -> Optional[PartitionTable]:
        return self._static_partition_table

    @property
    def boot_files_check_result(self) -> Optional[BootFilesCheckResult]:
        return self._boot_files_check_result

    @property
    def snapshots(self) -> Optional[Set[Subvolume]]:
        return self._snapshots
