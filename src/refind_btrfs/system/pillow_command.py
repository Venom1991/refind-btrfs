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

from pathlib import Path
from typing import Callable, Set, Tuple, Union

from refind_btrfs.common import BtrfsLogo, constants
from refind_btrfs.common.abc.commands import IconCommand
from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.enums import (
    BtrfsLogoHorizontalAlignment,
    BtrfsLogoVerticalAlignment,
)
from refind_btrfs.common.exceptions import RefindConfigError


class PillowCommand(IconCommand):
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
    ) -> None:
        minimum_offset: Callable[[int], int] = lambda _: 0
        medium_offset: Callable[[int], int] = lambda delta: delta // 2
        maximum_offset: Callable[[int], int] = lambda delta: delta

        self._logger = logger_factory.logger(__name__)
        self._validated_icons: Set[Path] = set()
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

    def validate_custom_icon(
        self, refind_config_path: Path, source_icon_path: Path, custom_icon_path: Path
    ) -> Path:
        custom_icon_absolute_path = refind_config_path.parent / custom_icon_path

        if not custom_icon_absolute_path.exists():
            raise RefindConfigError(
                f"The '{custom_icon_absolute_path}' path does not exist!"
            )

        validated_icons = self._validated_icons

        if custom_icon_absolute_path not in validated_icons:
            refind_directory = refind_config_path.parent
            logger = self._logger

            try:
                # pylint: disable=import-outside-toplevel
                from PIL import Image

                logger.info(
                    "Validating the "
                    f"'{custom_icon_absolute_path.relative_to(refind_directory)}' file."
                )

                with Image.open(custom_icon_absolute_path, "r") as custom_icon_image:
                    expected_formats = ["PNG", "JPEG", "BMP", "ICNS"]
                    custom_icon_image_format = custom_icon_image.format

                    if custom_icon_image_format not in expected_formats:
                        raise RefindConfigError(
                            f"The '{custom_icon_absolute_path.name}' image's "
                            f"format ('{custom_icon_image_format}') is not supported!"
                        )
            except OSError as e:
                logger.exception("Image.open('r') call failed!")
                raise RefindConfigError(
                    f"Could not read the '{custom_icon_absolute_path}' file!"
                ) from e

            validated_icons.add(custom_icon_absolute_path)

        return PillowCommand._discern_destination_icon_relative_path(
            refind_config_path, source_icon_path, custom_icon_absolute_path
        )

    def embed_btrfs_logo_into_source_icon(
        self, refind_config_path: Path, source_icon_path: Path, btrfs_logo: BtrfsLogo
    ) -> Path:
        source_icon_absolute_path = PillowCommand._discern_source_icon_absolute_path(
            refind_config_path, source_icon_path
        )
        absolute_paths = PillowCommand._discern_absolute_paths_for_btrfs_logo_embedding(
            refind_config_path, source_icon_absolute_path, btrfs_logo
        )
        btrfs_logo_absolute_path = absolute_paths[0]
        destination_icon_absolute_path = absolute_paths[1]

        if not destination_icon_absolute_path.exists():
            logger = self._logger
            refind_directory = refind_config_path.parent

            try:
                # pylint: disable=import-outside-toplevel
                from PIL import Image

                logger.info(
                    "Embedding "
                    f"the '{btrfs_logo_absolute_path.name}' "
                    "logo into "
                    f"the '{source_icon_absolute_path.relative_to(refind_directory)}' icon."
                )

                with Image.open(
                    btrfs_logo_absolute_path
                ) as btrfs_logo_image, Image.open(
                    source_icon_absolute_path
                ) as source_icon_image:
                    expected_format = "PNG"
                    source_icon_image_format = source_icon_image.format

                    if source_icon_image_format != expected_format:
                        raise RefindConfigError(
                            f"The '{source_icon_absolute_path.name}' image's "
                            f"format ('{source_icon_image_format}') is not supported!"
                        )

                    btrfs_logo_image_width = btrfs_logo_image.width
                    source_icon_image_width = source_icon_image.width

                    if source_icon_image_width < btrfs_logo_image_width:
                        raise RefindConfigError(
                            f"The '{source_icon_absolute_path.name}' image's width "
                            f"({source_icon_image_width} px) is less than "
                            "the selected Btrfs logo's width!"
                        )

                    btrfs_logo_image_height = btrfs_logo_image.height
                    source_icon_image_height = source_icon_image.height

                    if source_icon_image_height < btrfs_logo_image_height:
                        raise RefindConfigError(
                            f"The '{source_icon_absolute_path.name}' image's height "
                            f"({source_icon_image_height} px) is less than "
                            "the selected Btrfs logo's height!"
                        )

                    try:
                        horizontal_alignment = btrfs_logo.horizontal_alignment
                        x_delta = source_icon_image_width - btrfs_logo_image_width
                        x_offset = self._embed_offset_initializers[
                            horizontal_alignment
                        ](x_delta)
                        vertical_alignment = btrfs_logo.vertical_alignment
                        y_delta = source_icon_image_height - btrfs_logo_image_height
                        y_offset = self._embed_offset_initializers[vertical_alignment](
                            y_delta
                        )
                        resized_btrfs_logo_image = Image.new(
                            btrfs_logo_image.mode, source_icon_image.size
                        )

                        resized_btrfs_logo_image.paste(
                            btrfs_logo_image.copy(),
                            (
                                x_offset,
                                y_offset,
                            ),
                        )

                        destination_icon_image = Image.alpha_composite(
                            source_icon_image.copy(), resized_btrfs_logo_image
                        )
                        destination_directory = (
                            refind_directory
                            / constants.SNAPSHOT_STANZAS_DIR_NAME
                            / constants.ICONS_DIR
                        )

                        if not destination_directory.exists():
                            logger.info(
                                "Creating the "
                                f"'{destination_directory.relative_to(refind_directory)}' "
                                "destination directory."
                            )

                            destination_directory.mkdir(parents=True)

                        logger.info(
                            "Saving the "
                            f"'{destination_icon_absolute_path.relative_to(refind_directory)}' "
                            "file."
                        )

                        destination_icon_image.save(destination_icon_absolute_path)
                    except OSError as e:
                        logger.exception("Image.save() call failed!")
                        raise RefindConfigError(
                            f"Could not save the '{e.filename}' file!"
                        ) from e

            except OSError as e:
                logger.exception("Image.open('r') call failed!")
                raise RefindConfigError(
                    f"Could not read the '{e.filename}' file!"
                ) from e

        return PillowCommand._discern_destination_icon_relative_path(
            refind_config_path, source_icon_path, destination_icon_absolute_path
        )

    @staticmethod
    def _discern_source_icon_absolute_path(
        refind_config_path: Path, icon_path: Path
    ) -> Path:
        refind_config_path_parents = refind_config_path.parents
        icon_path_parts = icon_path.parts

        for parent in refind_config_path_parents:
            if parent.name not in icon_path_parts:
                return parent / str(icon_path).removeprefix(constants.FORWARD_SLASH)

        raise RefindConfigError(
            f"Could not discern the '{icon_path.name}' file's absolute path!"
        )

    @staticmethod
    def _discern_destination_icon_relative_path(
        refind_config_path: Path,
        source_icon_path: Path,
        destination_icon_path: Path,
    ) -> Path:
        source_icon_path_parts = source_icon_path.parts
        refind_config_path_parents = refind_config_path.parents

        for parent in refind_config_path_parents:
            if parent.name not in source_icon_path_parts:
                return constants.ROOT_DIR / destination_icon_path.relative_to(parent)

        raise RefindConfigError(
            f"Could not discern the '{destination_icon_path.name}' file's relative path!"
        )

    @staticmethod
    def _discern_absolute_paths_for_btrfs_logo_embedding(
        refind_config_path: Path, source_icon_absolute_path: Path, btrfs_logo: BtrfsLogo
    ) -> Tuple[Path, Path]:
        variant = btrfs_logo.variant
        size = btrfs_logo.size
        horizontal_alignment = btrfs_logo.horizontal_alignment
        vertical_alignment = btrfs_logo.vertical_alignment
        btrfs_logos_directory = constants.BTRFS_LOGOS_DIR
        btrfs_logo_name = f"{variant.value}_{size.value}.png"
        btrfs_logo_absolute_path = btrfs_logos_directory / btrfs_logo_name
        refind_directory = refind_config_path.parent
        destination_directory = (
            refind_directory / constants.SNAPSHOT_STANZAS_DIR_NAME / constants.ICONS_DIR
        )
        destination_icon_name = (
            f"{source_icon_absolute_path.stem}_{btrfs_logo_absolute_path.stem}_"
            f"h-{horizontal_alignment.value}_v-{vertical_alignment.value}.png"
        )
        destination_icon_absolute_path = destination_directory / destination_icon_name

        return (btrfs_logo_absolute_path, destination_icon_absolute_path)
