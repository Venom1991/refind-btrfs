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

from typing import Collection, Generator, List, Optional

from more_itertools import first

from refind_btrfs.common import constants
from refind_btrfs.common.exceptions import RefindConfigError
from refind_btrfs.device import BlockDevice, Subvolume
from refind_btrfs.utility.helpers import has_items, none_throws

from ..boot_options import BootOptions
from ..boot_stanza import BootStanza
from ..sub_menu import SubMenu
from .factory import Factory
from .state import State


class Migration:
    def __init__(
        self,
        boot_stanza: BootStanza,
        block_device: BlockDevice,
        bootable_snapshots: Collection[Subvolume],
    ) -> None:
        assert has_items(
            bootable_snapshots
        ), "Parameter 'bootable_snapshots' must contain at least one item!"

        if not boot_stanza.is_matched_with(block_device):
            raise RefindConfigError("Boot stanza is not matched with the partition!")

        root_partition = none_throws(block_device.root)
        filesystem = none_throws(root_partition.filesystem)
        source_subvolume = none_throws(filesystem.subvolume)

        self._boot_stanza = boot_stanza
        self._source_subvolume = source_subvolume
        self._bootable_snapshots = list(bootable_snapshots)

    def migrate(self, include_paths: bool, include_sub_menus: bool) -> BootStanza:
        boot_stanza = self._boot_stanza
        source_subvolume = self._source_subvolume
        bootable_snapshots = self._bootable_snapshots
        latest_migration_result: Optional[State] = None
        result_sub_menus: List[SubMenu] = []

        for destination_subvolume in bootable_snapshots:
            is_latest = self._is_latest_snapshot(destination_subvolume)
            migration_strategy = Factory.migration_strategy(
                boot_stanza,
                source_subvolume,
                destination_subvolume,
                include_paths,
                is_latest,
            )
            migration_result = migration_strategy.migrate()

            if is_latest:
                latest_migration_result = migration_result
            else:
                result_sub_menus.append(
                    SubMenu(
                        migration_result.name,
                        migration_result.loader_path,
                        migration_result.initrd_path,
                        boot_stanza.graphics,
                        migration_result.boot_options,
                        BootOptions(constants.EMPTY_STR),
                        boot_stanza.is_disabled,
                    )
                )

            if include_sub_menus:
                migrated_sub_menus = self._migrate_sub_menus(
                    source_subvolume,
                    destination_subvolume,
                    migration_result,
                    include_paths,
                )

                result_sub_menus.extend(list(migrated_sub_menus))

        boot_stanza_migration_result = none_throws(latest_migration_result)

        return BootStanza(
            boot_stanza_migration_result.name,
            boot_stanza.volume,
            boot_stanza_migration_result.loader_path,
            boot_stanza_migration_result.initrd_path,
            boot_stanza.icon_path,
            boot_stanza.os_type,
            boot_stanza.graphics,
            none_throws(boot_stanza_migration_result.boot_options),
            boot_stanza.firmware_bootnum,
            boot_stanza.is_disabled,
        ).with_sub_menus(result_sub_menus)

    def _migrate_sub_menus(
        self,
        source_subvolume: Subvolume,
        destination_subvolume: Subvolume,
        boot_stanza_result: State,
        include_paths: bool,
    ) -> Generator[SubMenu, None, None]:
        boot_stanza = self._boot_stanza

        if not boot_stanza.has_sub_menus():
            return

        current_sub_menus = none_throws(boot_stanza.sub_menus)
        is_latest = self._is_latest_snapshot(destination_subvolume)

        for sub_menu in current_sub_menus:
            if sub_menu.can_be_used_for_bootable_snapshot():
                migration_strategy = Factory.migration_strategy(
                    sub_menu,
                    source_subvolume,
                    destination_subvolume,
                    include_paths,
                    is_latest,
                    boot_stanza_result,
                )
                migration_result = migration_strategy.migrate()

                yield SubMenu(
                    migration_result.name,
                    migration_result.loader_path,
                    migration_result.initrd_path,
                    sub_menu.graphics,
                    migration_result.boot_options,
                    none_throws(migration_result.add_boot_options),
                    sub_menu.is_disabled,
                )

    def _is_latest_snapshot(self, snapshot: Subvolume) -> bool:
        bootable_snapshots = self._bootable_snapshots
        latest_snapshot = first(bootable_snapshots)

        return snapshot == latest_snapshot
