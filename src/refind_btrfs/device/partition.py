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

from pathlib import Path
from typing import List, Optional
from uuid import UUID

from refind_btrfs.common import constants
from refind_btrfs.utility import helpers

from .filesystem import Filesystem


class Partition:
    def __init__(self, uuid: str, name: str, label: Optional[str]) -> None:
        self._uuid = uuid
        self._name = name
        self._label = label
        self._part_type_code: Optional[int] = None
        self._part_type_uuid: Optional[UUID] = None
        self._filesystem: Optional[Filesystem] = None

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True

        if isinstance(other, Partition):
            return self.uuid == other.uuid

        return False

    def __hash__(self) -> int:
        return hash(self.uuid)

    def with_part_type(self, part_type: str) -> Partition:
        self._part_type_code = helpers.try_parse_int(part_type, base=16)
        self._part_type_uuid = helpers.try_parse_uuid(part_type)

        return self

    def with_filesystem(self, filesystem: Filesystem) -> Partition:
        self._filesystem = filesystem

        return self

    def is_matched_with(self, device_name: str) -> bool:
        if not helpers.is_none_or_whitespace(device_name):
            return self.name.startswith(device_name)

        return False

    def is_esp(self) -> bool:
        return (
            (
                self.part_type_code == constants.ESP_PART_CODE
                or self.part_type_uuid == UUID(constants.ESP_PART_UUID)
            )
            and self.filesystem.is_mounted()
            and self.filesystem.is_of_type(constants.ESP_FS_TYPE)
        )

    def is_root(self) -> bool:
        directory = constants.ROOT_DIR

        return self.filesystem.is_mounted_at(directory)

    def is_boot(self) -> bool:
        directory = constants.ROOT_DIR / constants.BOOT_DIR

        return self.filesystem.is_mounted_at(directory)

    def search_paths_for(self, file_name: str) -> Optional[List[Path]]:
        if helpers.is_none_or_whitespace(file_name):
            raise ValueError("The 'file_name' parameter must be initialized!")

        filesystem = helpers.none_throws(self.filesystem)

        if filesystem.is_mounted():
            search_directory = Path(filesystem.mount_point)
            all_matches = helpers.find_all_matched_files_in(search_directory, file_name)

            return list(all_matches)

        return None

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def part_type_code(self) -> Optional[int]:
        return self._part_type_code

    @property
    def part_type_uuid(self) -> Optional[UUID]:
        return self._part_type_uuid

    @property
    def name(self) -> str:
        return self._name

    @property
    def label(self) -> Optional[str]:
        return self._label

    @property
    def filesystem(self) -> Optional[Filesystem]:
        return self._filesystem
