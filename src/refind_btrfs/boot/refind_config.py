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

from itertools import chain
from pathlib import Path
from typing import Collection, Generator, Iterable, List, Optional

from more_itertools import always_iterable

from refind_btrfs.common import constants
from refind_btrfs.common.abc import BaseConfig
from refind_btrfs.common.exceptions import RefindConfigError
from refind_btrfs.device.partition import Partition
from refind_btrfs.device.subvolume import Subvolume
from refind_btrfs.utility.helpers import has_items, is_none_or_whitespace, none_throws

from .boot_stanza import BootStanza
from .migrations import Migration


class RefindConfig(BaseConfig):
    def __init__(self, file_path: Path) -> None:
        super().__init__(file_path)

        self._boot_stanzas: Optional[List[BootStanza]] = None
        self._included_configs: Optional[List[RefindConfig]] = None

    def with_boot_stanzas(self, boot_stanzas: Iterable[BootStanza]) -> RefindConfig:
        self._boot_stanzas = list(boot_stanzas)

        return self

    def with_included_configs(
        self, include_configs: Iterable[RefindConfig]
    ) -> RefindConfig:
        self._included_configs = list(include_configs)

        return self

    def get_boot_stanzas_matched_with(
        self, partition: Partition
    ) -> Generator[BootStanza, None, None]:
        boot_stanzas = self.boot_stanzas
        included_configs = self.included_configs

        if has_items(boot_stanzas):
            yield from (
                boot_stanza
                for boot_stanza in none_throws(boot_stanzas)
                if boot_stanza.is_matched_with(partition)
            )

        if has_items(included_configs):
            yield from chain.from_iterable(
                config.get_boot_stanzas_matched_with(partition)
                for config in none_throws(included_configs)
            )

    def get_included_configs_difference_from(
        self, other: RefindConfig
    ) -> Optional[Collection[RefindConfig]]:
        if self.has_included_configs():
            self_included_configs = none_throws(self.included_configs)

            if not other.has_included_configs():
                return self_included_configs

            other_included_configs = none_throws(other.included_configs)

            return set(
                included_config
                for included_config in self_included_configs
                if included_config not in other_included_configs
            )

        return None

    def generate_new_from(
        self,
        partition: Partition,
        bootable_snapshots: Collection[Subvolume],
        include_paths: bool,
        include_sub_menus: bool,
    ) -> Generator[RefindConfig, None, None]:
        matched_boot_stanzas = list(self.get_boot_stanzas_matched_with(partition))

        if not has_items(matched_boot_stanzas):
            raise RefindConfigError(
                "rEFInd config does not contain any boot stanzas matched with the root partition!"
            )

        file_path = self.file_path
        parent_directory = file_path.parent
        included_configs: List[RefindConfig] = []

        if self.has_included_configs():
            included_configs = none_throws(self.included_configs)

        for boot_stanza in matched_boot_stanzas:
            migration = Migration(boot_stanza, partition, bootable_snapshots)
            migrated_boot_stanza = migration.migrate(include_paths, include_sub_menus)
            boot_stanza_file_name = migrated_boot_stanza.file_name

            if not is_none_or_whitespace(boot_stanza_file_name):
                destination_directory = (
                    parent_directory / constants.SNAPSHOT_STANZAS_CONFIG_DIR
                )
                boot_stanza_config_file_path = (
                    destination_directory / boot_stanza_file_name
                )
                boot_stanza_config = RefindConfig(
                    boot_stanza_config_file_path.resolve()
                ).with_boot_stanzas(always_iterable(migrated_boot_stanza))

                if boot_stanza_config not in included_configs:
                    included_configs.append(boot_stanza_config)
                else:
                    index = included_configs.index(boot_stanza_config)
                    included_configs[index] = boot_stanza_config

                yield boot_stanza_config

        self._included_configs = included_configs

    def has_included_configs(self) -> bool:
        return has_items(self.included_configs)

    @property
    def boot_stanzas(self) -> Optional[List[BootStanza]]:
        return self._boot_stanzas

    @property
    def included_configs(self) -> Optional[List[RefindConfig]]:
        return self._included_configs
