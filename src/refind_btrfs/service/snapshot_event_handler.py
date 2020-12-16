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
from typing import Optional, Set, cast

from injector import inject
from watchdog.events import (
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    DirCreatedEvent,
    DirDeletedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)

from refind_btrfs.common.abc import (
    BaseLoggerFactory,
    BasePackageConfigProvider,
    BaseSubvolumeCommandFactory,
)
from refind_btrfs.common.exceptions import SubvolumeError
from refind_btrfs.state_management import RefindBtrfsMachine


class SnapshotEventHandler(FileSystemEventHandler):
    @inject
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
        package_config_provider: BasePackageConfigProvider,
        subvolume_command_factory: BaseSubvolumeCommandFactory,
        machine: RefindBtrfsMachine,
    ) -> None:
        self._logger = logger_factory.logger(__name__)
        self._package_config_provider = package_config_provider
        self._subvolume_command = subvolume_command_factory.subvolume_command()
        self._machine = machine
        self._directories_with_snapshots: Optional[Set[Path]] = None

    def on_created(self, event: FileSystemEvent) -> None:
        is_dir_created_event = (
            event.event_type == EVENT_TYPE_CREATED and event.is_directory
        )

        if is_dir_created_event:
            dir_created_event = cast(DirCreatedEvent, event)
            logger = self._logger
            directories_with_snapshots = self.directories_with_snapshots
            filesystem_path = Path(dir_created_event.src_path)
            is_snapshot_created = self._is_snapshot_contained_in(filesystem_path)

            if is_snapshot_created:
                machine = self._machine

                logger.info(
                    f"Directory '{filesystem_path}' containing a snapshot has been created."
                )

                machine.run()
                directories_with_snapshots.add(filesystem_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        is_dir_deleted_event = (
            event.event_type == EVENT_TYPE_DELETED and event.is_directory
        )

        if is_dir_deleted_event:
            dir_deleted_event = cast(DirDeletedEvent, event)
            logger = self._logger
            directories_with_snapshots = self.directories_with_snapshots
            filesystem_path = Path(dir_deleted_event.src_path)
            is_snapshot_deleted = filesystem_path in directories_with_snapshots

            if is_snapshot_deleted:
                machine = self._machine

                logger.info(
                    f"Directory '{filesystem_path}' containing a snapshot has been deleted."
                )

                machine.run()
                directories_with_snapshots.remove(filesystem_path)

    def _is_snapshot_contained_in(
        self,
        directory: Path,
    ) -> bool:
        subvolume_command = self._subvolume_command
        subdirectories = (child for child in directory.iterdir() if child.is_dir())

        for subdirectory in subdirectories:
            resolved_path = subdirectory.resolve()
            subvolume = subvolume_command.get_subvolume_from(resolved_path)
            is_snapshot = subvolume is not None and subvolume.is_snapshot()

            if is_snapshot:
                return True

        return False

    @property
    def directories_with_snapshots(self) -> Set[Path]:
        directories_with_snapshots = self._directories_with_snapshots

        if directories_with_snapshots is None:
            logger = self._logger
            package_config = self._package_config_provider.get_config()
            watched_directories = package_config.get_directories_for_watch()

            try:
                directories_with_snapshots = {
                    *[
                        directory
                        for directory in watched_directories
                        if self._is_snapshot_contained_in(directory)
                    ]
                }
            except SubvolumeError as e:
                logger.exception("Could not prepare for handling filesystem events!")
                raise e
            else:
                self._directories_with_snapshots = directories_with_snapshots

        return directories_with_snapshots
