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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from refind_btrfs.boot import RefindConfig
    from refind_btrfs.common import PackageConfig
    from refind_btrfs.state_management.model import ProcessingResult


class BasePersistenceProvider(ABC):
    @abstractmethod
    def get_package_config(self) -> Optional[PackageConfig]:
        pass

    @abstractmethod
    def save_package_config(self, value: PackageConfig) -> None:
        pass

    @abstractmethod
    def get_refind_config(self, file_path: Path) -> Optional[RefindConfig]:
        pass

    @abstractmethod
    def save_refind_config(self, value: RefindConfig) -> None:
        pass

    @abstractmethod
    def get_previous_run_result(self) -> ProcessingResult:
        pass

    @abstractmethod
    def save_current_run_result(self, value: ProcessingResult) -> None:
        pass
