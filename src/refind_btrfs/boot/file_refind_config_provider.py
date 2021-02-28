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

import re
from pathlib import Path
from typing import Dict, Generator, Iterable, List

from antlr4 import CommonTokenStream, FileStream
from injector import inject
from more_itertools import last, one

from refind_btrfs.common import constants
from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.abc.providers import (
    BasePackageConfigProvider,
    BasePersistenceProvider,
    BaseRefindConfigProvider,
)
from refind_btrfs.common.enums import RefindOption
from refind_btrfs.common.exceptions import RefindConfigError, RefindSyntaxError
from refind_btrfs.device import Partition
from refind_btrfs.utility.helpers import (
    checked_cast,
    has_items,
    is_none_or_whitespace,
    is_singleton,
    item_count_suffix,
    none_throws,
)

from .antlr4 import RefindConfigLexer, RefindConfigParser
from .boot_stanza import BootStanza
from .refind_config import RefindConfig
from .refind_listeners import RefindErrorListener
from .refind_visitors import BootStanzaVisitor, IncludeVisitor


class FileRefindConfigProvider(BaseRefindConfigProvider):
    all_config_file_paths: Dict[Partition, Path] = {}

    @inject
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
        package_config_provider: BasePackageConfigProvider,
        persistence_provider: BasePersistenceProvider,
    ) -> None:
        self._logger = logger_factory.logger(__name__)
        self._package_config_provider = package_config_provider
        self._persistence_provider = persistence_provider

    def get_config(self, partition: Partition) -> RefindConfig:
        logger = self._logger
        config_file_path = FileRefindConfigProvider.all_config_file_paths.get(partition)
        should_begin_search = config_file_path is None or not config_file_path.exists()

        if should_begin_search:
            package_config_provider = self._package_config_provider
            package_config = package_config_provider.get_config()
            boot_stanza_generation = package_config.boot_stanza_generation
            refind_config_file = boot_stanza_generation.refind_config

            logger.info(
                f"Searching for the '{refind_config_file}' file on '{partition.name}'."
            )

            refind_config_search_result = partition.search_paths_for(refind_config_file)

            if not has_items(refind_config_search_result):
                raise RefindConfigError(
                    f"Could not find the '{refind_config_file}' file!"
                )

            if not is_singleton(refind_config_search_result):
                raise RefindConfigError(
                    f"Found multiple '{refind_config_file}' files (at most one is expected)!"
                )

            config_file_path = checked_cast(
                Path, one(none_throws(refind_config_search_result))
            ).resolve()

            FileRefindConfigProvider.all_config_file_paths[partition] = config_file_path

        return self._read_config_from(none_throws(config_file_path))

    def save_config(self, config: RefindConfig) -> None:
        logger = self._logger
        persistence_provider = self._persistence_provider
        boot_stanzas = config.boot_stanzas

        if has_items(boot_stanzas):
            config_file_path = config.file_path
            destination_directory = config_file_path.parent

            if not destination_directory.exists():
                logger.info(
                    f"Creating the '{destination_directory.name}' destination directory."
                )

                destination_directory.mkdir()

            refind_directory = destination_directory.parent

            try:
                logger.info(
                    f"Writing to the '{config_file_path.relative_to(refind_directory)}' file."
                )

                with config_file_path.open("w") as config_file:
                    lines_for_writing: List[str] = []

                    lines_for_writing.append(
                        constants.NEWLINE.join(
                            str(boot_stanza)
                            for boot_stanza in none_throws(boot_stanzas)
                        )
                    )
                    lines_for_writing.append(constants.NEWLINE)
                    config_file.writelines(lines_for_writing)
            except OSError as e:
                logger.exception("Path.open('w') call failed!")
                raise RefindConfigError(
                    f"Could not write to the '{config_file_path.name}' file!"
                ) from e

            config.refresh_file_stat()
            persistence_provider.save_refind_config(config)

    def append_to_config(self, config: RefindConfig) -> None:
        logger = self._logger
        persistence_provider = self._persistence_provider
        config_file_path = config.file_path
        actual_config = persistence_provider.get_refind_config(config_file_path)

        if actual_config is not None:
            new_included_configs = config.get_included_configs_difference_from(
                actual_config
            )

            if has_items(new_included_configs):
                included_configs_for_appending = none_throws(new_included_configs)

                try:
                    with config_file_path.open("r") as config_file:
                        all_lines = config_file.readlines()
                        last_line = last(all_lines)
                except OSError as e:
                    logger.exception("Path.open('r') call failed!")
                    raise RefindConfigError(
                        f"Could not read from the '{config_file_path.name}' file!"
                    ) from e
                else:
                    include_option: str = RefindOption.INCLUDE.value
                    suffix = item_count_suffix(included_configs_for_appending)

                    try:
                        logger.info(
                            f"Appending {len(included_configs_for_appending)} '{include_option}' "
                            f"directive{suffix} to the '{config_file_path.name}' file."
                        )

                        with config_file_path.open("a") as config_file:
                            lines_for_appending: List[str] = []
                            should_prepend_newline = False

                            if not is_none_or_whitespace(last_line):
                                include_option_pattern = re.compile(
                                    constants.INCLUDE_OPTION_PATTERN, re.DOTALL
                                )

                                should_prepend_newline = (
                                    not include_option_pattern.match(last_line)
                                )

                            if should_prepend_newline:
                                lines_for_appending.append(constants.NEWLINE)

                            destination_directory = config_file_path.parent

                            for included_config in included_configs_for_appending:
                                included_config_relative_file_path = (
                                    included_config.file_path.relative_to(
                                        destination_directory
                                    )
                                )

                                lines_for_appending.append(
                                    f"{include_option} {included_config_relative_file_path}"
                                    f"{constants.NEWLINE}"
                                )

                            config_file.writelines(lines_for_appending)
                    except OSError as e:
                        logger.exception("Path.open('a') call failed!")
                        raise RefindConfigError(
                            f"Could not append to the '{config_file_path.name}' file!"
                        ) from e

                config.refresh_file_stat()

            persistence_provider.save_refind_config(config)

    def _read_config_from(self, config_file_path: Path) -> RefindConfig:
        logger = self._logger
        persistence_provider = self._persistence_provider
        refind_config = persistence_provider.get_refind_config(config_file_path)

        if refind_config is not None:
            if refind_config.has_included_configs():
                current_included_configs = none_throws(refind_config.included_configs)
                actual_included_configs = [
                    self._read_config_from(included_config.file_path)
                    for included_config in current_included_configs
                ]

                return refind_config.with_included_configs(actual_included_configs)

            return refind_config

        logger.info(f"Analyzing the '{config_file_path.name}' file.")

        try:
            input_stream = FileStream(str(config_file_path), encoding="utf-8")
            lexer = RefindConfigLexer(input_stream)
            token_stream = CommonTokenStream(lexer)
            parser = RefindConfigParser(token_stream)
            error_listener = RefindErrorListener()

            parser.removeErrorListeners()
            parser.addErrorListener(error_listener)

            refind_context = parser.refind()
        except RefindSyntaxError as e:
            logger.exception(f"Error while parsing the '{config_file_path.name}' file!")
            raise RefindConfigError(
                "Could not load rEFInd configuration from file!"
            ) from e
        else:
            config_option_contexts = checked_cast(
                List[RefindConfigParser.Config_optionContext],
                refind_context.config_option(),
            )
            boot_stanzas = FileRefindConfigProvider._map_to_boot_stanzas(
                config_option_contexts
            )
            includes = FileRefindConfigProvider._map_to_includes(config_option_contexts)
            included_configs = self._read_included_configs_from(
                config_file_path.parent, includes
            )

            refind_config = (
                RefindConfig(config_file_path)
                .with_boot_stanzas(boot_stanzas)
                .with_included_configs(included_configs)
            )

            persistence_provider.save_refind_config(refind_config)

            return refind_config

    def _read_included_configs_from(
        self, root_directory: Path, includes: Iterable[str]
    ) -> Generator[RefindConfig, None, None]:
        logger = self._logger

        for include in includes:
            included_config_file_path = root_directory / include

            if included_config_file_path.exists():
                yield self._read_config_from(included_config_file_path.resolve())
            else:
                logger.warning(
                    f"The included config file '{included_config_file_path.name}' does not exist."
                )

    @staticmethod
    def _map_to_boot_stanzas(
        config_option_contexts: List[RefindConfigParser.Config_optionContext],
    ) -> Generator[BootStanza, None, None]:
        if has_items(config_option_contexts):
            boot_stanza_visitor = BootStanzaVisitor()

            for config_option_context in config_option_contexts:
                boot_stanza_context = config_option_context.boot_stanza()

                if boot_stanza_context is not None:
                    yield checked_cast(
                        BootStanza, boot_stanza_context.accept(boot_stanza_visitor)
                    )

    @staticmethod
    def _map_to_includes(
        config_option_contexts: List[RefindConfigParser.Config_optionContext],
    ) -> Generator[str, None, None]:
        if has_items(config_option_contexts):
            include_visitor = IncludeVisitor()

            for config_option_context in config_option_contexts:
                include_context = config_option_context.include()

                if include_context is not None:
                    yield checked_cast(str, include_context.accept(include_visitor))
