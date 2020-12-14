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

from typing import Callable, List, NamedTuple, Optional

from more_itertools import only

from refind_btrfs.boot import RefindConfig
from refind_btrfs.common import PackageConfig, constants
from refind_btrfs.common.abc import BaseLoggerFactory, BasePackageConfigProvider
from refind_btrfs.common.exceptions import (
    UnchangedConfiguration,
    UnsupportedConfiguration,
)
from refind_btrfs.device.block_device import BlockDevice
from refind_btrfs.device.partition import Partition
from refind_btrfs.device.subvolume import SnapshotPreparationResult, Subvolume
from refind_btrfs.utility import helpers


class BlockDevices(NamedTuple):
    esp_device: Optional[BlockDevice]
    root_device: Optional[BlockDevice]
    boot_device: Optional[BlockDevice]

    @classmethod
    def empty(cls) -> BlockDevices:
        return BlockDevices(None, None, None)


class Model:
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
        package_config_provider: BasePackageConfigProvider,
    ) -> None:
        self._logger = logger_factory.logger(__name__)
        self._package_config_provider = package_config_provider
        self._refind_config: Optional[RefindConfig] = None
        self._block_devices: Optional[BlockDevices] = None
        self._snapshot_preparation_result: Optional[SnapshotPreparationResult] = None

    def check_initial_state(self) -> bool:
        return True

    def check_block_devices(self) -> bool:
        logger = self._logger
        esp_device = self.esp_device

        if esp_device is None:
            logger.error("ESP not found!")

            return False

        esp = esp_device.esp
        name = esp.name
        filesystem = esp.filesystem
        mount_point = filesystem.mount_point

        logger.info(f"Found ESP mounted at '{mount_point}' on '{name}'.")

        root_device = self.root_device

        if root_device is None:
            logger.error(f"'{mount_point}' not found!")

            return False

        root = root_device.root
        name = root.name
        filesystem = root.filesystem
        mount_point = filesystem.mount_point

        logger.info(f"Found '{mount_point}' on '{name}'.")

        btrfs_type = constants.BTRFS_TYPE

        if not filesystem.is_of_type(btrfs_type):
            logger.error(f"'{mount_point}' is not a '{btrfs_type}' partition!")

            return False

        boot_device = self.boot_device

        if boot_device is not None:
            boot = esp_device.boot
            name = boot.name
            filesystem = boot.filesystem
            mount_point = filesystem.mount_point

            logger.info(f"Found separate '{mount_point}' on '{name}'.")

        return True

    def check_btrfs_metadata(self) -> bool:
        logger = self._logger
        root_device = self.root_device
        root = root_device.root
        filesystem = root.filesystem
        mount_point = filesystem.mount_point

        if not filesystem.has_subvolume():
            logger.error(f"'{mount_point}' is not a subvolume!")

            return False

        subvolume = filesystem.subvolume
        logical_path = subvolume.logical_path

        logger.info(f"Found '{logical_path}' subvolume for '{mount_point}'.")

        if subvolume.is_snapshot():
            parent_uuid = subvolume.parent_uuid

            raise UnsupportedConfiguration(
                f"'{logical_path}' is itself a snapshot (parent UUID - '{parent_uuid}'), exiting..."
            )

        if not subvolume.has_snapshots():
            logger.error(f"Could not find snapshots of subvolume '{logical_path}'!")

            return False

        snapshots = subvolume.snapshots
        suffix = helpers.item_count_suffix(snapshots)

        logger.info(
            f"Found {len(snapshots)} snapshot{suffix} of subvolume '{logical_path}'."
        )

        return True

    def check_refind_config(self) -> bool:
        logger = self._logger
        root_device = self.root_device
        root = root_device.root
        filesystem = root.filesystem
        mount_point = filesystem.mount_point
        refind_config = self._refind_config
        matched_boot_stanzas = refind_config.find_boot_stanzas_matched_with(root)

        if not helpers.has_items(matched_boot_stanzas):
            logger.error(f"Could not find boot stanzas matched with '{mount_point}'!")

            return False

        suffix = helpers.item_count_suffix(matched_boot_stanzas)

        logger.info(
            f"Found {len(matched_boot_stanzas)} boot stanza{suffix} matched with '{mount_point}'."
        )

        return True

    def check_prepared_snapshots(self) -> bool:
        logger = self._logger
        snapshot_preparation_result = self.snapshot_preparation_result
        has_changes = snapshot_preparation_result.has_changes
        snapshots_for_addition = snapshot_preparation_result.snapshots_for_addition
        snapshots_for_removal = snapshot_preparation_result.snapshots_for_removal

        if not has_changes:
            raise UnchangedConfiguration("No changes were detected, aborting...")

        if helpers.has_items(snapshots_for_addition):
            suffix = helpers.item_count_suffix(snapshots_for_addition)

            logger.info(
                f"Found {len(snapshots_for_addition)} snapshot{suffix} for addition."
            )

        if helpers.has_items(snapshots_for_removal):
            suffix = helpers.item_count_suffix(snapshots_for_removal)

            logger.info(
                f"Found {len(snapshots_for_removal)} snapshot{suffix} for removal."
            )

        return True

    def initialize_block_devices_from(
        self, all_block_devices: List[BlockDevice]
    ) -> None:
        if helpers.has_items(all_block_devices):

            def block_device_filter(
                filter_func: Callable[[BlockDevice], bool],
            ):
                return only(
                    block_device
                    for block_device in all_block_devices
                    if filter_func(block_device)
                )

            block_devices = BlockDevices(
                block_device_filter(BlockDevice.has_esp),
                block_device_filter(BlockDevice.has_root),
                block_device_filter(BlockDevice.has_boot),
            )
        else:
            block_devices = BlockDevices.empty()

        self._block_devices = block_devices

    def should_migrate_paths_in_options(self) -> bool:
        return self.boot_device is None

    @property
    def conditions(self) -> List[str]:
        return [
            self.check_initial_state.__name__,
            self.check_block_devices.__name__,
            self.check_btrfs_metadata.__name__,
            self.check_refind_config.__name__,
            self.check_prepared_snapshots.__name__,
        ]

    @property
    def esp_device(self) -> Optional[BlockDevice]:
        return helpers.none_throws(self._block_devices).esp_device

    @property
    def esp(self) -> Partition:
        esp_device = helpers.none_throws(self.esp_device)

        return helpers.none_throws(esp_device.esp)

    @property
    def root_device(self) -> Optional[BlockDevice]:
        return helpers.none_throws(self._block_devices).root_device

    @property
    def root_partition(self) -> Partition:
        root_device = helpers.none_throws(self.root_device)

        return helpers.none_throws(root_device.root)

    @property
    def root_subvolume(self) -> Subvolume:
        root = self.root_partition
        filesystem = helpers.none_throws(root.filesystem)

        return helpers.none_throws(filesystem.subvolume)

    @property
    def boot_device(self) -> Optional[BlockDevice]:
        return helpers.none_throws(self._block_devices).boot_device

    @property
    def package_config(self) -> PackageConfig:
        package_config_provider = self._package_config_provider

        return package_config_provider.get_config()

    @property
    def refind_config(self) -> RefindConfig:
        return helpers.none_throws(self._refind_config)

    @refind_config.setter
    def refind_config(self, value: RefindConfig) -> None:
        self._refind_config = value

    @property
    def snapshot_preparation_result(self) -> SnapshotPreparationResult:
        return helpers.none_throws(self._snapshot_preparation_result)

    @snapshot_preparation_result.setter
    def snapshot_preparation_result(self, value: SnapshotPreparationResult) -> None:
        self._snapshot_preparation_result = value
