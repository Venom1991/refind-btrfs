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

from pathlib import Path

from refind_btrfs.common import constants

from .partition_table import PartitionTable
from .subvolume import Subvolume


class StaticPartitionTable(PartitionTable):
    def __init__(self, fstab_file_path: Path) -> None:
        super().__init__(constants.EMPTY_HEX_UUID, constants.FSTAB_PT_TYPE)

        self._fstab_file_path = fstab_file_path

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True

        if isinstance(other, StaticPartitionTable):
            self_fstab_file_path_resolved = self.fstab_file_path.resolve()
            other_fstab_file_path_resolved = other.fstab_file_path.resolve()

            return self_fstab_file_path_resolved == other_fstab_file_path_resolved

        return False

    def __hash__(self) -> int:
        return hash(self.fstab_file_path)

    def align_with(self, subvolume: Subvolume) -> None:
        filesystem_path = subvolume.filesystem_path

        self._fstab_file_path = filesystem_path / constants.FSTAB_FILE

    @property
    def fstab_file_path(self) -> Path:
        return self._fstab_file_path
