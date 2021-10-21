# region Licensing
# SPDX-FileCopyrightText: 2020-2021 Luka Žaja <luka.zaja@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

""" refind-btrfs - Generate rEFInd manual boot stanzas from Btrfs snapshots
Copyright (C) 2020-2021  Luka Žaja

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

from refind_btrfs.common import BtrfsLogo


class IconCommand(ABC):
    @abstractmethod
    def validate_custom_icon(
        self, refind_config_path: Path, source_icon_path: Path, custom_icon_path: Path
    ) -> Path:
        pass

    @abstractmethod
    def embed_btrfs_logo_into_source_icon(
        self, refind_config_path: Path, source_icon_path: Path, btrfs_logo: BtrfsLogo
    ) -> Path:
        pass
