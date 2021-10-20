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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Union

from refind_btrfs.common import BtrfsLogo, Icon, constants
from refind_btrfs.common.enums import (
    BootStanzaIconGenerationMode,
    BtrfsLogoHorizontalAlignment,
    BtrfsLogoVerticalAlignment,
)
from refind_btrfs.common.exceptions import RefindConfigError


class BaseIconMigrationStrategy(ABC):
    def __init__(self, current_icon: str, refind_config_path: Path) -> None:
        self._current_icon_path = Path(current_icon)
        self._refind_config_path = refind_config_path

    def _discern_icon_relative_path(self, icon_path: Path) -> str:
        current_icon_path_parts = self._current_icon_path.parts
        refind_config_path_parents = self._refind_config_path.parents

        for parent in refind_config_path_parents:
            if parent.name not in current_icon_path_parts:
                return constants.FORWARD_SLASH + str(icon_path.relative_to(parent))

        raise RefindConfigError(
            f"Could not discern the '{icon_path.name}' file's relative path!"
        )

    def _discern_icon_full_path(self, icon_path: Path) -> Path:
        icon_path_parts = icon_path.parts
        refind_config_path_parents = self._refind_config_path.parents

        for parent in refind_config_path_parents:
            if parent.name not in icon_path_parts:
                return parent / str(icon_path).removeprefix(constants.FORWARD_SLASH)

        raise RefindConfigError(
            f"Could not discern the '{icon_path.name}' file's full path!"
        )

    @abstractmethod
    def migrate(self) -> str:
        pass


class DefaultMigrationStrategy(BaseIconMigrationStrategy):
    def migrate(self) -> str:
        return str(self._current_icon_path)


class CustomMigrationStrategy(BaseIconMigrationStrategy):
    def __init__(
        self, current_icon: str, refind_config_path: Path, custom_icon_path: Path
    ) -> None:
        super().__init__(current_icon, refind_config_path)

        self._custom_icon_path = custom_icon_path

    def migrate(self) -> str:
        refind_config_path = self._refind_config_path
        custom_icon_path = self._custom_icon_path
        custom_icon_full_path = refind_config_path.parent / custom_icon_path

        if not custom_icon_full_path.exists():
            raise RefindConfigError(
                f"The '{custom_icon_full_path}' path does not exist!"
            )

        try:
            # pylint: disable=import-outside-toplevel
            from PIL import Image

            with Image.open(custom_icon_full_path, "r") as custom_icon_image:
                expected_formats = ["PNG", "JPEG", "BMP", "ICNS"]
                custom_icon_image_format = custom_icon_image.format

                if custom_icon_image_format not in expected_formats:
                    raise RefindConfigError(
                        f"The '{custom_icon_full_path.name}' image's "
                        f"format ('{custom_icon_image_format}') is not supported!"
                    )
        except OSError as e:
            raise RefindConfigError(
                f"Could not read the '{custom_icon_full_path}' file!"
            ) from e

        return self._discern_icon_relative_path(custom_icon_full_path)


class EmbedBtrfsLogoStrategy(BaseIconMigrationStrategy):
    def __init__(
        self, current_icon: str, refind_config_path: Path, btrfs_logo: BtrfsLogo
    ) -> None:
        super().__init__(current_icon, refind_config_path)

        minimum_offset: Callable[[int], int] = lambda _: 0
        medium_offset: Callable[[int], int] = lambda delta: delta // 2
        maximum_offset: Callable[[int], int] = lambda delta: delta

        self._btrfs_logo = btrfs_logo
        self._embed_offset_initializers: dict[
            Union[BtrfsLogoHorizontalAlignment, BtrfsLogoVerticalAlignment],
            Callable[[int], int],
        ] = {
            BtrfsLogoHorizontalAlignment.LEFT: minimum_offset,
            BtrfsLogoHorizontalAlignment.CENTER: medium_offset,
            BtrfsLogoHorizontalAlignment.RIGHT: maximum_offset,
            BtrfsLogoVerticalAlignment.TOP: minimum_offset,
            BtrfsLogoVerticalAlignment.CENTER: medium_offset,
            BtrfsLogoVerticalAlignment.BOTTOM: maximum_offset,
        }

    def migrate(self) -> str:
        btrfs_logo = self._btrfs_logo
        variant = btrfs_logo.variant
        size = btrfs_logo.size
        btrfs_logo_file_path = (
            constants.BTRFS_LOGOS_DIR / f"{variant.value}_{size.value}.png"
        )

        if not btrfs_logo_file_path.exists():
            raise RefindConfigError(
                f"The '{btrfs_logo_file_path}' path does not exist!"
            )

        current_icon_path = self._current_icon_path
        current_icon_full_path = self._discern_icon_full_path(current_icon_path)

        try:
            # pylint: disable=import-outside-toplevel
            from PIL import Image

            with Image.open(btrfs_logo_file_path) as btrfs_logo_image, Image.open(
                current_icon_full_path
            ) as current_icon_image:
                expected_format = "PNG"
                current_icon_image_format = current_icon_image.format

                if current_icon_image_format != expected_format:
                    raise RefindConfigError(
                        f"The '{current_icon_full_path.name}' image's "
                        f"format ('{current_icon_image_format}') is not supported!"
                    )

                btrfs_logo_image_width = btrfs_logo_image.width
                current_icon_image_width = current_icon_image.width

                if current_icon_image_width < btrfs_logo_image_width:
                    raise RefindConfigError(
                        f"The '{current_icon_full_path.name}' image's width "
                        f"({current_icon_image_width} px) is less than "
                        "the selected Btrfs logo's width!"
                    )

                btrfs_logo_image_height = btrfs_logo_image.height
                current_icon_image_height = current_icon_image.height

                if current_icon_image_height < btrfs_logo_image_height:
                    raise RefindConfigError(
                        f"The '{current_icon_full_path.name}' image's height "
                        f"({current_icon_image_height} px) is less than "
                        "the selected Btrfs logo's height!"
                    )

                try:
                    horizontal_alignment = btrfs_logo.horizontal_alignment
                    x_delta = current_icon_image_width - btrfs_logo_image_width
                    x_offset = self._embed_offset_initializers[horizontal_alignment](x_delta)
                    vertical_alignment = btrfs_logo.vertical_alignment
                    y_delta = current_icon_image_height - btrfs_logo_image_height
                    y_offset = self._embed_offset_initializers[vertical_alignment](y_delta)
                    resized_btrfs_logo_image = Image.new(
                        btrfs_logo_image.mode, current_icon_image.size
                    )

                    resized_btrfs_logo_image.paste(
                        btrfs_logo_image.copy(),
                        (
                            x_offset,
                            y_offset,
                        ),
                    )

                    refind_config_path = self._refind_config_path
                    destination_icon_directory = (
                        refind_config_path.parent
                        / constants.SNAPSHOT_STANZAS_DIR_NAME
                        / constants.ICONS_DIR
                    )
                    destination_icon_image = Image.alpha_composite(
                        current_icon_image.copy(), resized_btrfs_logo_image
                    )

                    if not destination_icon_directory.exists():
                        destination_icon_directory.mkdir(parents=True)

                    destination_icon_full_path = (
                        destination_icon_directory / current_icon_path.name
                    )

                    destination_icon_image.save(destination_icon_full_path)
                except OSError as e:
                    raise RefindConfigError(
                        f"Could not save the '{e.filename}' file!"
                    ) from e

        except OSError as e:
            raise RefindConfigError(f"Could not read the '{e.filename}' file!") from e

        return self._discern_icon_relative_path(destination_icon_full_path)


class IconMigrationFactory:
    @staticmethod
    def migration_strategy(
        current_icon: str,
        refind_config_path: Path,
        icon: Icon,
    ) -> BaseIconMigrationStrategy:
        mode = icon.mode

        if mode == BootStanzaIconGenerationMode.DEFAULT:
            return DefaultMigrationStrategy(current_icon, refind_config_path)

        if mode == BootStanzaIconGenerationMode.CUSTOM:
            custom_icon_path = icon.path

            return CustomMigrationStrategy(
                current_icon, refind_config_path, custom_icon_path
            )

        if mode == BootStanzaIconGenerationMode.EMBED_BTRFS_LOGO:
            btrfs_logo = icon.btrfs_logo

            return EmbedBtrfsLogoStrategy(current_icon, refind_config_path, btrfs_logo)

        raise ValueError(
            "The 'icon' parameter's 'mode' property contains an unexpected value!"
        )
