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

from __future__ import annotations

from abc import ABC
from os import stat_result
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

from refind_btrfs.common.enums import ConfigInitializationType
from refind_btrfs.utility.helpers import checked_cast, none_throws

TDerived = TypeVar("TDerived")


class BaseConfig(ABC):
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._file_stat: Optional[stat_result] = None
        self._initialization_type: Optional[ConfigInitializationType] = None

        self.refresh_file_stat()

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True

        if isinstance(other, BaseConfig):
            self_file_path_resolved = self.file_path.resolve()
            other_file_path_resolved = other.file_path.resolve()

            return self_file_path_resolved == other_file_path_resolved

        return False

    def __hash__(self) -> int:
        return hash(self.file_path.resolve())

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        initialization_type_key = "_initialization_type"

        if initialization_type_key in state:
            del state[initialization_type_key]

        return state

    def with_initialization_type(
        self,
        initialization_type: ConfigInitializationType,
        derived_type: Type[TDerived],
    ) -> TDerived:
        self._initialization_type = initialization_type

        return checked_cast(derived_type, self)

    def refresh_file_stat(self):
        file_path = self.file_path

        if file_path.exists():
            self._file_stat = file_path.stat()

    def is_modified(self, actual_file_path: Path) -> bool:
        current_file_path = self.file_path

        if current_file_path != actual_file_path:
            return True

        current_file_stat = none_throws(self.file_stat)

        if actual_file_path.exists():
            actual_file_stat = actual_file_path.stat()

            return current_file_stat.st_mtime != actual_file_stat.st_mtime

        return True

    def is_of_initialization_type(
        self, initialization_type: ConfigInitializationType
    ) -> bool:
        return self.initialization_type == initialization_type

    @property
    def file_path(self) -> Path:
        return self._file_path

    @property
    def file_stat(self) -> Optional[stat_result]:
        return self._file_stat

    @property
    def initialization_type(self) -> Optional[ConfigInitializationType]:
        return self._initialization_type
