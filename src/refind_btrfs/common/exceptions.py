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

from more_itertools import first_true

from refind_btrfs.common import constants
from refind_btrfs.utility.helpers import checked_cast


class RefindBtrfsError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(args)

        if args is not None:
            self._message = checked_cast(
                str,
                first_true(
                    args,
                    pred=lambda arg: isinstance(arg, str),
                    default=constants.EMPTY_STR,
                ),
            )
        else:
            self._message = constants.EMPTY_STR

    def __str__(self) -> str:
        return f"{self.error_type_name}: {self.formatted_message}"

    @property
    def formatted_message(self) -> str:
        return self._message

    @property
    def error_type_name(self) -> str:
        return type(self).__name__


class PartitionError(RefindBtrfsError):
    pass


class SubvolumeError(RefindBtrfsError):
    pass


class PackageConfigError(RefindBtrfsError):
    pass


class RefindConfigError(RefindBtrfsError):
    pass


class RefindSyntaxError(RefindBtrfsError):
    def __init__(self, line, column, message) -> None:
        super().__init__(message)

        self._line = line
        self._column = column

    @property
    def formatted_message(self) -> str:
        return (
            f"line - {self._line}, column - {self._column}, message - '{self._message}'"
        )


class UnsupportedConfiguration(RefindBtrfsError):
    pass


class UnchangedConfiguration(RefindBtrfsError):
    pass
