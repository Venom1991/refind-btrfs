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

from typing import Generator, cast

from more_itertools import take
from transitions import EventData, State

from refind_btrfs.common.abc import (
    BaseDeviceCommandFactory,
    BasePersistenceProvider,
    BaseRefindConfigProvider,
    BaseSubvolumeCommandFactory,
)
from refind_btrfs.common.enums import States
from refind_btrfs.device.block_device import BlockDevice
from refind_btrfs.utility import helpers

from .model import Model, ProcessingResult


class InitBlockDevicesState(State):
    def __init__(self, device_command_factory: BaseDeviceCommandFactory):
        super().__init__(States.INIT_BLOCK_DEVICES.value)

        self._device_command_factory = device_command_factory

    def enter(self, event_data: EventData) -> None:
        model = cast(Model, event_data.model)

        all_block_devices = list(self._get_all_block_devices())

        model.initialize_block_devices_from(all_block_devices)

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


class InitBtrfsMetadataState(State):
    def __init__(self, subvolume_command_factory: BaseSubvolumeCommandFactory):
        super().__init__(States.INIT_BTRFS_METADATA.value)

        self._subvolume_command_factory = subvolume_command_factory

    def enter(self, event_data: EventData) -> None:
        model = cast(Model, event_data.model)
        subvolume_command = self._subvolume_command_factory.subvolume_command()
        root_device = model.root_device
        root = root_device.root
        filesystem = root.filesystem

        filesystem.initialize_subvolume_using(subvolume_command)


class InitRefindConfigState(State):
    def __init__(self, refind_config_provider: BaseRefindConfigProvider):
        super().__init__(States.INIT_REFIND_CONFIG.value)

        self._refind_config_provider = refind_config_provider

    def enter(self, event_data: EventData) -> None:
        model = cast(Model, event_data.model)
        refind_config_provider = self._refind_config_provider
        esp = model.esp

        model.refind_config = refind_config_provider.get_config(esp)


class PrepareSnapshotsState(State):
    def __init__(self, persistence_provider: BasePersistenceProvider):
        super().__init__(States.PREPARE_SNAPSHOTS.value)

        self._persistence_provider = persistence_provider

    def enter(self, event_data: EventData) -> None:
        model = cast(Model, event_data.model)
        persistence_provider = self._persistence_provider
        package_config = model.package_config
        subvolume = model.root_subvolume
        snapshot_manipulation = package_config.snapshot_manipulation
        previous_run_result = persistence_provider.get_previous_run_result()
        bootable_snapshots = previous_run_result.bootable_snapshots
        selected_snapshots = take(
            snapshot_manipulation.count,
            sorted(helpers.none_throws(subvolume.snapshots), reverse=True),
        )
        snapshots_union = snapshot_manipulation.cleanup_exclusion.union(
            selected_snapshots
        )
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

        model.initialize_preparation_result_from(
            snapshots_for_addition, snapshots_for_removal
        )


class ProcessChangesState(State):
    def __init__(
        self,
        device_command_factory: BaseDeviceCommandFactory,
        subvolume_command_factory: BaseSubvolumeCommandFactory,
        refind_config_provider: BaseRefindConfigProvider,
        persistence_provider: BasePersistenceProvider,
    ):
        super().__init__(States.PROCESS_CHANGES.value)

        self._device_command_factory = device_command_factory
        self._subvolume_command_factory = subvolume_command_factory
        self._refind_config_provider = refind_config_provider
        self._persistence_provider = persistence_provider

    def enter(self, event_data: EventData) -> None:
        model = cast(Model, event_data.model)
        persistence_provider = self._persistence_provider
        subvolume_command_factory = self._subvolume_command_factory
        subvolume_command = subvolume_command_factory.subvolume_command()
        previous_run_result = persistence_provider.get_previous_run_result()
        bootable_snapshots = previous_run_result.bootable_snapshots
        snapshot_preparation_result = model.preparation_result
        snapshots_for_addition = snapshot_preparation_result.snapshots_for_addition
        snapshots_for_removal = snapshot_preparation_result.snapshots_for_removal

        if helpers.has_items(snapshots_for_addition):
            device_command_factory = self._device_command_factory
            static_device_command = device_command_factory.static_device_command()
            subvolume = model.root_subvolume

            for addition in snapshots_for_addition:
                bootable_snapshot = subvolume_command.get_bootable_snapshot_from(
                    addition
                )

                bootable_snapshot.modify_partition_table_using(
                    subvolume, static_device_command
                )

                if bootable_snapshot not in bootable_snapshots:
                    bootable_snapshots.append(bootable_snapshot)

        if helpers.has_items(snapshots_for_removal):
            for removal in snapshots_for_removal:
                if removal.is_newly_created:
                    subvolume_command.delete_snapshot(removal)

                if removal in bootable_snapshots:
                    bootable_snapshots.remove(removal)

        root = model.root_partition
        sorted_bootable_snapshots = sorted(bootable_snapshots, reverse=True)
        include_paths = model.should_include_paths_during_generation()
        include_sub_menus = model.should_include_sub_menus_during_generation()
        refind_config = model.refind_config
        generated_refind_configs = refind_config.generate_new_from(
            root,
            sorted_bootable_snapshots,
            include_paths,
            include_sub_menus,
        )
        refind_config_provider = self._refind_config_provider

        for generated_refind_config in generated_refind_configs:
            refind_config_provider.save_config(generated_refind_config)

        refind_config_provider.append_to_config(refind_config)

        package_config = model.package_config
        current_boot_stanza_generation = package_config.boot_stanza_generation

        persistence_provider.save_current_run_result(
            ProcessingResult(sorted_bootable_snapshots, current_boot_stanza_generation)
        )
