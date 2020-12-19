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

from enum import Enum, unique


@unique
class RunMode(Enum):
    ONE_TIME = "one-time"
    BACKGROUND = "background"


@unique
class LsblkJsonKey(Enum):
    BLOCKDEVICES = "blockdevices"
    PARTITIONS = "children"


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
    PARTITIONS = "filesystems"


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
    COUNT = "count"
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
    MENU_ENTRY = "menuentry"
    VOLUME = "volume"
    LOADER = "loader"
    INITRD = "initrd"
    ICON = "icon"
    OS_TYPE = "ostype"
    GRAPHICS = "graphics"
    BOOT_OPTIONS = "options"
    ADD_BOOT_OPTIONS = "add_options"
    DISABLED = "disabled"
    SUB_MENU_ENTRY = "submenuentry"
    INCLUDE = "include"


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
class States(Enum):
    INITIAL = "initial"
    INIT_BLOCK_DEVICES = "init_block_devices"
    INIT_BTRFS_METADATA = "init_btrfs_metadata"
    INIT_REFIND_CONFIG = "init_refind_config"
    PREPARE_SNAPSHOTS = "prepare_snapshots"
    PROCESS_CHANGES = "process_changes"
    FINAL = "final"
