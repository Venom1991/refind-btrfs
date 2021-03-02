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

from enum import Enum, auto, unique
from typing import Any, List


class AutoNameToLower(Enum):
    # pylint: disable=unused-argument
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: List[Any]
    ) -> Any:
        return name.lower()


@unique
class RunMode(Enum):
    ONE_TIME = "one-time"
    BACKGROUND = "background"


@unique
class LsblkJsonKey(Enum):
    BLOCKDEVICES = "blockdevices"
    CHILDREN = "children"


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
class FindmntJsonKey(Enum):
    FILESYSTEMS = "filesystems"


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
class TopLevelConfigKey(Enum):
    EXIT_IF_ROOT_IS_SNAPSHOT = "exit_if_root_is_snapshot"
    SNAPSHOT_SEARCH = "snapshot-search"
    SNAPSHOT_MANIPULATION = "snapshot-manipulation"
    BOOT_STANZA_GENERATION = "boot-stanza-generation"


@unique
class SnapshotSearchConfigKey(Enum):
    DIRECTORY = "dir"
    IS_NESTED = "is_nested"
    MAX_DEPTH = "max_depth"


@unique
class SnapshotManipulationConfigKey(Enum):
    SELECTION_COUNT = "selection_count"
    MODIFY_READ_ONLY_FLAG = "modify_read_only_flag"
    DESTINATION_DIRECTORY = "destination_dir"
    CLEANUP_EXCLUSION = "cleanup_exclusion"


@unique
class BootStanzaGenerationConfigKey(Enum):
    REFIND_CONFIG = "refind_config"
    INCLUDE_PATHS = "include_paths"
    INCLUDE_SUB_MENUS = "include_sub_menus"


@unique
class LocalDbKey(Enum):
    PACKAGE_CONFIG = "package_config"
    REFIND_CONFIGS = "refind_configs"
    PROCESSING_RESULT = "processing_result"


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
class GraphicsParameter(Enum):
    ON = "on"
    OFF = "off"


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
