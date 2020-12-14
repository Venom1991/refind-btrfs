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

from pathlib import Path
from typing import Generator, List, NamedTuple, Set

from device.subvolume import Subvolume
from utility import helpers


class SnapshotSearch(NamedTuple):
    directory: Path
    is_nested: bool
    max_depth: int

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SnapshotSearch):
            self_directory_resolved = self.directory.resolve()
            other_directory_resolved = other.directory.resolve()

            return self_directory_resolved == other_directory_resolved

        return False


class SnapshotManipulation(NamedTuple):
    refind_config: str
    count: int
    include_sub_menus: bool
    modify_read_only_flag: bool
    destination_directory: Path
    cleanup_exclusion: Set[Subvolume]


class PackageConfig:
    def __init__(
        self,
        snapshot_searches: List[SnapshotSearch],
        snapshot_manipulation: SnapshotManipulation,
    ) -> None:
        self._snapshot_searches = snapshot_searches
        self._snapshot_manipulation = snapshot_manipulation

    def get_directories_for_watch(self) -> Generator[Path, None, None]:
        snapshot_searches = self.snapshot_searches

        for snapshot_search in snapshot_searches:
            directory = snapshot_search.directory
            max_depth = snapshot_search.max_depth - 1

            yield from helpers.find_all_directories_in(directory, max_depth)

    @property
    def snapshot_searches(self) -> List[SnapshotSearch]:
        return self._snapshot_searches

    @property
    def snapshot_manipulation(self) -> SnapshotManipulation:
        return self._snapshot_manipulation
