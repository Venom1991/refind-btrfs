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

from __future__ import annotations

from pathlib import Path
from typing import Optional

from refind_btrfs.common.abc.factories import BaseSubvolumeCommandFactory
from refind_btrfs.utility.helpers import is_none_or_whitespace

from .mount_options import MountOptions
from .subvolume import Subvolume


class Filesystem:
    def __init__(self, uuid: str, label: str, fs_type: str, mount_point: str) -> None:
        self._uuid = uuid
        self._label = label
        self._fs_type = fs_type
        self._mount_point = mount_point
        self._dump: Optional[int] = None
        self._fsck: Optional[int] = None
        self._mount_options: Optional[MountOptions] = None
        self._subvolume: Optional[Subvolume] = None

    def with_dump_and_fsck(self, dump: int, fsck: int) -> Filesystem:
        self._dump = dump
        self._fsck = fsck

        return self

    def with_mount_options(self, raw_mount_options: str) -> Filesystem:
        self._mount_options = (
            MountOptions(raw_mount_options)
            if not is_none_or_whitespace(raw_mount_options)
            else None
        )

        return self

    def initialize_subvolume_using(
        self, subvolume_command_factory: BaseSubvolumeCommandFactory
    ) -> None:
        if not self.has_subvolume():
            filesystem_path = Path(self.mount_point)
            subvolume_command = subvolume_command_factory.subvolume_command()
            subvolume = subvolume_command.get_subvolume_from(filesystem_path)

            if subvolume is not None:
                snapshots = subvolume_command.get_snapshots_for(subvolume)

                self._subvolume = subvolume.with_snapshots(snapshots)

    def is_of_type(self, fs_type: str) -> bool:
        return self.fs_type == fs_type

    def is_mounted(self) -> bool:
        return not is_none_or_whitespace(self.mount_point)

    def is_mounted_at(self, path: Path) -> bool:
        return self.is_mounted() and Path(self.mount_point) == path

    def has_subvolume(self) -> bool:
        return self.subvolume is not None

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def label(self) -> str:
        return self._label

    @property
    def fs_type(self) -> str:
        return self._fs_type

    @property
    def mount_point(self) -> str:
        return self._mount_point

    @property
    def dump(self) -> Optional[int]:
        return self._dump

    @property
    def fsck(self) -> Optional[int]:
        return self._fsck

    @property
    def mount_options(self) -> Optional[MountOptions]:
        return self._mount_options

    @property
    def subvolume(self) -> Optional[Subvolume]:
        return self._subvolume
