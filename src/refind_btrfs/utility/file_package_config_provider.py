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
from typing import Generator, List
from uuid import UUID

from injector import inject
from more_itertools import unique_everseen
from tomlkit.exceptions import TOMLKitError
from tomlkit.items import AoT, Table
from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile

from refind_btrfs.common import (
    BootStanzaGeneration,
    PackageConfig,
    SnapshotManipulation,
    SnapshotSearch,
    constants,
)
from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.abc.providers import (
    BasePackageConfigProvider,
    BasePersistenceProvider,
)
from refind_btrfs.common.enums import (
    BootStanzaGenerationConfigKey,
    PathRelation,
    SnapshotManipulationConfigKey,
    SnapshotSearchConfigKey,
    TopLevelConfigKey,
)
from refind_btrfs.common.exceptions import PackageConfigError
from refind_btrfs.device import NumIdRelation, Subvolume, UuidRelation

from .helpers import checked_cast, discern_path_relation_of, has_items, try_parse_uuid


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
                raise PackageConfigError(
                    f"The '{config_file_path}' path does not exist!"
                )

            if not config_file_path.is_file():
                raise PackageConfigError(
                    f"The '{config_file_path}' does not represent a file!"
                )

            logger.info(f"Analyzing the '{config_file_path.name}' file.")

            try:
                toml_file = TOMLFile(str(config_file_path))
                toml_document = toml_file.read()
            except TOMLKitError as e:
                logger.exception(
                    f"Error while parsing the '{config_file_path.name}' file"
                )
                raise PackageConfigError(
                    "Could not load the package configuration from file'!"
                ) from e
            else:
                config = FilePackageConfigProvider._read_config_from(toml_document)

            persistence_provider.save_package_config(config)

        return config

    @staticmethod
    def _read_config_from(toml_document: TOMLDocument):
        exit_if_root_is_snapshot_key: str = (
            TopLevelConfigKey.EXIT_IF_ROOT_IS_SNAPSHOT.value
        )
        snapshot_searches_key: str = TopLevelConfigKey.SNAPSHOT_SEARCH.value
        snapshot_manipulation_key: str = TopLevelConfigKey.SNAPSHOT_MANIPULATION.value
        boot_stanza_generation_key: str = TopLevelConfigKey.BOOT_STANZA_GENERATION.value

        if exit_if_root_is_snapshot_key not in toml_document:
            raise PackageConfigError(
                f"Missing option '{exit_if_root_is_snapshot_key}'!"
            )

        exit_if_root_is_snapshot_value = toml_document[exit_if_root_is_snapshot_key]

        if not isinstance(exit_if_root_is_snapshot_value, bool):
            raise PackageConfigError(
                f"The '{exit_if_root_is_snapshot_key}' option must be a bool!"
            )
        else:
            exit_if_root_is_snapshot = bool(exit_if_root_is_snapshot_value)

        if snapshot_searches_key not in toml_document:
            raise PackageConfigError(
                f"At least one '{snapshot_searches_key}' object is required!"
            )

        snapshot_searches = list(
            unique_everseen(
                FilePackageConfigProvider._map_to_snapshot_searches(
                    checked_cast(AoT, toml_document[snapshot_searches_key])
                )
            )
        )

        if snapshot_manipulation_key not in toml_document:
            raise PackageConfigError(
                f"The '{snapshot_manipulation_key}' object is required!"
            )

        snapshot_manipulation = FilePackageConfigProvider._map_to_snapshot_manipulation(
            checked_cast(Table, toml_document[snapshot_manipulation_key])
        )
        output_directory = snapshot_manipulation.destination_directory

        for snapshot_search in snapshot_searches:
            search_directory = snapshot_search.directory
            path_relation = discern_path_relation_of(
                (output_directory, search_directory)
            )

            if path_relation == PathRelation.SAME:
                raise PackageConfigError(
                    "The search and output directories cannot be the same!"
                )

            if path_relation == PathRelation.FIRST_NESTED_IN_SECOND:
                raise PackageConfigError(
                    f"The '{output_directory}' output directory is nested in "
                    f"the '{search_directory}' search directory!"
                )

            if path_relation == PathRelation.SECOND_NESTED_IN_FIRST:
                raise PackageConfigError(
                    f"The '{search_directory}' search directory is nested in "
                    f"the '{output_directory}' output directory!"
                )

        if boot_stanza_generation_key not in toml_document:
            raise PackageConfigError(
                f"The '{boot_stanza_generation_key}' object is required!"
            )

        boot_stanza_generation = (
            FilePackageConfigProvider._map_to_boot_stanza_generation(
                checked_cast(Table, toml_document[boot_stanza_generation_key])
            )
        )

        return PackageConfig(
            exit_if_root_is_snapshot,
            snapshot_searches,
            snapshot_manipulation,
            boot_stanza_generation,
        )

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
                raise PackageConfigError(
                    f"The '{directory_key}' option must be a string!"
                )
            else:
                directory = Path(directory_value)

                if not directory.exists():
                    raise PackageConfigError(
                        f"The '{directory_value}' path does not exist!"
                    )

                if not directory.is_dir():
                    raise PackageConfigError(
                        f"The '{directory_value}' path does not represent a directory!"
                    )

            is_nested_value = value[is_nested_key]

            if not isinstance(is_nested_value, bool):
                raise PackageConfigError(
                    f"The '{is_nested_key}' option must be a bool!"
                )
            else:
                is_nested = bool(is_nested_value)

            max_depth_value = value[max_depth_key]

            if not isinstance(max_depth_value, int):
                raise PackageConfigError(
                    f"The '{max_depth_key}' option must be an integer!"
                )
            else:
                max_depth = int(max_depth_value)

                if max_depth <= 0:
                    raise PackageConfigError(
                        f"The '{max_depth_key}' option must be greater than zero!"
                    )

            yield SnapshotSearch(directory, is_nested, max_depth)

    @staticmethod
    def _map_to_snapshot_manipulation(
        snapshot_manipulation_value: Table,
    ) -> SnapshotManipulation:
        selection_count_key: str = SnapshotManipulationConfigKey.SELECTION_COUNT.value
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
            selection_count_key,
            modify_read_only_flag_key,
            destination_directory_key,
            cleanup_exclusion_key,
        ]

        for key in all_keys:
            if key not in snapshot_manipulation_value:
                raise PackageConfigError(f"Missing option '{key}'!")

        selection_count_value = snapshot_manipulation_value[selection_count_key]

        if isinstance(selection_count_value, int):
            selection_count = int(selection_count_value)

            if selection_count <= 0:
                raise PackageConfigError(
                    f"The '{selection_count_key}' option must be greater than zero!"
                )
        elif isinstance(selection_count_value, str):
            actual_str = str(selection_count_value).strip()
            expected_str = constants.SNAPSHOT_SELECTION_COUNT_INFINITY

            if actual_str != expected_str:
                raise PackageConfigError(
                    f"In case the '{selection_count_key}' option is a string "
                    f"it can only be set to '{expected_str}'!"
                )

            selection_count = sys.maxsize
        else:
            raise PackageConfigError(
                f"The '{selection_count_key}' option must be either an integer or a string!"
            )

        modify_read_only_flag_value = snapshot_manipulation_value[
            modify_read_only_flag_key
        ]

        if not isinstance(modify_read_only_flag_value, bool):
            raise PackageConfigError(
                f"The '{modify_read_only_flag_key}' option must be a bool!"
            )
        else:
            modify_read_only_flag = bool(modify_read_only_flag_value)

        destination_directory_value = snapshot_manipulation_value[
            destination_directory_key
        ]

        if not isinstance(destination_directory_value, str):
            raise PackageConfigError(
                f"The '{destination_directory_key}' option must be a string!"
            )
        else:
            destination_directory = Path(destination_directory_value)

        cleanup_exclusion_value = snapshot_manipulation_value[cleanup_exclusion_key]

        if not isinstance(cleanup_exclusion_value, list):
            raise PackageConfigError(
                f"The '{cleanup_exclusion_key}' option must be a string!"
            )

        cleanup_exclusion = list(cleanup_exclusion_value)
        uuids: List[UUID] = []

        if has_items(cleanup_exclusion):
            for item in cleanup_exclusion:
                if not isinstance(item, str):
                    raise PackageConfigError(
                        f"Every member of the '{cleanup_exclusion_key}' array must be a string!"
                    )

                uuid = try_parse_uuid(item)

                if uuid is None:
                    raise PackageConfigError(f"Could not parse '{item}' as an UUID!")

                uuids.append(uuid)

        return SnapshotManipulation(
            selection_count,
            modify_read_only_flag,
            destination_directory,
            set(
                Subvolume(
                    constants.EMPTY_PATH,
                    constants.EMPTY_STR,
                    datetime.min,
                    UuidRelation(uuid, constants.EMPTY_UUID),
                    NumIdRelation(0, 0),
                    False,
                )
                for uuid in uuids
            ),
        )

    @staticmethod
    def _map_to_boot_stanza_generation(
        boot_stanza_generation_value: Table,
    ) -> BootStanzaGeneration:
        refind_config_key: str = BootStanzaGenerationConfigKey.REFIND_CONFIG.value
        include_paths_key: str = BootStanzaGenerationConfigKey.INCLUDE_PATHS.value
        include_sub_menus_key: str = (
            BootStanzaGenerationConfigKey.INCLUDE_SUB_MENUS.value
        )
        all_keys = [refind_config_key, include_paths_key, include_sub_menus_key]

        for key in all_keys:
            if key not in boot_stanza_generation_value:
                raise PackageConfigError(f"Missing option '{key}'!")

        refind_config_value = boot_stanza_generation_value[refind_config_key]

        if not isinstance(refind_config_value, str):
            raise PackageConfigError(
                f"The '{refind_config_key}' option must be a string!"
            )
        else:
            refind_config = str(refind_config_value)

        include_paths_value = boot_stanza_generation_value[include_paths_key]

        if not isinstance(include_paths_value, bool):
            raise PackageConfigError(
                f"The '{include_paths_key}' option must be a bool!"
            )
        else:
            include_paths = bool(include_paths_value)

        include_sub_menus_value = boot_stanza_generation_value[include_sub_menus_key]

        if not isinstance(include_sub_menus_value, bool):
            raise PackageConfigError(
                f"The '{include_sub_menus_key}' option must be a bool!"
            )
        else:
            include_sub_menus = bool(include_sub_menus_value)

        return BootStanzaGeneration(refind_config, include_paths, include_sub_menus)
