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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generator, Optional

from refind_btrfs.device import Subvolume


class SubvolumeCommand(ABC):
    @abstractmethod
    def get_subvolume_from(self, filesystem_path: Path) -> Optional[Subvolume]:
        pass

    @abstractmethod
    def get_snapshots_for(self, parent: Subvolume) -> Generator[Subvolume, None, None]:
        pass

    @abstractmethod
    def get_bootable_snapshot_from(self, source: Subvolume) -> Subvolume:
        pass

    @abstractmethod
    def delete_snapshot(self, snapshot: Subvolume) -> None:
        pass
