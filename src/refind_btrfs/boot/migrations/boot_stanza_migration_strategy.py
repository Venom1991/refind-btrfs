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

from refind_btrfs.common import constants
from refind_btrfs.device import Subvolume
from refind_btrfs.utility.helpers import is_none_or_whitespace, none_throws

from ..boot_stanza import BootStanza
from .base_migration_strategy import BaseMigrationStrategy
from .state import State


class BootStanzaMigrationStrategy(BaseMigrationStrategy):
    def __init__(
        self,
        boot_stanza: BootStanza,
        source_subvolume: Subvolume,
        destination_subvolume: Subvolume,
        include_paths: bool,
        is_latest: bool,
    ) -> None:
        super().__init__(
            State(
                boot_stanza.normalized_name,
                boot_stanza.loader_path,
                boot_stanza.initrd_path,
                boot_stanza.boot_options,
                None,
            ),
            source_subvolume,
            destination_subvolume,
            include_paths,
            is_latest,
        )

    def migrate(self) -> State:
        include_paths = self._include_paths
        is_latest = self._is_latest
        destination_loader_path = constants.EMPTY_STR
        destination_initrd_path = constants.EMPTY_STR

        if is_latest:
            current_state = self._current_state
            destination_loader_path = none_throws(current_state.loader_path)
            destination_initrd_path = none_throws(current_state.initrd_path)

        if include_paths:
            destination_loader_path = none_throws(self.destination_loader_path)
            destination_initrd_path_candidate = self.destination_initrd_path

            if not is_none_or_whitespace(destination_initrd_path_candidate):
                destination_initrd_path = none_throws(destination_initrd_path_candidate)

        return State(
            self.destination_name,
            destination_loader_path,
            destination_initrd_path,
            self.destination_boot_options,
            None,
        )
