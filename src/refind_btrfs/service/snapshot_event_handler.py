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

from pathlib import Path
from threading import Lock
from typing import Set

from injector import inject
from more_itertools import only
from watchdog.events import (
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    DirCreatedEvent,
    DirDeletedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)

from refind_btrfs.common.abc.factories import (
    BaseLoggerFactory,
    BaseSubvolumeCommandFactory,
)
from refind_btrfs.common.abc.providers import (
    BasePackageConfigProvider,
    BasePersistenceProvider,
)
from refind_btrfs.device import Subvolume
from refind_btrfs.state_management import RefindBtrfsMachine
from refind_btrfs.utility.helpers import (
    checked_cast,
    discern_distance_between,
    has_items,
)


class SnapshotEventHandler(FileSystemEventHandler):
    @inject
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
        subvolume_command_factory: BaseSubvolumeCommandFactory,
        package_config_provider: BasePackageConfigProvider,
        persistence_provider: BasePersistenceProvider,
        machine: RefindBtrfsMachine,
    ) -> None:
        self._logger = logger_factory.logger(__name__)
        self._subvolume_command_factory = subvolume_command_factory
        self._package_config_provider = package_config_provider
        self._persistence_provider = persistence_provider
        self._machine = machine
        self._deleted_snapshots: Set[Subvolume] = set()
        self._deletion_lock = Lock()

    def on_created(self, event: FileSystemEvent) -> None:
        is_dir_created_event = (
            event.event_type == EVENT_TYPE_CREATED and event.is_directory
        )

        if is_dir_created_event:
            dir_created_event = checked_cast(DirCreatedEvent, event)
            logger = self._logger
            created_directory = Path(dir_created_event.src_path)

            if self._is_snapshot_created(created_directory):
                machine = self._machine

                logger.info(f"The '{created_directory}' directory has been created.")

                machine.run()

    def on_deleted(self, event: FileSystemEvent) -> None:
        is_dir_deleted_event = (
            event.event_type == EVENT_TYPE_DELETED and event.is_directory
        )

        if is_dir_deleted_event:
            dir_deleted_event = checked_cast(DirDeletedEvent, event)
            logger = self._logger
            deleted_directory = Path(dir_deleted_event.src_path)

            if self._is_snapshot_deleted(deleted_directory):
                machine = self._machine

                logger.info(f"The '{deleted_directory}' directory has been deleted.")

                machine.run()

    def _is_snapshot_created(self, created_directory: Path) -> bool:
        package_config_provider = self._package_config_provider
        package_config = package_config_provider.get_config()
        snapshot_searches = package_config.snapshot_searches
        parents = created_directory.parents

        for snapshot_search in snapshot_searches:
            search_directory = snapshot_search.directory

            if snapshot_search.directory in parents:
                distance = discern_distance_between(
                    (search_directory, created_directory)
                )

                if distance is not None:
                    max_depth = snapshot_search.max_depth - distance

                    if self._is_or_contains_snapshot(created_directory, max_depth):
                        return True

        return False

    def _is_snapshot_deleted(self, deleted_directory: Path) -> bool:
        persistence_provider = self._persistence_provider
        previous_run_result = persistence_provider.get_previous_run_result()
        bootable_snapshots = previous_run_result.bootable_snapshots

        if has_items(bootable_snapshots):
            deleted_snapshot = only(
                snapshot
                for snapshot in bootable_snapshots
                if snapshot.is_located_in(deleted_directory)
            )

            if deleted_snapshot is not None:
                deleted_snapshots = self._deleted_snapshots
                deletion_lock = self._deletion_lock

                with deletion_lock:
                    if not deleted_snapshot in deleted_snapshots:
                        deleted_snapshots.add(deleted_snapshot)

                        return True

        return False

    def _is_or_contains_snapshot(
        self, directory: Path, max_depth: int, current_depth: int = 0
    ) -> bool:
        if current_depth <= max_depth:
            subvolume_command = self._subvolume_command_factory.subvolume_command()
            resolved_path = directory.resolve()
            subvolume = subvolume_command.get_subvolume_from(resolved_path)
            is_snapshot = subvolume is not None and subvolume.is_snapshot()

            if is_snapshot:
                return True

            subdirectories = (child for child in directory.iterdir() if child.is_dir())

            if any(
                self._is_or_contains_snapshot(
                    subdirectory, max_depth, current_depth + 1
                )
                for subdirectory in subdirectories
            ):
                return True

        return False
