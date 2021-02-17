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

import shelve
from pathlib import Path
from typing import Dict, Optional, cast

from refind_btrfs.boot import RefindConfig
from refind_btrfs.common import constants, PackageConfig
from refind_btrfs.common.abc import BasePersistenceProvider
from refind_btrfs.common.enums import LocalDbKey
from refind_btrfs.state_management.model import ProcessingResult


class ShelvePersistenceProvider(BasePersistenceProvider):
    def __init__(self) -> None:
        self._db_filename = str(constants.DB_FILE)

    def get_package_config(self) -> Optional[PackageConfig]:
        db_key: str = LocalDbKey.PACKAGE_CONFIG.value

        with shelve.open(self._db_filename) as local_db:
            if db_key in local_db:
                package_config = cast(PackageConfig, local_db[db_key])

                if not package_config.has_been_modified(constants.PACKAGE_CONFIG_FILE):
                    return package_config

        return None

    def save_package_config(self, value: PackageConfig) -> None:
        db_key: str = LocalDbKey.PACKAGE_CONFIG.value

        with shelve.open(self._db_filename) as local_db:
            local_db[db_key] = value

    def get_refind_config(self, file_path: Path) -> Optional[RefindConfig]:
        db_key: str = LocalDbKey.REFIND_CONFIGS.value

        with shelve.open(self._db_filename) as local_db:
            if db_key in local_db:
                all_refind_configs = cast(Dict[Path, RefindConfig], local_db[db_key])
                refind_config = all_refind_configs.get(file_path)

                if refind_config is not None:
                    if refind_config.has_been_modified(file_path):
                        del all_refind_configs[file_path]

                        local_db[db_key] = all_refind_configs
                    else:
                        return refind_config

        return None

    def save_refind_config(self, value: RefindConfig) -> None:
        db_key: str = LocalDbKey.REFIND_CONFIGS.value

        with shelve.open(self._db_filename) as local_db:
            all_refind_configs: Optional[Dict[Path, RefindConfig]] = None

            if db_key in local_db:
                all_refind_configs = cast(Dict[Path, RefindConfig], local_db[db_key])
            else:
                all_refind_configs = {}

            file_path = value.file_path
            all_refind_configs[file_path] = value
            local_db[db_key] = all_refind_configs

    def get_previous_run_result(self) -> ProcessingResult:
        db_key: str = LocalDbKey.PROCESSING_RESULT.value

        with shelve.open(self._db_filename) as local_db:
            if db_key in local_db:
                return local_db[db_key]

        return ProcessingResult.none()

    def save_current_run_result(self, value: ProcessingResult) -> None:
        db_key: str = LocalDbKey.PROCESSING_RESULT.value

        with shelve.open(self._db_filename) as local_db:
            local_db[db_key] = value
