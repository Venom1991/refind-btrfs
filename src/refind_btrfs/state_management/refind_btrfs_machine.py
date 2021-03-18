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

from typing import Collection

from injector import inject
from more_itertools import first, last
from transitions import Machine, State

from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.enums import StateNames
from refind_btrfs.common.exceptions import (
    PartitionError,
    RefindConfigError,
    SubvolumeError,
    UnchangedConfiguration,
)
from refind_btrfs.utility.helpers import checked_cast, has_items, is_singleton

from .model import Model

States = Collection[State]


class RefindBtrfsMachine(Machine):
    @inject
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
        model: Model,
        states: States,
    ):
        self._logger = logger_factory.logger(__name__)

        if not has_items(states) or is_singleton(states):
            raise ValueError(
                "The 'states' collection must be initialized and contain at least two items!"
            )

        initial = checked_cast(State, first(states))
        expected_initial_name: str = StateNames.INITIAL.value

        if initial.name != expected_initial_name:
            raise ValueError(
                "The first item of the 'states' collection must "
                f"be a state named '{expected_initial_name}'!"
            )

        final = checked_cast(State, last(states))
        expected_final_name: str = StateNames.FINAL.value

        if final.name != expected_final_name:
            raise ValueError(
                "The last item of the 'states' collection must "
                f"be a state named '{expected_final_name}'!"
            )

        conditions = model.conditions

        super().__init__(
            model=model,
            states=list(states),
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
                if model.is_final():
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
