# region Licensing
# SPDX-FileCopyrightText: 2020-2021 Luka Žaja <luka.zaja@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

""" refind-btrfs - Generate rEFInd manual boot stanzas from Btrfs snapshots
Copyright (C) 2020-2021  Luka Žaja

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
from abc import ABC, abstractmethod
from copy import deepcopy
from functools import singledispatchmethod
from pathlib import Path
from typing import Any, Optional

from refind_btrfs.common import BootStanzaGeneration, Icon, constants
from refind_btrfs.common.abc.commands import IconCommand
from refind_btrfs.device import Subvolume
from refind_btrfs.utility.helpers import (
    is_none_or_whitespace,
    none_throws,
    replace_root_part_in,
)

from ..boot_options import BootOptions
from ..boot_stanza import BootStanza
from ..sub_menu import SubMenu
from .icon_migration_strategies import IconMigrationFactory
from .state import State


class BaseMainMigrationStrategy(ABC):
    def __init__(
        self,
        is_latest: bool,
        refind_config_path: Path,
        current_state: State,
        source_subvolume: Subvolume,
        destination_subvolume: Subvolume,
        boot_stanza_generation: BootStanzaGeneration,
    ) -> None:
        self._is_latest = is_latest
        self._refind_config_path = refind_config_path
        self._current_state = current_state
        self._source_subvolume = source_subvolume
        self._destination_subvolume = destination_subvolume
        self._boot_stanza_generation = boot_stanza_generation

    @abstractmethod
    def migrate(self) -> State:
        pass

    @property
    def destination_name(self) -> str:
        destination_subvolume = self._destination_subvolume

        if not destination_subvolume.is_named():
            raise ValueError("The 'destination_subvolume' instance must be named!")

        current_name = self._current_state.name
        destination_subvolume_name = none_throws(destination_subvolume.name)
        subvolume_name_pattern = re.compile(rf"\({constants.SUBVOLUME_NAME_PATTERN}\)")
        match = subvolume_name_pattern.search(current_name)

        if match:
            destination_name = subvolume_name_pattern.sub(
                f"({destination_subvolume_name})", current_name
            )
        else:
            destination_name = f"{current_name} ({destination_subvolume_name})"

        return f"{constants.DOUBLE_QUOTE}{destination_name}{constants.DOUBLE_QUOTE}"

    @property
    def destination_loader_path(self) -> Optional[str]:
        current_loader_path = self._current_state.loader_path

        if not is_none_or_whitespace(current_loader_path):
            return replace_root_part_in(
                none_throws(current_loader_path),
                self._source_subvolume.logical_path,
                self._destination_subvolume.logical_path,
            )

        return None

    @property
    def destination_initrd_path(self) -> Optional[str]:
        current_initrd_path = self._current_state.initrd_path

        if not is_none_or_whitespace(current_initrd_path):
            return replace_root_part_in(
                none_throws(current_initrd_path),
                self._source_subvolume.logical_path,
                self._destination_subvolume.logical_path,
            )

        return None

    @property
    def destination_boot_options(self) -> Optional[BootOptions]:
        current_boot_options = self._current_state.boot_options

        if current_boot_options is not None:
            destination_boot_options = deepcopy(current_boot_options)
            include_paths = self.include_paths

            destination_boot_options.migrate_from_to(
                self._source_subvolume,
                self._destination_subvolume,
                include_paths,
            )

            return destination_boot_options

        return None

    @property
    def destination_add_boot_options(self) -> Optional[BootOptions]:
        current_add_boot_options = self._current_state.add_boot_options

        if current_add_boot_options is not None:
            destination_add_boot_options = deepcopy(current_add_boot_options)
            include_paths = self.include_paths

            destination_add_boot_options.migrate_from_to(
                self._source_subvolume,
                self._destination_subvolume,
                include_paths,
            )

            return destination_add_boot_options

        return None

    @property
    def include_paths(self) -> bool:
        return self._boot_stanza_generation.include_paths

    @property
    def icon(self) -> Icon:
        return self._boot_stanza_generation.icon


class BootStanzaMigrationStrategy(BaseMainMigrationStrategy):
    def __init__(
        self,
        is_latest: bool,
        refind_config_path: Path,
        boot_stanza: BootStanza,
        source_subvolume: Subvolume,
        destination_subvolume: Subvolume,
        boot_stanza_generation: BootStanzaGeneration,
        icon_command: IconCommand,
    ) -> None:
        super().__init__(
            is_latest,
            refind_config_path,
            State(
                boot_stanza.normalized_name,
                boot_stanza.loader_path,
                boot_stanza.initrd_path,
                boot_stanza.icon_path,
                boot_stanza.boot_options,
                None,
            ),
            source_subvolume,
            destination_subvolume,
            boot_stanza_generation,
        )

        self._icon_command = icon_command

    def migrate(self) -> State:
        include_paths = self.include_paths
        is_latest = self._is_latest
        current_state = self._current_state
        destination_loader_path = constants.EMPTY_STR
        destination_initrd_path = constants.EMPTY_STR

        if is_latest:
            destination_loader_path = none_throws(current_state.loader_path)
            destination_initrd_path = none_throws(current_state.initrd_path)

        if include_paths:
            destination_loader_path = none_throws(self.destination_loader_path)
            destination_initrd_path_candidate = self.destination_initrd_path

            if not is_none_or_whitespace(destination_initrd_path_candidate):
                destination_initrd_path = none_throws(destination_initrd_path_candidate)

        icon_migration_strategy = IconMigrationFactory.migration_strategy(
            self._icon_command,
            self._refind_config_path,
            none_throws(current_state.icon_path),
            self.icon,
        )

        destination_icon_path = icon_migration_strategy.migrate()

        return State(
            self.destination_name,
            destination_loader_path,
            destination_initrd_path,
            destination_icon_path,
            self.destination_boot_options,
            None,
        )


class SubMenuMigrationStrategy(BaseMainMigrationStrategy):
    def __init__(
        self,
        is_latest: bool,
        refind_config_path: Path,
        sub_menu: SubMenu,
        source_subvolume: Subvolume,
        destination_subvolume: Subvolume,
        boot_stanza_generation: BootStanzaGeneration,
        inherit_from_state: State,
    ) -> None:
        super().__init__(
            is_latest,
            refind_config_path,
            State(
                sub_menu.normalized_name,
                sub_menu.loader_path,
                sub_menu.initrd_path,
                None,
                sub_menu.boot_options,
                sub_menu.add_boot_options,
            ),
            source_subvolume,
            destination_subvolume,
            boot_stanza_generation,
        )

        self._inherit_from_state = inherit_from_state

    def migrate(self) -> State:
        include_paths = self.include_paths
        is_latest = self._is_latest
        current_state = self._current_state
        inherit_from_state = self._inherit_from_state
        destination_loader_path = current_state.loader_path
        destination_initrd_path = current_state.initrd_path
        destination_boot_options: Optional[BootOptions] = None
        destination_add_boot_options = self.destination_add_boot_options

        if not is_latest:
            if include_paths:
                destination_loader_path = inherit_from_state.loader_path
                destination_initrd_path = inherit_from_state.initrd_path

            destination_boot_options = BootOptions.merge(
                (
                    none_throws(inherit_from_state.boot_options),
                    none_throws(destination_add_boot_options),
                )
            )
            destination_add_boot_options = BootOptions(constants.EMPTY_STR)

        if include_paths:
            destination_loader_path_candidate = self.destination_loader_path
            destination_initrd_path_candidate = self.destination_initrd_path

            if not is_none_or_whitespace(destination_loader_path_candidate):
                destination_loader_path = destination_loader_path_candidate

            if not is_none_or_whitespace(destination_initrd_path_candidate):
                destination_initrd_path = destination_initrd_path_candidate

        return State(
            self.destination_name,
            destination_loader_path,
            destination_initrd_path,
            None,
            destination_boot_options,
            destination_add_boot_options,
        )


class MainMigrationFactory:
    # pylint: disable=unused-argument
    @singledispatchmethod
    @staticmethod
    def migration_strategy(
        argument: Any,
        is_latest: bool,
        refind_config_path: Path,
        source_subvolume: Subvolume,
        destination_subvolume: Subvolume,
        boot_stanza_generation: BootStanzaGeneration,
        icon_command: Optional[IconCommand] = None,
        inherit_from_state: Optional[State] = None,
    ) -> BaseMainMigrationStrategy:
        raise NotImplementedError(
            "Cannot instantiate the main migration strategy "
            f"for parameter of type '{type(argument).__name__}'!"
        )

    # pylint: disable=unused-argument
    @migration_strategy.register(BootStanza)
    @staticmethod
    def _boot_stanza_overload(
        boot_stanza: BootStanza,
        is_latest: bool,
        refind_config_path: Path,
        source_subvolume: Subvolume,
        destination_subvolume: Subvolume,
        boot_stanza_generation: BootStanzaGeneration,
        icon_command: Optional[IconCommand] = None,
        inherit_from_state: Optional[State] = None,
    ) -> BaseMainMigrationStrategy:
        return BootStanzaMigrationStrategy(
            is_latest,
            refind_config_path,
            boot_stanza,
            source_subvolume,
            destination_subvolume,
            boot_stanza_generation,
            none_throws(icon_command),
        )

    # pylint: disable=unused-argument
    @migration_strategy.register(SubMenu)
    @staticmethod
    def _sub_menu_overload(
        sub_menu: SubMenu,
        is_latest: bool,
        refind_config_path: Path,
        source_subvolume: Subvolume,
        destination_subvolume: Subvolume,
        boot_stanza_generation: BootStanzaGeneration,
        icon_command: Optional[IconCommand] = None,
        inherit_from_state: Optional[State] = None,
    ) -> BaseMainMigrationStrategy:
        return SubMenuMigrationStrategy(
            is_latest,
            refind_config_path,
            sub_menu,
            source_subvolume,
            destination_subvolume,
            boot_stanza_generation,
            none_throws(inherit_from_state),
        )
