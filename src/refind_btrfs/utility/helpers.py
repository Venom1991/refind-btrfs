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

import errno
import os
import re
from inspect import ismethod
from pathlib import Path
from typing import Any, Generator, Optional, Sized, Tuple, TypeVar
from uuid import UUID

from refind_btrfs.common import constants
from refind_btrfs.common.enums import PathRelation


def check_access_rights() -> None:
    if os.getuid() != constants.ROOT_UID:
        error_code = errno.EPERM

        raise PermissionError(error_code, os.strerror(error_code))


def try_parse_int(value: str, base: int = 10) -> Optional[int]:
    try:
        return int(value, base)
    except ValueError:
        return None


def try_parse_uuid(value: str) -> Optional[UUID]:
    try:
        return UUID(hex=value)
    except ValueError:
        return None


def try_convert_bytes_to_uuid(value: bytes) -> Optional[UUID]:
    try:
        return UUID(bytes=value)
    except ValueError:
        return None


def is_empty(value: Optional[str]) -> bool:
    if value is None:
        return False

    return value == constants.EMPTY_STR


def is_none_or_whitespace(value: Optional[str]) -> bool:
    if value is None:
        return True

    return value == constants.EMPTY_STR or value.isspace()


def has_method(obj: Any, method_name: str) -> bool:
    if hasattr(obj, method_name):
        attr = getattr(obj, method_name)

        return ismethod(attr)

    return False


def has_items(value: Optional[Sized]) -> bool:
    return value is not None and len(value) > 0


def is_singleton(value: Optional[Sized]) -> bool:
    return value is not None and len(value) == 1


def item_count_suffix(value: Sized) -> str:
    assert has_items(
        value
    ), "The 'value' parameter must be initialized and contain least one item!"

    return constants.EMPTY_STR if is_singleton(value) else "s"


def find_all_matched_files_in(
    root_directory: Path, file_name: str
) -> Generator[Path, None, None]:
    if root_directory.exists() and root_directory.is_dir():
        children = root_directory.iterdir()

        for child in children:
            if child.is_file():
                if child.name == file_name:
                    yield child
            elif child.is_dir():
                yield from find_all_matched_files_in(child, file_name)


def find_all_directories_in(
    root_directory: Path, max_depth: int, current_depth: int = 0
) -> Generator[Path, None, None]:
    if current_depth > max_depth:
        return

    if root_directory.exists() and root_directory.is_dir():
        yield root_directory.resolve()

        subdirectories = (child for child in root_directory.iterdir() if child.is_dir())

        for subdirectory in subdirectories:
            yield from find_all_directories_in(
                subdirectory, max_depth, current_depth + 1
            )


def discern_path_relation_of(first: Path, second: Path) -> PathRelation:
    first_resolved = first.resolve()
    second_resolved = second.resolve()

    if first_resolved == second_resolved:
        return PathRelation.SAME

    first_parents = first_resolved.parents

    if second_resolved in first_parents:
        return PathRelation.FIRST_NESTED_IN_SECOND

    second_parents = second_resolved.parents

    if first_resolved in second_parents:
        return PathRelation.SECOND_NESTED_IN_FIRST

    return PathRelation.UNRELATED


def discern_distance_between(first: Path, second: Path) -> Optional[int]:
    path_relation = discern_path_relation_of(first, second)

    if path_relation != PathRelation.UNRELATED:
        distance = 0

        if path_relation != PathRelation.SAME:
            if path_relation == PathRelation.FIRST_NESTED_IN_SECOND:
                first_parts = first.parts
                second_stem = second.stem

                for part in reversed(first_parts):
                    if part != second_stem:
                        distance += 1
                    else:
                        break
            elif path_relation == PathRelation.SECOND_NESTED_IN_FIRST:
                first_stem = first.stem
                second_parts = second.parts

                for part in reversed(second_parts):
                    if part != first_stem:
                        distance += 1
                    else:
                        break

        return distance

    return None


def replace_root_in_path(
    full_path: str,
    current_root_part: str,
    replacement_root_part: str,
    dir_separator_replacement: Optional[Tuple[str, str]] = None,
) -> str:
    pattern = re.compile(
        rf"(?P<prefix>^{constants.DIR_SEPARATOR_PATTERN}?)"
        f"{current_root_part}"
        rf"(?P<suffix>{constants.DIR_SEPARATOR_PATTERN})"
    )
    substituted_full_path = pattern.sub(
        rf"\g<prefix>{replacement_root_part}\g<suffix>", full_path
    )

    if dir_separator_replacement is not None:
        return substituted_full_path.replace(
            dir_separator_replacement[0], dir_separator_replacement[1]
        )

    return substituted_full_path


_T = TypeVar("_T")


def none_throws(value: Optional[_T], message: str = "Unexpected 'None'") -> _T:
    if value is None:
        raise AssertionError(message)

    return value


def default_if_none(value: Optional[_T], default: _T) -> _T:
    if value is None:
        return default

    return value
