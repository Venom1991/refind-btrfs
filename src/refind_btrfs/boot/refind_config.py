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

from __future__ import annotations

from itertools import chain
from os import stat_result
from pathlib import Path
from typing import Generator, Iterable, List, Optional

from more_itertools import always_iterable

from common import constants
from common.exceptions import RefindConfigError
from device.partition import Partition
from device.subvolume import Subvolume
from utility import helpers

from .boot_stanza import BootStanza
from .migrations import Migration


class RefindConfig:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._file_stat: Optional[stat_result] = None
        self._boot_stanzas: Optional[List[BootStanza]] = None
        self._included_configs: Optional[List[RefindConfig]] = None

        self.refresh_file_stat()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RefindConfig):
            self_file_path_resolved = self.file_path.resolve()
            other_file_path_resolved = other.file_path.resolve()

            return self_file_path_resolved == other_file_path_resolved

        return False

    def with_boot_stanzas(self, boot_stanzas: Iterable[BootStanza]) -> RefindConfig:
        self._boot_stanzas = list(boot_stanzas)

        return self

    def with_included_configs(
        self, include_configs: Iterable[RefindConfig]
    ) -> RefindConfig:
        self._included_configs = list(include_configs)

        return self

    def refresh_file_stat(self):
        file_path = self.file_path

        if file_path.exists():
            self._file_stat = file_path.stat()

    def has_been_modified(self, file_path: Path) -> bool:
        if file_path.exists():
            current_file_stat = helpers.none_throws(self.file_stat)
            actual_file_stat = file_path.stat()

            return current_file_stat.st_mtime != actual_file_stat.st_mtime

        return True

    def find_boot_stanzas_matched_with(self, partition: Partition) -> List[BootStanza]:
        all_boot_stanzas = self.all_boot_stanzas

        return [
            stanza for stanza in all_boot_stanzas if stanza.is_matched_with(partition)
        ]

    def generate_new_from(
        self,
        partition: Partition,
        bootable_snapshots: List[Subvolume],
        include_paths: bool,
        include_sub_menus: bool,
    ) -> Generator[RefindConfig, None, None]:
        matched_boot_stanzas = self.find_boot_stanzas_matched_with(partition)

        if not helpers.has_items(matched_boot_stanzas):
            filesystem = helpers.none_throws(partition.filesystem)
            mount_point = filesystem.mount_point

            raise RefindConfigError(
                f"rEFInd config does not contain any boot stanzas matched with '{mount_point}'!"
            )

        file_path = self.file_path
        parent_directory = file_path.parent
        included_configs = self.included_configs

        for boot_stanza in matched_boot_stanzas:
            migration = Migration(boot_stanza, partition, bootable_snapshots)
            migrated_boot_stanza = migration.migrate(include_paths, include_sub_menus)
            boot_stanza_file_name = migrated_boot_stanza.file_name
            destination_directory = (
                parent_directory / constants.SNAPSHOT_STANZAS_CONFIG_DIR
            )
            boot_stanza_config_file_path = destination_directory / boot_stanza_file_name

            boot_stanza_config = RefindConfig(
                boot_stanza_config_file_path.resolve()
            ).with_boot_stanzas(always_iterable(migrated_boot_stanza))

            if boot_stanza_config not in included_configs:
                included_configs.append(boot_stanza_config)
            else:
                index = included_configs.index(boot_stanza_config)
                included_configs[index] = boot_stanza_config

            yield boot_stanza_config

    @property
    def file_path(self) -> Path:
        return self._file_path

    @property
    def file_stat(self) -> Optional[stat_result]:
        return self._file_stat

    @property
    def boot_stanzas(self) -> Optional[List[BootStanza]]:
        return self._boot_stanzas

    @property
    def included_configs(self) -> Optional[List[RefindConfig]]:
        return self._included_configs

    @property
    def all_boot_stanzas(self) -> List[BootStanza]:
        all_boot_stanzas: List[BootStanza] = []
        self_boot_stanzas = self.boot_stanzas
        included_configs = self.included_configs

        if helpers.has_items(self_boot_stanzas):
            all_boot_stanzas.extend(self_boot_stanzas)

        if helpers.has_items(included_configs):
            include_configs_stanzas = chain.from_iterable(
                config.boot_stanzas for config in included_configs
            )

            all_boot_stanzas.extend(list(include_configs_stanzas))

        return all_boot_stanzas
