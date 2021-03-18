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

import re
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Optional

from refind_btrfs.common import constants
from refind_btrfs.device import Subvolume
from refind_btrfs.utility.helpers import (
    is_none_or_whitespace,
    none_throws,
    replace_root_part_in,
)

from ..boot_options import BootOptions
from .state import State


class BaseMigrationStrategy(ABC):
    def __init__(
        self,
        current_state: State,
        source_subvolume: Subvolume,
        destination_subvolume: Subvolume,
        include_paths: bool,
        is_latest: bool,
    ) -> None:
        self._current_state = current_state
        self._source_subvolume = source_subvolume
        self._destination_subvolume = destination_subvolume
        self._include_paths = include_paths
        self._is_latest = is_latest

    @abstractmethod
    def migrate(self) -> State:
        pass

    @property
    def destination_name(self) -> str:
        destination_subvolume = self._destination_subvolume

        if not destination_subvolume.is_named():
            raise ValueError("The 'destination_subvolume' instance must be named!")

        current_name = self._current_state.name
        destination_subvolume_name = none_throws(destination_subvolume.name)
        subvolume_name_pattern = re.compile(rf"\({constants.SUBVOLUME_NAME_PATTERN}\)")
        match = subvolume_name_pattern.search(current_name)

        if match:
            destination_name = subvolume_name_pattern.sub(
                f"({destination_subvolume_name})", current_name
            )
        else:
            destination_name = f"{current_name} ({destination_subvolume_name})"

        return f"{constants.DOUBLE_QUOTE}{destination_name}{constants.DOUBLE_QUOTE}"

    @property
    def destination_loader_path(self) -> Optional[str]:
        current_loader_path = self._current_state.loader_path

        if not is_none_or_whitespace(current_loader_path):
            return replace_root_part_in(
                none_throws(current_loader_path),
                self._source_subvolume.logical_path,
                self._destination_subvolume.logical_path,
            )

        return None

    @property
    def destination_initrd_path(self) -> Optional[str]:
        current_initrd_path = self._current_state.initrd_path

        if not is_none_or_whitespace(current_initrd_path):
            return replace_root_part_in(
                none_throws(current_initrd_path),
                self._source_subvolume.logical_path,
                self._destination_subvolume.logical_path,
            )

        return None

    @property
    def destination_boot_options(self) -> Optional[BootOptions]:
        current_boot_options = self._current_state.boot_options

        if current_boot_options is not None:
            destination_boot_options = deepcopy(current_boot_options)

            destination_boot_options.migrate_from_to(
                self._source_subvolume,
                self._destination_subvolume,
                self._include_paths,
            )

            return destination_boot_options

        return None

    @property
    def destination_add_boot_options(self) -> Optional[BootOptions]:
        current_add_boot_options = self._current_state.add_boot_options

        if current_add_boot_options is not None:
            destination_add_boot_options = deepcopy(current_add_boot_options)

            destination_add_boot_options.migrate_from_to(
                self._source_subvolume,
                self._destination_subvolume,
                self._include_paths,
            )

            return destination_add_boot_options

        return None
