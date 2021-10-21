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

from enum import Enum, auto, unique
from typing import Any


class AutoNameToLower(Enum):
    # pylint: disable=arguments-differ, unused-argument
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
        return name.lower()


@unique
class RunMode(AutoNameToLower):
    ONE_TIME = "one-time"
    BACKGROUND = auto()


@unique
class LsblkJsonKey(AutoNameToLower):
    BLOCKDEVICES = auto()
    CHILDREN = auto()


@unique
class LsblkColumn(Enum):
    DEVICE_NAME = "name"
    DEVICE_TYPE = "type"
    MAJOR_MINOR = "maj:min"
    PTABLE_UUID = "ptuuid"
    PTABLE_TYPE = "pttype"
    PART_UUID = "partuuid"
    PART_TYPE = "parttype"
    PART_LABEL = "partlabel"
    FS_UUID = "uuid"
    FS_TYPE = "fstype"
    FS_LABEL = "label"
    FS_MOUNT_POINT = "mountpoint"


@unique
class FindmntJsonKey(AutoNameToLower):
    FILESYSTEMS = auto()


@unique
class FindmntColumn(Enum):
    DEVICE_NAME = "source"
    PART_UUID = "partuuid"
    PART_LABEL = "partlabel"
    FS_UUID = "uuid"
    FS_TYPE = "fstype"
    FS_LABEL = "label"
    FS_MOUNT_POINT = "target"
    FS_MOUNT_OPTIONS = "options"


@unique
class FstabColumn(Enum):
    DEVICE_NAME = 0
    FS_MOUNT_POINT = 1
    FS_TYPE = 2
    FS_MOUNT_OPTIONS = 3
    FS_DUMP = 4
    FS_FSCK = 5


@unique
class PathRelation(Enum):
    UNRELATED = 0
    SAME = 1
    FIRST_NESTED_IN_SECOND = 2
    SECOND_NESTED_IN_FIRST = 3


@unique
class ConfigInitializationType(Enum):
    PARSED = 0
    PERSISTED = 1


@unique
class TopLevelConfigKey(AutoNameToLower):
    EXIT_IF_ROOT_IS_SNAPSHOT = auto()
    EXIT_IF_NO_CHANGES_ARE_DETECTED = auto()
    ESP_UUID = auto()
    SNAPSHOT_SEARCH = "snapshot-search"
    SNAPSHOT_MANIPULATION = "snapshot-manipulation"
    BOOT_STANZA_GENERATION = "boot-stanza-generation"


@unique
class SnapshotSearchConfigKey(AutoNameToLower):
    DIRECTORY = auto()
    IS_NESTED = auto()
    MAX_DEPTH = auto()


@unique
class SnapshotManipulationConfigKey(AutoNameToLower):
    SELECTION_COUNT = auto()
    MODIFY_READ_ONLY_FLAG = auto()
    DESTINATION_DIRECTORY = auto()
    CLEANUP_EXCLUSION = auto()


@unique
class BootStanzaGenerationConfigKey(AutoNameToLower):
    REFIND_CONFIG = auto()
    INCLUDE_PATHS = auto()
    INCLUDE_SUB_MENUS = auto()
    ICON = auto()


@unique
class IconConfigKey(AutoNameToLower):
    MODE = auto()
    PATH = auto()
    BTRFS_LOGO = "btrfs-logo"


@unique
class BootStanzaIconGenerationMode(AutoNameToLower):
    DEFAULT = auto()
    CUSTOM = auto()
    EMBED_BTRFS_LOGO = auto()


@unique
class BtrfsLogoConfigKey(AutoNameToLower):
    VARIANT = auto()
    SIZE = auto()
    HORIZONTAL_ALIGNMENT = auto()
    VERTICAL_ALIGNMENT = auto()


@unique
class BtrfsLogoVariant(AutoNameToLower):
    ORIGINAL = auto()
    INVERTED = auto()


@unique
class BtrfsLogoSize(AutoNameToLower):
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()


@unique
class BtrfsLogoHorizontalAlignment(AutoNameToLower):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


@unique
class BtrfsLogoVerticalAlignment(AutoNameToLower):
    TOP = auto()
    CENTER = auto()
    BOTTOM = auto()


@unique
class LocalDbKey(AutoNameToLower):
    PACKAGE_CONFIG = auto()
    REFIND_CONFIGS = auto()
    PROCESSING_RESULT = auto()


@unique
class RefindOption(Enum):
    ADD_BOOT_OPTIONS = "add_options"
    BOOT_OPTIONS = "options"
    DISABLED = "disabled"
    FIRMWARE_BOOTNUM = "firmware_bootnum"
    GRAPHICS = "graphics"
    ICON = "icon"
    INCLUDE = "include"
    INITRD = "initrd"
    LOADER = "loader"
    MENU_ENTRY = "menuentry"
    OS_TYPE = "ostype"
    SUB_MENU_ENTRY = "submenuentry"
    VOLUME = "volume"


@unique
class OSTypeParameter(Enum):
    MAC_OS = "MacOS"
    LINUX = "Linux"
    ELILO = "ELILO"
    WINDOWS = "Windows"
    XOM = "XOM"


@unique
class GraphicsParameter(AutoNameToLower):
    ON = auto()
    OFF = auto()


@unique
class BootFilePathSource(Enum):
    BOOT_STANZA = 0
    SUB_MENU = 1


@unique
class StateNames(AutoNameToLower):
    INITIAL = auto()
    INITIALIZE_BLOCK_DEVICES = auto()
    INITIALIZE_ROOT_SUBVOLUME = auto()
    INITIALIZE_MATCHED_BOOT_STANZAS = auto()
    INITIALIZE_PREPARED_SNAPSHOTS = auto()
    COMBINE_BOOT_STANZAS_WITH_SNAPSHOTS = auto()
    PROCESS_CHANGES = auto()
    FINAL = auto()
