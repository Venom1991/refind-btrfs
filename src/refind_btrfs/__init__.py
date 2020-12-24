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

from argparse import ArgumentParser
from typing import Optional, cast

from injector import Injector

from refind_btrfs.common.abc import BaseRunner
from refind_btrfs.common.enums import RunMode
from refind_btrfs.utility import helpers
from refind_btrfs.utility.injector_modules import CLIModule, WatchdogModule


def main() -> int:
    one_time_mode = RunMode.ONE_TIME.value
    background_mode = RunMode.BACKGROUND.value
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
    run_mode = cast(str, helpers.none_throws(arguments.run_mode))
    injector: Optional[Injector] = None

    if run_mode == one_time_mode:
        injector = Injector(CLIModule)
    elif run_mode == background_mode:
        injector = Injector(WatchdogModule)

    runner = injector.get(BaseRunner)

    return runner.run()
