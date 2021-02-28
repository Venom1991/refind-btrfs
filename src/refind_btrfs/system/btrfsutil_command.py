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

from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional, Set

import btrfsutil

from refind_btrfs.common import PackageConfig, constants
from refind_btrfs.common.abc.commands import SubvolumeCommand
from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.abc.providers import BasePackageConfigProvider
from refind_btrfs.common.exceptions import SubvolumeError
from refind_btrfs.device import NumIdRelation, Subvolume, UuidRelation
from refind_btrfs.utility.helpers import (
    checked_cast,
    default_if_none,
    none_throws,
    try_convert_bytes_to_uuid,
)


class BtrfsUtilCommand(SubvolumeCommand):
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
        package_config_provider: BasePackageConfigProvider,
    ) -> None:
        self._logger = logger_factory.logger(__name__)
        self._package_config_provider = package_config_provider
        self._searched_directories: Set[Path] = set()

    def get_subvolume_from(self, filesystem_path: Path) -> Optional[Subvolume]:
        logger = self._logger

        if not filesystem_path.exists():
            raise SubvolumeError(f"The '{filesystem_path}' path does not exist!")

        if not filesystem_path.is_dir():
            raise SubvolumeError(
                f"The '{filesystem_path}' path does not represent a directory!"
            )

        try:
            filesystem_path_str = str(filesystem_path)

            if btrfsutil.is_subvolume(filesystem_path_str):
                subvolume_id = btrfsutil.subvolume_id(filesystem_path_str)
                subvolume_path = btrfsutil.subvolume_path(
                    filesystem_path_str, subvolume_id
                )
                subvolume_read_only = btrfsutil.get_subvolume_read_only(
                    filesystem_path_str
                )
                subvolume_info = btrfsutil.subvolume_info(
                    filesystem_path_str, subvolume_id
                )
                self_uuid = default_if_none(
                    try_convert_bytes_to_uuid(subvolume_info.uuid),
                    constants.EMPTY_UUID,
                )
                parent_uuid = default_if_none(
                    try_convert_bytes_to_uuid(subvolume_info.parent_uuid),
                    constants.EMPTY_UUID,
                )

                return Subvolume(
                    filesystem_path,
                    subvolume_path,
                    datetime.fromtimestamp(subvolume_info.otime),
                    UuidRelation(self_uuid, parent_uuid),
                    NumIdRelation(subvolume_info.id, subvolume_info.parent_id),
                    subvolume_read_only,
                )
        except btrfsutil.BtrfsUtilError as e:
            logger.exception("btrfsutil call failed!")
            raise SubvolumeError(
                f"Could not initialize the subvolume for '{filesystem_path}'!"
            ) from e

        return None

    def get_snapshots_for(self, parent: Subvolume) -> Generator[Subvolume, None, None]:
        self._searched_directories.clear()

        snapshot_searches = self.package_config.snapshot_searches

        for snapshot_search in snapshot_searches:
            directory = snapshot_search.directory
            is_nested = snapshot_search.is_nested
            max_depth = snapshot_search.max_depth
            search_result = self._search_for_snapshots_in(
                parent,
                directory,
                max_depth,
            )

            if is_nested:
                root_directory = directory.root

                for snapshot in search_result:
                    filesystem_path = snapshot.filesystem_path
                    nested_directory = filesystem_path / directory.relative_to(
                        root_directory
                    )

                    if nested_directory.exists():
                        yield from self._search_for_snapshots_in(
                            parent,
                            nested_directory,
                            max_depth,
                        )

                    yield snapshot
            else:
                yield from search_result

    def get_bootable_snapshot_from(self, source: Subvolume) -> Subvolume:
        if source.is_read_only:
            snapshot_manipulation = self.package_config.snapshot_manipulation
            modify_read_only_flag = snapshot_manipulation.modify_read_only_flag

            if modify_read_only_flag:
                destination = self._modify_read_only_flag_for(source)
            else:
                destination = self._create_writable_snapshot_from(source)
        else:
            destination = source

        return destination.as_named()

    def delete_snapshot(self, snapshot: Subvolume) -> None:
        logger = self._logger
        filesystem_path = snapshot.filesystem_path
        logical_path = snapshot.logical_path

        try:
            filesystem_path_str = str(filesystem_path)
            is_subvolume = filesystem_path.exists() and btrfsutil.is_subvolume(
                filesystem_path_str
            )

            if is_subvolume:
                root_dir_str = str(constants.ROOT_DIR)
                num_id = snapshot.num_id
                deleted_subvolumes = checked_cast(
                    List[int], btrfsutil.deleted_subvolumes(root_dir_str)
                )

                if num_id not in deleted_subvolumes:
                    logger.info(f"Deleting the '{logical_path}' snapshot.")

                    btrfsutil.delete_subvolume(filesystem_path_str)
                else:
                    logger.warning(
                        f"The '{logical_path}' snapshot has already "
                        "been deleted but not yet cleaned up."
                    )
            else:
                logger.warning(f"The '{filesystem_path}' directory is not a subvolume.")
        except btrfsutil.BtrfsUtilError as e:
            logger.exception("btrfsutil call failed!")
            raise SubvolumeError(
                f"Could not delete the '{logical_path}' snapshot!"
            ) from e

    def _search_for_snapshots_in(
        self,
        parent: Subvolume,
        directory: Path,
        max_depth: int,
        current_depth: int = 0,
    ) -> Generator[Subvolume, None, None]:
        if current_depth > max_depth:
            return

        logger = self._logger
        is_initial_call = not bool(current_depth)
        logical_path = parent.logical_path
        resolved_path = directory.resolve()

        if is_initial_call:
            logger.info(
                f"Searching for snapshots of the '{logical_path}' "
                f"subvolume in the '{directory}' directory."
            )

        searched_directories = self._searched_directories

        if resolved_path not in searched_directories:
            subvolume = self.get_subvolume_from(resolved_path)
            is_snapshot_of = subvolume is not None and subvolume.is_snapshot_of(parent)

            searched_directories.add(resolved_path)

            if is_snapshot_of:
                yield none_throws(subvolume)
            else:
                subdirectories = (
                    child for child in directory.iterdir() if child.is_dir()
                )

                for subdirectory in subdirectories:
                    yield from self._search_for_snapshots_in(
                        parent, subdirectory, max_depth, current_depth + 1
                    )

    def _modify_read_only_flag_for(self, source: Subvolume) -> Subvolume:
        logger = self._logger
        source_logical_path = source.logical_path

        try:
            logger.info(
                f"Modifying the '{source_logical_path}' snapshot's read-only flag."
            )

            source_filesystem_path_str = str(source.filesystem_path)

            btrfsutil.set_subvolume_read_only(source_filesystem_path_str, False)
        except btrfsutil.BtrfsUtilError as e:
            logger.exception("btrfsutil call failed!")
            raise SubvolumeError(
                f"Could not modify the '{source_logical_path}' snapshot's read-only flag!"
            ) from e

        return source.as_writable()

    def _create_writable_snapshot_from(self, source: Subvolume) -> Subvolume:
        logger = self._logger
        snapshot_manipulation = self.package_config.snapshot_manipulation
        destination_directory = snapshot_manipulation.destination_directory

        if not destination_directory.exists():
            directory_permissions = constants.SNAPSHOTS_ROOT_DIR_PERMISSIONS
            octal_permissions = "{0:o}".format(directory_permissions)

            try:
                logger.info(
                    f"Creating the '{destination_directory}' destination "
                    f"directory with {octal_permissions} permissions."
                )

                destination_directory.mkdir(mode=directory_permissions, parents=True)
            except OSError as e:
                logger.exception("Path.mkdir() call failed!")
                raise SubvolumeError(
                    f"Could not create the '{destination_directory}' destination directory!"
                ) from e

        destination = source.to_destination(destination_directory)
        source_logical_path = source.logical_path
        snapshot_directory = destination.filesystem_path

        try:
            logger.info(
                "Creating a new writable snapshot from the read-only "
                f"'{source_logical_path}' snapshot at '{snapshot_directory}'."
            )

            snapshot_directory_str = str(snapshot_directory)
            is_subvolume = snapshot_directory.exists() and btrfsutil.is_subvolume(
                snapshot_directory_str
            )

            if not is_subvolume:
                source_filesystem_path_str = str(source.filesystem_path)

                btrfsutil.create_snapshot(
                    source_filesystem_path_str, snapshot_directory_str, read_only=False
                )
            else:
                logger.warning(
                    f"The '{snapshot_directory}' directory is already a subvolume."
                )
        except btrfsutil.BtrfsUtilError as e:
            logger.exception("btrfsutil call failed!")
            raise SubvolumeError(
                f"Could not create a new writable snapshot at '{snapshot_directory}'!"
            ) from e

        writable_snapshot = self.get_subvolume_from(snapshot_directory)

        return none_throws(writable_snapshot).as_newly_created_from(source)

    @property
    def package_config(self) -> PackageConfig:
        package_config_provider = self._package_config_provider

        return package_config_provider.get_config()
