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
from typing import TYPE_CHECKING

from refind_btrfs.common import constants
from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.exceptions import (
    RefindConfigError,
    SubvolumeError,
    UnchangedConfiguration,
    UnsupportedConfiguration,
)
from refind_btrfs.utility.helpers import (
    has_items,
    is_singleton,
    item_count_suffix,
    none_throws,
)

if TYPE_CHECKING:
    from .model import Model


class Conditions:
    def __init__(self, logger_factory: BaseLoggerFactory, model: Model) -> None:
        self._logger = logger_factory.logger(__name__)
        self._model = model

    def check_filtered_block_devices(self) -> bool:
        logger = self._logger
        model = self._model
        esp_device = model.esp_device

        if esp_device is None:
            logger.error("Could not find the ESP!")

            return False

        esp = model.esp
        esp_filesystem = none_throws(esp.filesystem)

        logger.info(
            f"Found the ESP mounted at '{esp_filesystem.mount_point}' on '{esp.name}'."
        )

        root_device = model.root_device

        if root_device is None:
            logger.error("Could not find the root partition!")

            return False

        root_partition = model.root_partition
        root_filesystem = none_throws(root_partition.filesystem)

        logger.info(f"Found the root partition on '{root_partition.name}'.")

        btrfs_type = constants.BTRFS_TYPE

        if not root_filesystem.is_of_type(btrfs_type):
            logger.error(f"The root partition's filesystem is not '{btrfs_type}'!")

            return False

        boot_device = model.boot_device

        if boot_device is not None:
            boot = none_throws(esp_device.boot)

            logger.info(f"Found a separate boot partition on '{boot.name}'.")

        return True

    def check_root_subvolume(self) -> bool:
        logger = self._logger
        model = self._model
        root_partition = model.root_partition
        filesystem = none_throws(root_partition.filesystem)

        if not filesystem.has_subvolume():
            logger.error("The root partition is not mounted as a subvolume!")

            return False

        subvolume = none_throws(filesystem.subvolume)
        logical_path = subvolume.logical_path

        logger.info(f"Found subvolume '{logical_path}' mounted as the root partition.")

        if subvolume.is_snapshot():
            package_config = model.package_config

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

    def check_matched_boot_stanzas(self) -> bool:
        logger = self._logger
        model = self._model
        matched_boot_stanzas = model.matched_boot_stanzas

        if not has_items(matched_boot_stanzas):
            logger.error(
                "Could not find a boot stanza matched with the root partition!"
            )

            return False

        suffix = item_count_suffix(matched_boot_stanzas)

        logger.info(
            f"Found {len(matched_boot_stanzas)} boot "
            f"stanza{suffix} matched with the root partition."
        )

        grouping_result = groupby(matched_boot_stanzas)

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

        for boot_stanza in matched_boot_stanzas:
            try:
                boot_stanza.validate_boot_files_check_result()
            except RefindConfigError as e:
                logger.warning(e.formatted_message)

        usable_boot_stanzas = model.usable_boot_stanzas

        if not has_items(usable_boot_stanzas):
            logger.error("None of the matched boot stanzas are usable!")

            return False

        return True

    def check_prepared_snapshots(self) -> bool:
        logger = self._logger
        model = self._model
        prepared_snapshots = model.prepared_snapshots

        if not prepared_snapshots.has_changes():
            raise UnchangedConfiguration("No changes were detected, aborting...")

        snapshots_for_addition = prepared_snapshots.snapshots_for_addition
        snapshots_for_removal = prepared_snapshots.snapshots_for_removal

        if has_items(snapshots_for_addition):
            subvolume = model.root_subvolume
            suffix = item_count_suffix(snapshots_for_addition)

            logger.info(
                f"Found {len(snapshots_for_addition)} snapshot{suffix} for addition."
            )

            for snapshot in snapshots_for_addition:
                try:
                    snapshot.validate_static_partition_table(subvolume)
                except SubvolumeError as e:
                    logger.warning(e.formatted_message)

            usable_snapshots_for_addition = model.usable_snapshots_for_addition

            if not has_items(usable_snapshots_for_addition):
                logger.warning("None of the snapshots for addition are usable!")

        if has_items(snapshots_for_removal):
            suffix = item_count_suffix(snapshots_for_removal)

            logger.info(
                f"Found {len(snapshots_for_removal)} snapshot{suffix} for removal."
            )

        return True

    def check_boot_stanzas_with_snapshots(self) -> bool:
        logger = self._logger
        model = self._model
        boot_stanzas_with_snapshots = model.boot_stanzas_with_snapshots

        for item in boot_stanzas_with_snapshots:
            if item.has_unmatched_snapshots():
                unmatched_snapshots = item.unmatched_snapshots

                for snapshot in unmatched_snapshots:
                    try:
                        snapshot.validate_boot_files_check_result()
                    except SubvolumeError as e:
                        logger.warning(e.formatted_message)

            if not item.has_matched_snapshots():
                boot_stanza = item.boot_stanza
                normalized_name = boot_stanza.normalized_name

                logger.warning(
                    "None of the prepared snapshots are matched "
                    f"with the '{normalized_name}' boot stanza!"
                )

        usable_boot_stanzas_with_snapshots = model.usable_boot_stanzas_with_snapshots

        if not has_items(usable_boot_stanzas_with_snapshots):
            logger.error(
                "None of the matched boot stanzas can be "
                "combined with any of the prepared snapshots!"
            )

            return False

        return True
