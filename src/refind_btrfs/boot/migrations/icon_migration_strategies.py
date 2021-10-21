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

from abc import ABC, abstractmethod
from pathlib import Path

from refind_btrfs.common import BtrfsLogo, Icon
from refind_btrfs.common.abc.commands import IconCommand
from refind_btrfs.common.enums import BootStanzaIconGenerationMode


class BaseIconMigrationStrategy(ABC):
    def __init__(
        self, icon_command: IconCommand, refind_config_path: Path, source_icon: str
    ) -> None:
        self._icon_command = icon_command
        self._refind_config_path = refind_config_path
        self._source_icon_path = Path(source_icon)

    @abstractmethod
    def migrate(self) -> str:
        pass


class DefaultMigrationStrategy(BaseIconMigrationStrategy):
    def migrate(self) -> str:
        return str(self._source_icon_path)


class CustomMigrationStrategy(BaseIconMigrationStrategy):
    def __init__(
        self,
        icon_command: IconCommand,
        refind_config_path: Path,
        source_icon: str,
        custom_icon_path: Path,
    ) -> None:
        super().__init__(icon_command, refind_config_path, source_icon)

        self._custom_icon_path = custom_icon_path

    def migrate(self) -> str:
        icon_command = self._icon_command
        refind_config_path = self._refind_config_path
        source_icon_path = self._source_icon_path
        custom_icon_path = self._custom_icon_path
        destination_icon_relative_path = icon_command.validate_custom_icon(
            refind_config_path, source_icon_path, custom_icon_path
        )

        return str(destination_icon_relative_path)


class EmbedBtrfsLogoStrategy(BaseIconMigrationStrategy):
    def __init__(
        self,
        icon_command: IconCommand,
        refind_config_path: Path,
        source_icon: str,
        btrfs_logo: BtrfsLogo,
    ) -> None:
        super().__init__(icon_command, refind_config_path, source_icon)

        self._btrfs_logo = btrfs_logo

    def migrate(self) -> str:
        icon_command = self._icon_command
        refind_config_path = self._refind_config_path
        source_icon_path = self._source_icon_path
        btrfs_logo = self._btrfs_logo
        destination_icon_relative_path = icon_command.embed_btrfs_logo_into_source_icon(
            refind_config_path, source_icon_path, btrfs_logo
        )

        return str(destination_icon_relative_path)


class IconMigrationFactory:
    @staticmethod
    def migration_strategy(
        icon_command: IconCommand,
        refind_config_path: Path,
        source_icon: str,
        icon: Icon,
    ) -> BaseIconMigrationStrategy:
        mode = icon.mode

        if mode == BootStanzaIconGenerationMode.DEFAULT:
            return DefaultMigrationStrategy(
                icon_command, refind_config_path, source_icon
            )

        if mode == BootStanzaIconGenerationMode.CUSTOM:
            custom_icon_path = icon.path

            return CustomMigrationStrategy(
                icon_command, refind_config_path, source_icon, custom_icon_path
            )

        if mode == BootStanzaIconGenerationMode.EMBED_BTRFS_LOGO:
            btrfs_logo = icon.btrfs_logo

            return EmbedBtrfsLogoStrategy(
                icon_command, refind_config_path, source_icon, btrfs_logo
            )

        raise ValueError(
            "The 'icon' parameter's 'mode' property contains an unexpected value!"
        )
