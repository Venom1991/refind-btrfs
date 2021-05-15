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

import os
from argparse import ArgumentParser
from typing import Optional

from injector import Injector

from refind_btrfs.common import constants
from refind_btrfs.common.abc import BaseRunner
from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.enums import RunMode
from refind_btrfs.common.exceptions import PackageConfigError
from refind_btrfs.utility.helpers import check_access_rights, checked_cast, none_throws
from refind_btrfs.utility.injector_modules import CLIModule, WatchdogModule


def initialize_injector() -> Optional[Injector]:
    one_time_mode: str = RunMode.ONE_TIME.value
    background_mode: str = RunMode.BACKGROUND.value
    parser = ArgumentParser(
        prog="refind-btrfs",
        usage="%(prog)s [options]",
        description="Generate rEFInd manual boot stanzas from Btrfs snapshots",
    )

    parser.add_argument(
        "-rm",
        "--run-mode",
        help="Mode of execution",
        choices=[one_time_mode, background_mode],
        type=str,
        nargs="?",
        const=one_time_mode,
        default=one_time_mode,
    )

    arguments = parser.parse_args()
    run_mode = checked_cast(str, none_throws(arguments.run_mode))

    if run_mode == one_time_mode:
        return Injector(CLIModule)
    elif run_mode == background_mode:
        return Injector(WatchdogModule)

    return None


def main() -> int:
    exit_code = os.EX_OK
    injector = none_throws(initialize_injector())
    logger_factory = injector.get(BaseLoggerFactory)
    logger = logger_factory.logger(__name__)

    try:
        check_access_rights()

        runner = injector.get(BaseRunner)
        exit_code = runner.run()
    except PackageConfigError as e:
        exit_code = constants.EX_NOT_OK
        logger.error(e.formatted_message)
    except PermissionError as e:
        exit_code = e.errno
        logger.error(e.strerror)
    except Exception:
        exit_code = constants.EX_NOT_OK
        logger.exception(constants.MESSAGE_UNEXPECTED_ERROR)

    return exit_code
