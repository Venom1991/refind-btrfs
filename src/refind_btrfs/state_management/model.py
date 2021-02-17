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

from itertools import groupby
from typing import Callable, Collection, Generator, List, NamedTuple, Optional

from injector import inject
from more_itertools import only, take

from refind_btrfs.boot import BootStanza, RefindConfig
from refind_btrfs.common import (
    PackageConfig,
    BootStanzaGeneration,
    constants,
)
from refind_btrfs.common.abc import (
    BaseDeviceCommandFactory,
    BaseLoggerFactory,
    BasePackageConfigProvider,
    BasePersistenceProvider,
    BaseRefindConfigProvider,
    BaseSubvolumeCommandFactory,
)
from refind_btrfs.common.exceptions import (
    UnchangedConfiguration,
    UnsupportedConfiguration,
)
from refind_btrfs.device.block_device import BlockDevice
from refind_btrfs.device.partition import Partition
from refind_btrfs.device.subvolume import Subvolume
from refind_btrfs.utility.helpers import (
    has_items,
    item_count_suffix,
    is_singleton,
    none_throws,
)


class BlockDevices(NamedTuple):
    esp_device: Optional[BlockDevice]
    root_device: Optional[BlockDevice]
    boot_device: Optional[BlockDevice]

    @classmethod
    def none(cls) -> BlockDevices:
        return BlockDevices(None, None, None)


class PreparationResult(NamedTuple):
    snapshots_for_addition: List[Subvolume]
    snapshots_for_removal: List[Subvolume]
    current_boot_stanza_generation: BootStanzaGeneration
    previous_boot_stanza_generation: Optional[BootStanzaGeneration]

    def has_changes(self) -> bool:
        return (
            has_items(self.snapshots_for_addition)
            or has_items(self.snapshots_for_removal)
        ) or (
            self.current_boot_stanza_generation != self.previous_boot_stanza_generation
        )


class ProcessingResult(NamedTuple):
    bootable_snapshots: List[Subvolume]
    boot_stanza_generation: Optional[BootStanzaGeneration]

    @classmethod
    def none(cls) -> ProcessingResult:
        return ProcessingResult([], None)


class Model:
    @inject
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
        device_command_factory: BaseDeviceCommandFactory,
        subvolume_command_factory: BaseSubvolumeCommandFactory,
        package_config_provider: BasePackageConfigProvider,
        refind_config_provider: BaseRefindConfigProvider,
        persistence_provider: BasePersistenceProvider,
    ) -> None:
        self._logger = logger_factory.logger(__name__)
        self._device_command_factory = device_command_factory
        self._subvolume_command_factory = subvolume_command_factory
        self._package_config_provider = package_config_provider
        self._refind_config_provider = refind_config_provider
        self._persistence_provider = persistence_provider
        self._block_devices: Optional[BlockDevices] = None
        self._boot_stanzas: Optional[List[BootStanza]] = None
        self._preparation_result: Optional[PreparationResult] = None

    def initialize_block_devices(self) -> None:
        all_block_devices = list(self._get_all_block_devices())

        if has_items(all_block_devices):

            def block_device_filter(
                filter_func: Callable[[BlockDevice], bool],
            ) -> Optional[BlockDevice]:
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
            block_devices = BlockDevices.none()

        self._block_devices = block_devices

    def initialize_root_subvolume(self) -> None:
        subvolume_command_factory = self._subvolume_command_factory
        root = self.root_partition
        filesystem = none_throws(root.filesystem)
        subvolume_command = subvolume_command_factory.subvolume_command()

        filesystem.initialize_subvolume_using(subvolume_command)

    def initialize_boot_stanzas(self) -> None:
        refind_config = self.refind_config
        root = self.root_partition
        matched_boot_stanzas = list(refind_config.get_boot_stanzas_matched_with(root))

        self._boot_stanzas = matched_boot_stanzas

    def initialize_preparation_result(self) -> None:
        persistence_provider = self._persistence_provider
        package_config = self.package_config
        subvolume = self.root_subvolume
        snapshot_manipulation = package_config.snapshot_manipulation
        previous_run_result = persistence_provider.get_previous_run_result()
        selected_snapshots = take(
            snapshot_manipulation.selection_count,
            sorted(none_throws(subvolume.snapshots), reverse=True),
        )
        snapshots_union = snapshot_manipulation.cleanup_exclusion.union(
            selected_snapshots
        )
        bootable_snapshots = previous_run_result.bootable_snapshots
        snapshots_for_addition = [
            snapshot
            for snapshot in selected_snapshots
            if snapshot.can_be_added(bootable_snapshots)
        ]
        snapshots_for_removal = [
            snapshot
            for snapshot in bootable_snapshots
            if snapshot.can_be_removed(snapshots_union)
        ]
        current_boot_stanza_generation = package_config.boot_stanza_generation
        previous_boot_stanza_generation = previous_run_result.boot_stanza_generation

        self._preparation_result = PreparationResult(
            snapshots_for_addition,
            snapshots_for_removal,
            current_boot_stanza_generation,
            previous_boot_stanza_generation,
        )

    def process_changes(self) -> None:
        bootable_snapshots = self._process_snapshots()

        self._process_boot_stanzas(bootable_snapshots)

        persistence_provider = self._persistence_provider
        package_config = self.package_config
        current_boot_stanza_generation = package_config.boot_stanza_generation

        persistence_provider.save_current_run_result(
            ProcessingResult(bootable_snapshots, current_boot_stanza_generation)
        )

    # region Condition Methods

    def check_initial_state(self) -> bool:
        return True

    def check_block_devices(self) -> bool:
        logger = self._logger
        esp_device = self.esp_device

        if esp_device is None:
            logger.error("Could not find the ESP!")

            return False

        esp = self.esp
        esp_filesystem = none_throws(esp.filesystem)

        logger.info(
            f"Found the ESP mounted at '{esp_filesystem.mount_point}' on '{esp.name}'."
        )

        root_device = self.root_device

        if root_device is None:
            logger.error("Could not find the root partition!")

            return False

        root = self.root_partition
        root_filesystem = none_throws(root.filesystem)

        logger.info(f"Found the root partition on '{root.name}'.")

        btrfs_type = constants.BTRFS_TYPE

        if not root_filesystem.is_of_type(btrfs_type):
            logger.error(f"The root partition's filesystem is not '{btrfs_type}'!")

            return False

        boot_device = self.boot_device

        if boot_device is not None:
            boot = none_throws(esp_device.boot)

            logger.info(f"Found a separate boot partition on '{boot.name}'.")

        return True

    def check_root_subvolume(self) -> bool:
        logger = self._logger
        root = self.root_partition
        filesystem = none_throws(root.filesystem)

        if not filesystem.has_subvolume():
            logger.error("The root partition is not mounted as a subvolume!")

            return False

        subvolume = none_throws(filesystem.subvolume)
        logical_path = subvolume.logical_path

        logger.info(f"Found subvolume '{logical_path}' mounted as the root partition.")

        if subvolume.is_snapshot():
            package_config = self.package_config

            if package_config.exit_if_root_is_snapshot:
                parent_uuid = subvolume.parent_uuid

                raise UnsupportedConfiguration(
                    f"Subvolume '{logical_path}' is itself a snapshot "
                    f"(parent UUID - '{parent_uuid}'), exiting..."
                )

        if not subvolume.has_snapshots():
            logger.error(f"No snapshots of the '{logical_path}' subvolume were found!")

            return False

        snapshots = none_throws(subvolume.snapshots)
        suffix = item_count_suffix(snapshots)

        logger.info(
            f"Found {len(snapshots)} snapshot{suffix} of the '{logical_path}' subvolume."
        )

        return True

    def check_boot_stanzas(self) -> bool:
        logger = self._logger
        boot_stanzas = self.boot_stanzas

        if not has_items(boot_stanzas):
            logger.error(
                "Could not find a boot stanza matched with the root partition!"
            )

            return False

        suffix = item_count_suffix(boot_stanzas)

        logger.info(
            f"Found {len(boot_stanzas)} boot "
            f"stanza{suffix} matched with the root partition."
        )

        grouping_result = groupby(boot_stanzas)

        for key, grouper in grouping_result:
            grouped_boot_stanzas = list(grouper)

            if not is_singleton(grouped_boot_stanzas):
                volume = key.volume
                loader_path = key.loader_path

                logger.error(
                    f"Found {len(grouped_boot_stanzas)} boot stanzas defined with "
                    f"the same volume ('{volume}') and loader ('{loader_path}') options!"
                )

                return False

        return True

    def check_preparation_result(self) -> bool:
        logger = self._logger
        preparation_result = self.preparation_result

        if not preparation_result.has_changes():
            raise UnchangedConfiguration("No changes were detected, aborting...")

        snapshots_for_addition = preparation_result.snapshots_for_addition
        snapshots_for_removal = preparation_result.snapshots_for_removal

        if has_items(snapshots_for_addition):
            suffix = item_count_suffix(snapshots_for_addition)

            logger.info(
                f"Found {len(snapshots_for_addition)} snapshot{suffix} for addition."
            )

        if has_items(snapshots_for_removal):
            suffix = item_count_suffix(snapshots_for_removal)

            logger.info(
                f"Found {len(snapshots_for_removal)} snapshot{suffix} for removal."
            )

        return True

    def check_final_state(self) -> bool:
        return True

    # endregion

    def _get_all_block_devices(self) -> Generator[BlockDevice, None, None]:
        device_command_factory = self._device_command_factory
        physical_device_command = device_command_factory.physical_device_command()
        live_device_command = device_command_factory.live_device_command()
        block_devices = physical_device_command.get_block_devices()

        for block_device in block_devices:
            physical_partition_table = physical_device_command.get_partition_table_for(
                block_device
            )
            live_partition_table = live_device_command.get_partition_table_for(
                block_device
            )

            yield block_device.with_partition_tables(
                physical_partition_table, live_partition_table
            )

    def _process_snapshots(self) -> List[Subvolume]:
        subvolume_command_factory = self._subvolume_command_factory
        persistence_provider = self._persistence_provider
        preparation_result = self.preparation_result
        subvolume_command = subvolume_command_factory.subvolume_command()
        previous_run_result = persistence_provider.get_previous_run_result()
        bootable_snapshots = previous_run_result.bootable_snapshots
        snapshots_for_addition = preparation_result.snapshots_for_addition

        if has_items(snapshots_for_addition):
            device_command_factory = self._device_command_factory
            static_device_command = device_command_factory.static_device_command()
            subvolume = self.root_subvolume

            for addition in snapshots_for_addition:
                bootable_snapshot = subvolume_command.get_bootable_snapshot_from(
                    addition
                )

                bootable_snapshot.modify_partition_table_using(
                    subvolume, static_device_command
                )

                if bootable_snapshot not in bootable_snapshots:
                    bootable_snapshots.append(bootable_snapshot)

        snapshots_for_removal = preparation_result.snapshots_for_removal

        if has_items(snapshots_for_removal):
            for removal in snapshots_for_removal:
                if removal.is_newly_created:
                    subvolume_command.delete_snapshot(removal)

                if removal in bootable_snapshots:
                    bootable_snapshots.remove(removal)

        return sorted(bootable_snapshots, reverse=True)

    def _process_boot_stanzas(self, bootable_snapshots: Collection[Subvolume]) -> None:
        refind_config = self.refind_config
        root = self.root_partition
        generated_refind_configs = refind_config.generate_new_from(
            root,
            bootable_snapshots,
            self._should_include_paths_during_generation(),
            self._should_include_sub_menus_during_generation(),
        )

        refind_config_provider = self._refind_config_provider

        for generated_refind_config in generated_refind_configs:
            refind_config_provider.save_config(generated_refind_config)

        refind_config_provider.append_to_config(refind_config)

    def _should_include_paths_during_generation(self) -> bool:
        package_config = self.package_config
        boot_stanza_generation = package_config.boot_stanza_generation

        if boot_stanza_generation.include_paths:
            return self.boot_device is None

        return False

    def _should_include_sub_menus_during_generation(self) -> bool:
        package_config = self.package_config
        boot_stanza_generation = package_config.boot_stanza_generation

        return boot_stanza_generation.include_sub_menus

    @property
    def conditions(self) -> List[str]:
        return [
            self.check_initial_state.__name__,
            self.check_block_devices.__name__,
            self.check_root_subvolume.__name__,
            self.check_boot_stanzas.__name__,
            self.check_preparation_result.__name__,
            self.check_final_state.__name__,
        ]

    @property
    def package_config(self) -> PackageConfig:
        package_config_provider = self._package_config_provider

        return package_config_provider.get_config()

    @property
    def refind_config(self) -> RefindConfig:
        refind_config_provider = self._refind_config_provider
        esp = self.esp

        return refind_config_provider.get_config(esp)

    @property
    def esp_device(self) -> Optional[BlockDevice]:
        return none_throws(self._block_devices).esp_device

    @property
    def esp(self) -> Partition:
        esp_device = none_throws(self.esp_device)

        return none_throws(esp_device.esp)

    @property
    def root_device(self) -> Optional[BlockDevice]:
        return none_throws(self._block_devices).root_device

    @property
    def root_partition(self) -> Partition:
        root_device = none_throws(self.root_device)

        return none_throws(root_device.root)

    @property
    def root_subvolume(self) -> Subvolume:
        root = self.root_partition
        filesystem = none_throws(root.filesystem)

        return none_throws(filesystem.subvolume)

    @property
    def boot_device(self) -> Optional[BlockDevice]:
        return none_throws(self._block_devices).boot_device

    @property
    def boot_stanzas(self) -> List[BootStanza]:
        return none_throws(self._boot_stanzas)

    @property
    def preparation_result(self) -> PreparationResult:
        return none_throws(self._preparation_result)
