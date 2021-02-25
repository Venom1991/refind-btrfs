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

from injector import inject

from refind_btrfs.common import constants
from refind_btrfs.common.abc import BaseRunner
from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.exceptions import UnsupportedConfiguration
from refind_btrfs.state_management import RefindBtrfsMachine


class CLIRunner(BaseRunner):
    @inject
    def __init__(
        self, logger_factory: BaseLoggerFactory, machine: RefindBtrfsMachine
    ) -> None:
        self._logger = logger_factory.logger(__name__)
        self._machine = machine

    def run(self) -> int:
        logger = self._logger
        machine = self._machine
        exit_code = os.EX_OK

        try:
            if not machine.run():
                exit_code = constants.EX_NOT_OK
        except UnsupportedConfiguration as e:
            logger.warning(e.formatted_message)
        except KeyboardInterrupt:
            exit_code = constants.EX_CTRL_C_INTERRUPT
            logger.warning(constants.MESSAGE_CTRL_C_INTERRUPT)

        return exit_code
