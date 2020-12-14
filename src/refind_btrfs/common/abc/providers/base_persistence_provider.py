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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from refind_btrfs.boot import RefindConfig
from refind_btrfs.device.subvolume import Subvolume


class BasePersistenceProvider(ABC):
    @abstractmethod
    def get_refind_config(self, file_path: Path) -> Optional[RefindConfig]:
        pass

    @abstractmethod
    def save_refind_config(self, value: RefindConfig) -> None:
        pass

    @abstractmethod
    def get_bootable_snapshots(self) -> List[Subvolume]:
        pass

    @abstractmethod
    def save_bootable_snapshots(self, value: List[Subvolume]) -> None:
        pass
