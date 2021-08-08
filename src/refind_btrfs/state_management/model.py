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
from typing import Callable, Dict, List, NamedTuple, Optional

from injector import inject
from more_itertools import only

from refind_btrfs.boot import BootStanza, RefindConfig
from refind_btrfs.common import BootStanzaGeneration, PackageConfig
from refind_btrfs.common.abc.factories import (
    BaseDeviceCommandFactory,
    BaseLoggerFactory,
    BaseSubvolumeCommandFactory,
)
from refind_btrfs.common.abc.providers import (
    BasePackageConfigProvider,
    BasePersistenceProvider,
    BaseRefindConfigProvider,
)
from refind_btrfs.device import BlockDevice, Partition, Subvolume
from refind_btrfs.utility.helpers import has_items, none_throws, replace_item_in

from .conditions import Conditions

# region Helper Tuples


class BlockDevices(NamedTuple):
    esp_device: Optional[BlockDevice]
    root_device: Optional[BlockDevice]
    boot_device: Optional[BlockDevice]

    @classmethod
    def none(cls) -> BlockDevices:
        return cls(None, None, None)


class PreparedSnapshots(NamedTuple):
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


class BootStanzaWithSnapshots(NamedTuple):
    boot_stanza: BootStanza
    matched_snapshots: List[Subvolume]
    unmatched_snapshots: List[Subvolume]

    def has_matched_snapshots(self) -> bool:
        return has_items(self.matched_snapshots)

    def has_unmatched_snapshots(self) -> bool:
        return has_items(self.unmatched_snapshots)

    def replace_matched_snapshot(
        self, current_snapshot: Subvolume, replacement_snapshot: Subvolume
    ) -> None:
        matched_snapshots = self.matched_snapshots

        replace_item_in(matched_snapshots, current_snapshot, replacement_snapshot)


class ProcessingResult(NamedTuple):
    bootable_snapshots: List[Subvolume]
    boot_stanza_generation: Optional[BootStanzaGeneration]

    @classmethod
    def none(cls) -> ProcessingResult:
        return cls([], None)


# endregion


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
        self._device_command_factory = device_command_factory
        self._subvolume_command_factory = subvolume_command_factory
        self._package_config_provider = package_config_provider
        self._refind_config_provider = refind_config_provider
        self._persistence_provider = persistence_provider
        self._conditions = Conditions(logger_factory, self)
        self._filtered_block_devices: Optional[BlockDevices] = None
        self._matched_boot_stanzas: Optional[List[BootStanza]] = None
        self._prepared_snapshots: Optional[PreparedSnapshots] = None
        self._boot_stanzas_with_snapshots: Optional[
            List[BootStanzaWithSnapshots]
        ] = None

    def initialize_block_devices(self) -> None:
        device_command_factory = self._device_command_factory
        physical_device_command = device_command_factory.physical_device_command()
        all_block_devices = list(physical_device_command.get_block_devices())

        if has_items(all_block_devices):
            for block_device in all_block_devices:
                block_device.initialize_partition_tables_using(device_command_factory)

            def block_device_filter(
                filter_func: Callable[[BlockDevice], bool],
            ) -> Optional[BlockDevice]:
                return only(
                    block_device
                    for block_device in all_block_devices
                    if filter_func(block_device)
                )

            filtered_block_devices = BlockDevices(
                block_device_filter(BlockDevice.has_esp),
                block_device_filter(BlockDevice.has_root),
                block_device_filter(BlockDevice.has_boot),
            )
        else:
            filtered_block_devices = BlockDevices.none()

        self._filtered_block_devices = filtered_block_devices

    def initialize_root_subvolume(self) -> None:
        subvolume_command_factory = self._subvolume_command_factory
        root_partition = self.root_partition
        filesystem = none_throws(root_partition.filesystem)

        filesystem.initialize_subvolume_using(subvolume_command_factory)

    def initialize_matched_boot_stanzas(self) -> None:
        refind_config = self.refind_config
        include_paths = self._should_include_paths_during_generation()
        root_device = none_throws(self.root_device)
        matched_boot_stanzas = refind_config.get_boot_stanzas_matched_with(root_device)

        if include_paths:
            subvolume = self.root_subvolume
            include_sub_menus = self._should_include_sub_menus_during_generation()

            self._matched_boot_stanzas = [
                boot_stanza.with_boot_files_check_result(subvolume, include_sub_menus)
                for boot_stanza in matched_boot_stanzas
            ]
        else:
            self._matched_boot_stanzas = list(matched_boot_stanzas)

    def initialize_prepared_snapshots(self) -> None:
        persistence_provider = self._persistence_provider
        package_config = self.package_config
        subvolume = self.root_subvolume
        snapshot_manipulation = package_config.snapshot_manipulation
        previous_run_result = persistence_provider.get_previous_run_result()
        selected_snapshots = none_throws(
            subvolume.select_snapshots(snapshot_manipulation.selection_count)
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

        if has_items(snapshots_for_addition):
            device_command_factory = self._device_command_factory

            for snapshot in snapshots_for_addition:
                snapshot.initialize_partition_table_using(device_command_factory)

        current_boot_stanza_generation = package_config.boot_stanza_generation
        previous_boot_stanza_generation = previous_run_result.boot_stanza_generation

        self._prepared_snapshots = PreparedSnapshots(
            snapshots_for_addition,
            snapshots_for_removal,
            current_boot_stanza_generation,
            previous_boot_stanza_generation,
        )

    def combine_boot_stanzas_with_snapshots(self) -> None:
        usable_boot_stanzas = self.usable_boot_stanzas
        actual_bootable_snapshots = self.actual_bootable_snapshots
        include_paths = self._should_include_paths_during_generation()
        boot_stanza_preparation_results: List[BootStanzaWithSnapshots] = []

        for boot_stanza in usable_boot_stanzas:
            matched_snapshots: List[Subvolume] = []
            unmatched_snapshots: List[Subvolume] = []

            if include_paths:
                checked_bootable_snapshots = (
                    snapshot.with_boot_files_check_result(boot_stanza)
                    for snapshot in actual_bootable_snapshots
                )

                for snapshot in checked_bootable_snapshots:
                    append_func = (
                        unmatched_snapshots.append
                        if snapshot.has_unmatched_boot_files()
                        else matched_snapshots.append
                    )

                    append_func(snapshot)
            else:
                matched_snapshots.extend(actual_bootable_snapshots)

            boot_stanza_preparation_results.append(
                BootStanzaWithSnapshots(
                    boot_stanza, matched_snapshots, unmatched_snapshots
                )
            )

        self._boot_stanzas_with_snapshots = boot_stanza_preparation_results

    def process_changes(self) -> None:
        bootable_snapshots = self._process_snapshots()

        self._process_boot_stanzas()

        persistence_provider = self._persistence_provider
        package_config = self.package_config
        current_boot_stanza_generation = package_config.boot_stanza_generation

        persistence_provider.save_current_run_result(
            ProcessingResult(bootable_snapshots, current_boot_stanza_generation)
        )

    def _process_snapshots(self) -> List[Subvolume]:
        subvolume_command_factory = self._subvolume_command_factory
        actual_bootable_snapshots = self.actual_bootable_snapshots
        usable_snapshots_for_addition = self.usable_snapshots_for_addition
        subvolume_command = subvolume_command_factory.subvolume_command()

        if has_items(usable_snapshots_for_addition):
            device_command_factory = self._device_command_factory
            subvolume = self.root_subvolume
            boot_stanzas_with_snapshots = self.boot_stanzas_with_snapshots
            all_usable_snapshots = set(
                chain.from_iterable(self.usable_boot_stanzas_with_snapshots.values())
            )

            for addition in usable_snapshots_for_addition:
                if addition in all_usable_snapshots:
                    bootable_snapshot = subvolume_command.get_bootable_snapshot_from(
                        addition
                    )

                    bootable_snapshot.modify_partition_table_using(
                        subvolume, device_command_factory
                    )
                    replace_item_in(
                        actual_bootable_snapshots, addition, bootable_snapshot
                    )

                    for item in boot_stanzas_with_snapshots:
                        item.replace_matched_snapshot(addition, bootable_snapshot)
                else:
                    actual_bootable_snapshots.remove(addition)

        prepared_snapshots = self.prepared_snapshots
        snapshots_for_removal = prepared_snapshots.snapshots_for_removal

        if has_items(snapshots_for_removal):
            for removal in snapshots_for_removal:
                if removal.is_newly_created():
                    subvolume_command.delete_snapshot(removal)

        return actual_bootable_snapshots

    def _process_boot_stanzas(self) -> None:
        refind_config = self.refind_config
        root_device = none_throws(self.root_device)
        usable_boot_stanzas_with_snapshots = self.usable_boot_stanzas_with_snapshots
        include_paths = self._should_include_paths_during_generation()
        include_sub_menus = self._should_include_sub_menus_during_generation()
        generated_refind_configs = refind_config.generate_new_from(
            root_device,
            usable_boot_stanzas_with_snapshots,
            include_paths,
            include_sub_menus,
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
    def conditions(self) -> List[Callable[[], bool]]:
        conditions = self._conditions
        always_true_func = lambda: True

        return [
            always_true_func,
            conditions.check_filtered_block_devices,
            conditions.check_root_subvolume,
            conditions.check_matched_boot_stanzas,
            conditions.check_prepared_snapshots,
            conditions.check_boot_stanzas_with_snapshots,
            always_true_func,
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
        return none_throws(self._filtered_block_devices).esp_device

    @property
    def esp(self) -> Partition:
        esp_device = none_throws(self.esp_device)

        return none_throws(esp_device.esp)

    @property
    def root_device(self) -> Optional[BlockDevice]:
        return none_throws(self._filtered_block_devices).root_device

    @property
    def root_partition(self) -> Partition:
        root_device = none_throws(self.root_device)

        return none_throws(root_device.root)

    @property
    def root_subvolume(self) -> Subvolume:
        root_partition = self.root_partition
        filesystem = none_throws(root_partition.filesystem)

        return none_throws(filesystem.subvolume)

    @property
    def boot_device(self) -> Optional[BlockDevice]:
        return none_throws(self._filtered_block_devices).boot_device

    @property
    def matched_boot_stanzas(self) -> List[BootStanza]:
        return none_throws(self._matched_boot_stanzas)

    @property
    def usable_boot_stanzas(self) -> List[BootStanza]:
        matched_boot_stanzas = self.matched_boot_stanzas

        return [
            boot_stanza
            for boot_stanza in matched_boot_stanzas
            if not boot_stanza.has_unmatched_boot_files()
        ]

    @property
    def prepared_snapshots(self) -> PreparedSnapshots:
        return none_throws(self._prepared_snapshots)

    @property
    def usable_snapshots_for_addition(self) -> List[Subvolume]:
        subvolume = self.root_subvolume
        prepared_snapshots = self.prepared_snapshots
        snapshots_for_addition = prepared_snapshots.snapshots_for_addition

        return [
            snapshot
            for snapshot in snapshots_for_addition
            if snapshot.is_static_partition_table_matched_with(subvolume)
        ]

    @property
    def actual_bootable_snapshots(self) -> List[Subvolume]:
        persistence_provider = self._persistence_provider
        prepared_snapshots = self.prepared_snapshots
        usable_snapshots_for_addition = self.usable_snapshots_for_addition
        previous_run_result = persistence_provider.get_previous_run_result()
        snapshots_for_removal = prepared_snapshots.snapshots_for_removal
        bootable_snapshots = set(previous_run_result.bootable_snapshots)

        if has_items(usable_snapshots_for_addition):
            bootable_snapshots |= set(usable_snapshots_for_addition)

        if has_items(snapshots_for_removal):
            bootable_snapshots -= set(snapshots_for_removal)

        return list(bootable_snapshots)

    @property
    def boot_stanzas_with_snapshots(self) -> List[BootStanzaWithSnapshots]:
        return none_throws(self._boot_stanzas_with_snapshots)

    @property
    def usable_boot_stanzas_with_snapshots(self) -> Dict[BootStanza, List[Subvolume]]:
        boot_stanzas_with_snapshots = self.boot_stanzas_with_snapshots

        return {
            item.boot_stanza: item.matched_snapshots
            for item in boot_stanzas_with_snapshots
            if item.has_matched_snapshots()
        }
