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

import queue

from injector import inject

from refind_btrfs.common import CheckableObserver, constants
from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.exceptions import UnsupportedConfiguration


class SnapshotObserver(CheckableObserver):
    @inject
    def __init__(self, logger_factory: BaseLoggerFactory):
        super().__init__()

        self._logger = logger_factory.logger(__name__)

    def run(self) -> None:
        logger = self._logger

        while self.should_keep_running():
            try:
                self.dispatch_events(self.event_queue, self.timeout)
            except queue.Empty:
                continue
            except UnsupportedConfiguration as e:
                logger.warning(e.formatted_message)
                self._exception = e
                self.stop()
            except Exception as e:
                logger.exception(constants.MESSAGE_UNEXPECTED_ERROR)
                self._exception = e
                self.stop()
