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

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, NamedTuple, Optional, Set
from uuid import UUID

from refind_btrfs.common import constants
from refind_btrfs.common.enums import PathRelation
from refind_btrfs.utility.helpers import (
    discern_path_relation_of,
    has_items,
    is_none_or_whitespace,
    none_throws,
)

if TYPE_CHECKING:
    from refind_btrfs.common.abc import DeviceCommand


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
        self._name: str = constants.EMPTY_STR
        self._filesystem_path = filesystem_path
        self._logical_path = logical_path
        self._time_created = time_created
        self._uuid = uuid_relation.self_uuid
        self._parent_uuid = uuid_relation.parent_uuid
        self._num_id = num_id_relation.self_id
        self._parent_num_id = num_id_relation.parent_id
        self._is_read_only = is_read_only
        self._created_from: Optional[Subvolume] = None
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
            return self.time_created < other.time_created

        return False

    def with_snapshots(self, snapshots: Iterable[Subvolume]) -> Subvolume:
        self._snapshots = set(snapshots)

        return self

    def named(self) -> Subvolume:
        type_prefix = "ro" if self.is_read_only else "rw"
        type_prefix += "snap" if self.is_snapshot() else "subvol"
        formatted_time_created = self.time_created.strftime("%Y-%m-%d_%H-%M-%S")

        if self.is_newly_created:
            created_from = none_throws(self._created_from)
            num_id = created_from.num_id
        else:
            num_id = self.num_id

        self._name = f"{type_prefix}_{formatted_time_created}_ID{num_id}"

        return self

    def located_in(self, parent_directory: Path):
        name = self.name

        if is_none_or_whitespace(name):
            raise ValueError("The 'name' property must be initialized beforehand!")

        self._filesystem_path = parent_directory / name

        return self

    def as_writable(self) -> Subvolume:
        self._is_read_only = False

        return self

    def as_newly_created_from(self, created_from: Subvolume) -> Subvolume:
        source_time_created = created_from.time_created

        self._time_created = source_time_created
        self._created_from = created_from

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
            .named()
            .located_in(directory)
        )

    def is_snapshot(self) -> bool:
        return self.parent_uuid != constants.EMPTY_UUID

    def is_snapshot_of(self, subvolume: Subvolume) -> bool:
        return self.is_snapshot() and self.parent_uuid == subvolume.uuid

    def has_snapshots(self) -> bool:
        return has_items(self.snapshots)

    def can_be_added(self, comparison_iterable: Iterable[Subvolume]) -> bool:
        if self not in comparison_iterable:
            return not any(
                subvolume.is_newly_created and subvolume.is_snapshot_of(self)
                for subvolume in comparison_iterable
            )

        return False

    def can_be_removed(self, comparison_iterable: Iterable[Subvolume]) -> bool:
        if self not in comparison_iterable:
            if self.is_newly_created:
                return not any(
                    self.is_snapshot_of(subvolume) for subvolume in comparison_iterable
                )

            return True

        return False

    def is_located_in(self, parent_directory: Path) -> bool:
        if self.is_newly_created:
            created_from = none_throws(self._created_from)
            filesystem_path = created_from.filesystem_path
        else:
            filesystem_path = self.filesystem_path

        path_relation = discern_path_relation_of(parent_directory, filesystem_path)
        expected_results = [PathRelation.SAME, PathRelation.SECOND_NESTED_IN_FIRST]

        return path_relation in expected_results

    def modify_partition_table_using(
        self, current_subvolume: Subvolume, device_command: DeviceCommand
    ) -> None:
        current_partition_table = device_command.get_partition_table_for(self)

        if not current_partition_table.has_been_migrated_to(self):
            replacement_partition_table = current_partition_table.as_migrated_from_to(
                current_subvolume, self
            )

            device_command.save_partition_table(replacement_partition_table)

    @property
    def name(self) -> str:
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
    def is_newly_created(self) -> bool:
        return self._created_from is not None

    @property
    def snapshots(self) -> Optional[Set[Subvolume]]:
        return self._snapshots
