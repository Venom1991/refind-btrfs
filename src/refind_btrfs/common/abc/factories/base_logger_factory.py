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

import logging
from abc import ABC, abstractmethod
from logging import Handler, Logger

from refind_btrfs.utility import LevelAwareFormatter


class BaseLoggerFactory(ABC):
    def logger(self, name: str) -> Logger:
        logger = logging.getLogger(name)

        if not logger.hasHandlers():
            logging_handler = self.get_handler()
            formatter = LevelAwareFormatter()

            logger.propagate = False
            logger.setLevel(logging.INFO)
            logging_handler.setLevel(logging.INFO)
            logging_handler.setFormatter(formatter)
            logger.addHandler(logging_handler)

        return logger

    @abstractmethod
    def get_handler(self) -> Handler:
        pass
