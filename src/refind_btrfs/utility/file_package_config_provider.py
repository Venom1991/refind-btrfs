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

import sys
from datetime import datetime
from pathlib import Path
from typing import Generator, List, cast
from uuid import UUID

from injector import inject
from more_itertools import unique_everseen
from tomlkit.exceptions import TOMLKitError
from tomlkit.items import AoT, Table
from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile

from refind_btrfs.common import (
    PackageConfig,
    SnapshotManipulation,
    SnapshotSearch,
    constants,
)
from refind_btrfs.common.abc import (
    BaseLoggerFactory,
    BasePackageConfigProvider,
    BasePersistenceProvider,
)
from refind_btrfs.common.enums import (
    PathRelation,
    SnapshotManipulationConfigKey,
    SnapshotSearchConfigKey,
    TopLevelConfigKey,
)
from refind_btrfs.common.exceptions import PackageConfigError
from refind_btrfs.device.subvolume import NumIdRelation, Subvolume, UuidRelation

from . import helpers


class FilePackageConfigProvider(BasePackageConfigProvider):
    @inject
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
        persistence_provider: BasePersistenceProvider,
    ) -> None:
        self._logger = logger_factory.logger(__name__)
        self._persistence_provider = persistence_provider

    def get_config(self) -> PackageConfig:
        persistence_provider = self._persistence_provider
        config = persistence_provider.get_package_config()

        if config is None:
            logger = self._logger
            config_file_path = constants.PACKAGE_CONFIG_FILE

            if not config_file_path.exists():
                raise PackageConfigError(f"Path '{config_file_path}' does not exist!")

            if not config_file_path.is_file():
                raise PackageConfigError(f"'{config_file_path}' is not a file!")

            try:
                toml_file = TOMLFile(str(config_file_path))
                toml_document = toml_file.read()
            except TOMLKitError as e:
                logger.exception(f"Error while parsing file '{config_file_path}'")
                raise PackageConfigError(
                    "Could not load the package configuration from file'!"
                ) from e
            else:
                config = FilePackageConfigProvider._read_config_from(toml_document)

            persistence_provider.save_package_config(config)

        return config

    @staticmethod
    def _read_config_from(toml_document: TOMLDocument):
        snapshot_searches_key = TopLevelConfigKey.SNAPSHOT_SEARCH.value
        snapshot_manipulation_key = TopLevelConfigKey.SNAPSHOT_MANIPULATION.value

        if snapshot_searches_key not in toml_document:
            raise PackageConfigError(
                f"At least one '{snapshot_searches_key}' object is required!"
            )

        snapshot_searches = list(
            unique_everseen(
                FilePackageConfigProvider._map_to_snapshot_searches(
                    cast(AoT, toml_document[snapshot_searches_key])
                )
            )
        )

        if snapshot_manipulation_key not in toml_document:
            raise PackageConfigError(
                f"The '{snapshot_manipulation_key}' object is required!"
            )

        snapshot_manipulation = FilePackageConfigProvider._map_to_snapshot_manipulation(
            cast(Table, toml_document[snapshot_manipulation_key])
        )

        output_directory = snapshot_manipulation.destination_directory

        for snapshot_search in snapshot_searches:
            search_directory = snapshot_search.directory
            path_relation = helpers.discern_path_relation_of(
                output_directory, search_directory
            )

            if path_relation == PathRelation.SAME:
                raise PackageConfigError(
                    "Search directory and output directory cannot be the same!"
                )

            if path_relation == PathRelation.FIRST_NESTED_IN_SECOND:
                raise PackageConfigError(
                    f"Output directory '{output_directory}' is nested in "
                    f"search directory '{search_directory}'!"
                )

            if path_relation == PathRelation.SECOND_NESTED_IN_FIRST:
                raise PackageConfigError(
                    f"Search directory '{search_directory}' is nested in "
                    f"output directory '{output_directory}'!"
                )

        return PackageConfig(snapshot_searches, snapshot_manipulation)

    @staticmethod
    def _map_to_snapshot_searches(
        snapshot_searches_value: AoT,
    ) -> Generator[SnapshotSearch, None, None]:
        directory_key: str = SnapshotSearchConfigKey.DIRECTORY.value
        max_depth_key: str = SnapshotSearchConfigKey.MAX_DEPTH.value
        is_nested_key: str = SnapshotSearchConfigKey.IS_NESTED.value
        all_keys = [directory_key, max_depth_key, is_nested_key]

        for value in snapshot_searches_value:
            for key in all_keys:
                if key not in value:
                    raise PackageConfigError(f"Missing option '{key}'!")

            directory_value = value[directory_key]

            if not isinstance(directory_value, str):
                raise PackageConfigError(f"Option '{directory_key}' must be a string!")
            else:
                directory = Path(directory_value)

                if not directory.exists():
                    raise PackageConfigError(
                        f"Path '{directory_value}' does not exist!"
                    )

                if not directory.is_dir():
                    raise PackageConfigError(f"'{directory_value}' is not a directory!")

            is_nested_value = value[is_nested_key]

            if not isinstance(is_nested_value, bool):
                raise PackageConfigError(f"Option '{is_nested_key}' must be a bool!")
            else:
                is_nested = bool(is_nested_value)

            max_depth_value = value[max_depth_key]

            if not isinstance(max_depth_value, int):
                raise PackageConfigError(
                    f"Option '{max_depth_key}' must be an integer!"
                )
            else:
                max_depth = int(max_depth_value)

                if max_depth <= 0:
                    raise PackageConfigError(
                        f"Option '{max_depth_key}' must be greater than zero!"
                    )

            yield SnapshotSearch(directory, is_nested, max_depth)

    @staticmethod
    def _map_to_snapshot_manipulation(
        snapshot_manipulation_value: Table,
    ) -> SnapshotManipulation:
        refind_config_key: str = SnapshotManipulationConfigKey.REFIND_CONFIG.value
        count_key: str = SnapshotManipulationConfigKey.COUNT.value
        include_sub_menus_key: str = (
            SnapshotManipulationConfigKey.INCLUDE_SUB_MENUS.value
        )
        modify_read_only_flag_key: str = (
            SnapshotManipulationConfigKey.MODIFY_READ_ONLY_FLAG.value
        )
        destination_directory_key: str = (
            SnapshotManipulationConfigKey.DESTINATION_DIRECTORY.value
        )
        cleanup_exclusion_key: str = (
            SnapshotManipulationConfigKey.CLEANUP_EXCLUSION.value
        )
        all_keys = [
            count_key,
            include_sub_menus_key,
            modify_read_only_flag_key,
            destination_directory_key,
            cleanup_exclusion_key,
        ]

        for key in all_keys:
            if key not in snapshot_manipulation_value:
                raise PackageConfigError(f"Missing option '{key}'!")

        refind_config_value = snapshot_manipulation_value[refind_config_key]

        if not isinstance(refind_config_value, str):
            raise PackageConfigError(f"Option '{refind_config_key}' must be a string!")
        else:
            refind_config = str(refind_config_value)

        count_value = snapshot_manipulation_value[count_key]

        if isinstance(count_value, int):
            count = int(count_value)

            if count <= 0:
                raise PackageConfigError(
                    f"Option '{count_key}' must be greater than zero!"
                )
        elif isinstance(count_value, str):
            actual_str = str(count_value).strip()
            expected_str = constants.SNAPSHOT_COUNT_INFINITY

            if actual_str != expected_str:
                raise PackageConfigError(
                    f"In case the option '{count_key}' is a string "
                    f"it can only be set to '{expected_str}'!"
                )

            count = sys.maxsize
        else:
            raise PackageConfigError(
                f"Option '{count_key}' must be either an integer or a string!"
            )

        include_sub_menus_value = snapshot_manipulation_value[include_sub_menus_key]

        if not isinstance(include_sub_menus_value, bool):
            raise PackageConfigError(
                f"Option '{include_sub_menus_key}' must be a bool!"
            )
        else:
            include_sub_menus = bool(include_sub_menus_value)

        modify_read_only_flag_value = snapshot_manipulation_value[
            modify_read_only_flag_key
        ]

        if not isinstance(modify_read_only_flag_value, bool):
            raise PackageConfigError(
                f"Option '{modify_read_only_flag_key}' must be a bool!"
            )
        else:
            modify_read_only_flag = bool(modify_read_only_flag_value)

        destination_directory_value = snapshot_manipulation_value[
            destination_directory_key
        ]

        if not isinstance(destination_directory_value, str):
            raise PackageConfigError(
                f"Option '{destination_directory_key}' must be a string!"
            )
        else:
            destination_directory = Path(destination_directory_value)

        cleanup_exclusion_value = snapshot_manipulation_value[cleanup_exclusion_key]

        if not isinstance(cleanup_exclusion_value, list):
            raise PackageConfigError(
                f"Option '{cleanup_exclusion_key}' must be a string!"
            )

        cleanup_exclusion = list(cleanup_exclusion_value)
        uuids: List[UUID] = []

        if helpers.has_items(cleanup_exclusion):
            for item in cleanup_exclusion:
                if not isinstance(item, str):
                    raise PackageConfigError(
                        f"Every member of the '{cleanup_exclusion_key}' array must be a string!"
                    )

                uuid = helpers.try_parse_uuid(item)

                if uuid is None:
                    raise PackageConfigError(f"Could not parse '{item}' as an UUID!")

                uuids.append(uuid)

        return SnapshotManipulation(
            refind_config,
            count,
            include_sub_menus,
            modify_read_only_flag,
            destination_directory,
            {
                *[
                    Subvolume(
                        constants.DEFAULT_PATH,
                        constants.EMPTY_STR,
                        datetime.min,
                        UuidRelation(uuid, constants.EMPTY_UUID),
                        NumIdRelation(0, 0),
                        False,
                    )
                    for uuid in uuids
                ]
            },
        )
