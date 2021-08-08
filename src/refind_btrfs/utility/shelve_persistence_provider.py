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

import shelve
from pathlib import Path
from shelve import Shelf
from typing import Any, Dict, Optional, TypeVar, cast

from semantic_version import Version

from refind_btrfs.boot import RefindConfig
from refind_btrfs.common import PackageConfig, constants
from refind_btrfs.common.abc.providers import BasePersistenceProvider
from refind_btrfs.common.enums import LocalDbKey
from refind_btrfs.state_management.model import ProcessingResult
from refind_btrfs.utility.helpers import checked_cast


class ShelvePersistenceProvider(BasePersistenceProvider):
    def __init__(self) -> None:
        self._db_filename = str(constants.DB_FILE)
        self._current_versions = {
            f"{LocalDbKey.PACKAGE_CONFIG.value}_"
            f"{constants.DB_ITEM_VERSION_SUFFIX}": Version("1.0.0"),
            f"{LocalDbKey.REFIND_CONFIGS.value}_"
            f"{constants.DB_ITEM_VERSION_SUFFIX}": Version("1.0.0"),
            f"{LocalDbKey.PROCESSING_RESULT.value}_"
            f"{constants.DB_ITEM_VERSION_SUFFIX}": Version("1.0.0"),
        }

    def get_package_config(self) -> Optional[PackageConfig]:
        db_key: str = LocalDbKey.PACKAGE_CONFIG.value

        with shelve.open(self._db_filename) as local_db:
            item = self._get_item(db_key, local_db)

            if item is not None:
                package_config = checked_cast(PackageConfig, item)

                if not package_config.has_been_modified(constants.PACKAGE_CONFIG_FILE):
                    return package_config

        return None

    def save_package_config(self, value: PackageConfig) -> None:
        db_key: str = LocalDbKey.PACKAGE_CONFIG.value

        with shelve.open(self._db_filename) as local_db:
            self._save_item(value, db_key, local_db)

    def get_refind_config(self, file_path: Path) -> Optional[RefindConfig]:
        db_key: str = LocalDbKey.REFIND_CONFIGS.value

        with shelve.open(self._db_filename) as local_db:
            item = self._get_item(db_key, local_db)

            if item is not None:
                all_refind_configs = checked_cast(Dict[Path, RefindConfig], item)
                refind_config = all_refind_configs.get(file_path)

                if refind_config is not None:
                    if refind_config.has_been_modified(file_path):
                        del all_refind_configs[file_path]

                        self._save_item(all_refind_configs, db_key, local_db)
                    else:
                        return refind_config

        return None

    def save_refind_config(self, value: RefindConfig) -> None:
        db_key: str = LocalDbKey.REFIND_CONFIGS.value

        with shelve.open(self._db_filename) as local_db:
            item = self._get_item(db_key, local_db)
            all_refind_configs: Optional[Dict[Path, RefindConfig]] = None

            if item is not None:
                all_refind_configs = checked_cast(Dict[Path, RefindConfig], item)
            else:
                all_refind_configs = {}

            file_path = value.file_path
            all_refind_configs[file_path] = value

            self._save_item(all_refind_configs, db_key, local_db)

    def get_previous_run_result(self) -> ProcessingResult:
        db_key: str = LocalDbKey.PROCESSING_RESULT.value

        with shelve.open(self._db_filename) as local_db:
            item = self._get_item(db_key, local_db)

            if item is not None:
                return cast(ProcessingResult, item)

        return ProcessingResult.none()

    def save_current_run_result(self, value: ProcessingResult) -> None:
        db_key: str = LocalDbKey.PROCESSING_RESULT.value

        with shelve.open(self._db_filename) as local_db:
            self._save_item(value, db_key, local_db)

    def _get_item(self, value_key: str, local_db: Shelf) -> Optional[Any]:
        version_key = f"{value_key}_{constants.DB_ITEM_VERSION_SUFFIX}"
        default_version = Version("0.0.0")
        current_version = self._current_versions[version_key]
        actual_version = (
            checked_cast(Version, local_db[version_key])
            if version_key in local_db
            else default_version
        )

        return local_db.get(value_key) if actual_version >= current_version else None

    _T = TypeVar("_T")

    def _save_item(self, item: _T, value_key: str, local_db: Shelf) -> None:
        version_key = f"{value_key}_{constants.DB_ITEM_VERSION_SUFFIX}"
        current_version = self._current_versions[version_key]

        local_db[value_key] = item
        local_db[version_key] = current_version
