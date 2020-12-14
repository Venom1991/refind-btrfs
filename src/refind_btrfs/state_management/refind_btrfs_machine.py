# region Licensing
# SPDX-FileCopyrightText: 2020 Luka Žaja <luka.zaja@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

""" refind-btrfs - Generate rEFInd manual boot stanzas from btrfs snapshots
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

from typing import List, Type, cast

from more_itertools import first
from transitions import Machine, State

from common.abc import BaseLoggerFactory
from common.exceptions import (
    PartitionError,
    RefindConfigError,
    SubvolumeError,
    UnchangedConfiguration,
)

from .model import Model


class RefindBtrfsMachine(Machine):
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
        model: Model,
        states: List[Type[State]],
    ):
        self._logger = logger_factory.logger(__name__)

        initial = cast(State, first(states))
        conditions = model.conditions

        super().__init__(
            model=model,
            states=states,
            initial=initial,
            auto_transitions=False,
            name=__name__,
        )
        self.add_ordered_transitions(
            loop=False,
            conditions=conditions,
        )

        self._initial_state = initial

    def run(self) -> bool:
        logger = self._logger
        model = self.model
        initial_state = self._initial_state

        self.set_state(initial_state)

        try:
            while model.next_state():
                if model.is_process_changes():
                    return True
        except UnchangedConfiguration as e:
            logger.warning(e.formatted_message)
            return True
        except (
            PartitionError,
            SubvolumeError,
            RefindConfigError,
        ) as e:
            logger.error(e.formatted_message)

        return False
