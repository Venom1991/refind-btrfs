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
from typing import Any, Callable, Iterator, Optional, Type, TypeVar, cast
from uuid import UUID

from injector import inject
from more_itertools import one, unique_everseen
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
    ConfigInitializationType,
    PathRelation,
    SnapshotManipulationConfigKey,
    SnapshotSearchConfigKey,
    TopLevelConfigKey,
)
from refind_btrfs.common.exceptions import PackageConfigError
from refind_btrfs.device import NumIdRelation, Subvolume, UuidRelation

from .helpers import checked_cast, discern_path_relation_of, has_items, try_parse_uuid

TSourceValue = TypeVar("TSourceValue")
TDestinationValue = TypeVar("TDestinationValue")


class FilePackageConfigProvider(BasePackageConfigProvider):
    default_package_config = PackageConfig(
        constants.EMPTY_UUID,
        True,
        True,
        [SnapshotSearch(Path("/.snapshots"), False, 2)],
        SnapshotManipulation(5, False, Path("/root/.refind-btrfs"), set()),
        BootStanzaGeneration("refind.conf", True, False),
    )

    @inject
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
        persistence_provider: BasePersistenceProvider,
    ) -> None:
        self._logger = logger_factory.logger(__name__)
        self._persistence_provider = persistence_provider
        self._package_config: Optional[PackageConfig] = None

    def get_config(self) -> PackageConfig:
        persistence_provider = self._persistence_provider
        persisted_package_config = persistence_provider.get_package_config()
        current_package_config = self._package_config

        if persisted_package_config is None:
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
                current_package_config = FilePackageConfigProvider._read_config_from(
                    toml_document
                ).with_initialization_type(
                    ConfigInitializationType.PARSED, PackageConfig
                )

                persistence_provider.save_package_config(current_package_config)
        elif current_package_config is None:
            current_package_config = persisted_package_config.with_initialization_type(
                ConfigInitializationType.PERSISTED, PackageConfig
            )

        self._package_config = current_package_config

        return current_package_config

    @staticmethod
    def _read_config_from(toml_document: TOMLDocument):
        container = cast(dict, toml_document)
        default_package_config = FilePackageConfigProvider.default_package_config
        esp_uuid = FilePackageConfigProvider._get_config_value(
            container,
            TopLevelConfigKey.ESP_UUID.value,
            str,
            default_package_config,
            (UUID, try_parse_uuid),
        )
        exit_if_root_is_snapshot = FilePackageConfigProvider._get_config_value(
            container,
            TopLevelConfigKey.EXIT_IF_ROOT_IS_SNAPSHOT.value,
            bool,
            default_package_config,
        )
        exit_if_no_changes_are_detected = FilePackageConfigProvider._get_config_value(
            container,
            TopLevelConfigKey.EXIT_IF_NO_CHANGES_ARE_DETECTED.value,
            bool,
            default_package_config,
        )
        snapshot_searches_key = TopLevelConfigKey.SNAPSHOT_SEARCH.value
        default_snapshot_searches = default_package_config.snapshot_searches

        if snapshot_searches_key in container:
            snapshot_searches = list(
                unique_everseen(
                    FilePackageConfigProvider._map_to_snapshot_searches(
                        checked_cast(AoT, container[snapshot_searches_key]),
                        one(default_snapshot_searches),
                    )
                )
            )
        else:
            snapshot_searches = default_snapshot_searches

        snapshot_manipulation_key = TopLevelConfigKey.SNAPSHOT_MANIPULATION.value

        if snapshot_manipulation_key in container:
            snapshot_manipulation = (
                FilePackageConfigProvider._map_to_snapshot_manipulation(
                    checked_cast(
                        Table,
                        container[snapshot_manipulation_key],
                    ),
                    default_package_config.snapshot_manipulation,
                )
            )
        else:
            snapshot_manipulation = default_package_config.snapshot_manipulation

        destination_directory = snapshot_manipulation.destination_directory

        for snapshot_search in snapshot_searches:
            search_directory = snapshot_search.directory
            path_relation = discern_path_relation_of(
                (destination_directory, search_directory)
            )

            if path_relation == PathRelation.SAME:
                raise PackageConfigError(
                    "The search and destination directories cannot be the same!"
                )

            if path_relation == PathRelation.FIRST_NESTED_IN_SECOND:
                raise PackageConfigError(
                    f"The '{destination_directory}' destination directory is nested in "
                    f"the '{search_directory}' search directory!"
                )

            if path_relation == PathRelation.SECOND_NESTED_IN_FIRST:
                raise PackageConfigError(
                    f"The '{search_directory}' search directory is nested in "
                    f"the '{destination_directory}' destination directory!"
                )

        boot_stanza_generation_key = TopLevelConfigKey.BOOT_STANZA_GENERATION.value

        if boot_stanza_generation_key in container:
            boot_stanza_generation = (
                FilePackageConfigProvider._map_to_boot_stanza_generation(
                    checked_cast(Table, container[boot_stanza_generation_key]),
                    default_package_config.boot_stanza_generation,
                )
            )
        else:
            boot_stanza_generation = default_package_config.boot_stanza_generation

        return PackageConfig(
            esp_uuid,
            exit_if_root_is_snapshot,
            exit_if_no_changes_are_detected,
            snapshot_searches,
            snapshot_manipulation,
            boot_stanza_generation,
        )

    @staticmethod
    def _map_to_snapshot_searches(
        snapshot_search_values: AoT, default_snapshot_search: SnapshotSearch
    ) -> Iterator[SnapshotSearch]:
        max_depth_key = SnapshotSearchConfigKey.MAX_DEPTH.value

        for snapshot_search_value in snapshot_search_values.body:
            container = cast(dict, snapshot_search_value)
            directory = cast(
                Path,
                FilePackageConfigProvider._get_config_value(
                    container,
                    SnapshotSearchConfigKey.DIRECTORY.value,
                    str,
                    default_snapshot_search,
                    (Path, None),
                ),
            )

            if not directory.exists():
                raise PackageConfigError(f"The '{directory}' path does not exist!")

            if not directory.is_dir():
                raise PackageConfigError(
                    f"The '{directory}' path does not represent a directory!"
                )

            is_nested = FilePackageConfigProvider._get_config_value(
                container,
                SnapshotSearchConfigKey.IS_NESTED.value,
                bool,
                default_snapshot_search,
            )
            max_depth = cast(
                int,
                FilePackageConfigProvider._get_config_value(
                    container, max_depth_key, int, default_snapshot_search
                ),
            )

            if max_depth <= 0:
                raise PackageConfigError(
                    f"The '{max_depth_key}' option must be greater than zero!"
                )

            yield SnapshotSearch(directory, is_nested, max_depth)

    @staticmethod
    def _map_to_snapshot_manipulation(
        snapshot_manipulation_value: Table,
        default_snapshot_manipulation: SnapshotManipulation,
    ) -> SnapshotManipulation:
        container = cast(dict, snapshot_manipulation_value)
        selection_count_key = SnapshotManipulationConfigKey.SELECTION_COUNT.value

        if selection_count_key in container:
            selection_count_value = container[selection_count_key]

            if isinstance(selection_count_value, int):
                selection_count = int(selection_count_value)

                if selection_count <= 0:
                    raise PackageConfigError(
                        f"The '{selection_count_key}' option must be greater than zero!"
                    )
            elif isinstance(selection_count_value, str):
                actual_string = str(selection_count_value).strip()
                expected_string = constants.SNAPSHOT_SELECTION_COUNT_INFINITY

                if actual_string != expected_string:
                    raise PackageConfigError(
                        f"In case the '{selection_count_key}' option is a string "
                        f"it can only be set to '{expected_string}'!"
                    )

                selection_count = sys.maxsize
            else:
                raise PackageConfigError(
                    f"The '{selection_count_key}' option must be either an integer or a string!"
                )
        else:
            selection_count = default_snapshot_manipulation.selection_count

        modify_read_only_flag = FilePackageConfigProvider._get_config_value(
            container,
            SnapshotManipulationConfigKey.MODIFY_READ_ONLY_FLAG.value,
            bool,
            default_snapshot_manipulation,
        )
        destination_directory = FilePackageConfigProvider._get_config_value(
            container,
            SnapshotManipulationConfigKey.DESTINATION_DIRECTORY.value,
            str,
            default_snapshot_manipulation,
            (Path, None),
        )
        cleanup_exclusion_key = SnapshotManipulationConfigKey.CLEANUP_EXCLUSION.value
        cleanup_exclusion = cast(
            list,
            FilePackageConfigProvider._get_config_value(
                container,
                cleanup_exclusion_key,
                list,
                default_snapshot_manipulation,
            ),
        )
        uuids: list[UUID] = []

        if has_items(cleanup_exclusion):
            for item in cleanup_exclusion:
                if not isinstance(item, str):
                    raise PackageConfigError(
                        f"Every member of the '{cleanup_exclusion_key}' array must be a string!"
                    )

                uuid = try_parse_uuid(item)
                type_name = UUID.__name__

                if uuid is None:
                    raise PackageConfigError(
                        f"Could not parse '{item}' as expected type ('{type_name}')!"
                    )

                if uuid == constants.EMPTY_UUID:
                    raise PackageConfigError(
                        f"The '{cleanup_exclusion_key}' array must "
                        f"not contain empty '{type_name}' values!"
                    )

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
        default_boot_stanza_generation: BootStanzaGeneration,
    ) -> BootStanzaGeneration:
        container = cast(dict, boot_stanza_generation_value)
        refind_config = FilePackageConfigProvider._get_config_value(
            container,
            BootStanzaGenerationConfigKey.REFIND_CONFIG.value,
            str,
            default_boot_stanza_generation,
        )
        include_paths = FilePackageConfigProvider._get_config_value(
            container,
            BootStanzaGenerationConfigKey.INCLUDE_PATHS.value,
            bool,
            default_boot_stanza_generation,
        )
        include_sub_menus = FilePackageConfigProvider._get_config_value(
            container,
            BootStanzaGenerationConfigKey.INCLUDE_SUB_MENUS.value,
            bool,
            default_boot_stanza_generation,
        )

        return BootStanzaGeneration(refind_config, include_paths, include_sub_menus)

    @staticmethod
    def _get_config_value(
        container: dict,
        key: str,
        source_type: Type[TSourceValue],
        default_config: object,
        value_conversion: Optional[
            tuple[Type[TDestinationValue], Optional[Callable[[TSourceValue], Any]]]
        ] = None,
    ) -> Any:
        if key in container:
            source_value = container[key]

            if not isinstance(source_value, source_type):
                raise PackageConfigError(
                    f"The '{key}' option must be of type '{source_type.__name__}'!"
                )

            if value_conversion is not None:
                destination_type = value_conversion[0]
                converter_func = value_conversion[1]

                if converter_func is None:
                    converter_func = cast(
                        Callable[[TSourceValue], Any], destination_type
                    )

                destination_value = converter_func(source_value)

                if destination_value is None:
                    raise PackageConfigError(
                        f"Could not parse '{source_value}' as "
                        f"expected type ('{destination_type.__name__}')!"
                    )

                return checked_cast(destination_type, destination_value)

            return checked_cast(source_type, source_value)

        return getattr(default_config, key)
