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

from injector import inject

from refind_btrfs.common.abc.commands import DeviceCommand, SubvolumeCommand
from refind_btrfs.common.abc.factories import (
    BaseDeviceCommandFactory,
    BaseLoggerFactory,
    BaseSubvolumeCommandFactory,
)
from refind_btrfs.common.abc.providers import BasePackageConfigProvider

from .btrfsutil_command import BtrfsUtilCommand
from .findmnt_command import FindmntCommand
from .fstab_command import FstabCommand
from .lsblk_command import LsblkCommand


class SystemDeviceCommandFactory(BaseDeviceCommandFactory):
    @inject
    def __init__(self, logger_factory: BaseLoggerFactory) -> None:
        self._logger_factory = logger_factory

    def physical_device_command(self) -> DeviceCommand:
        return LsblkCommand(self._logger_factory)

    def live_device_command(self) -> DeviceCommand:
        return FindmntCommand(self._logger_factory)

    def static_device_command(self) -> DeviceCommand:
        return FstabCommand(self._logger_factory)


class BtrfsUtilSubvolumeCommandFactory(BaseSubvolumeCommandFactory):
    @inject
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
        package_config_provider: BasePackageConfigProvider,
    ) -> None:
        self._logger_factory = logger_factory
        self._package_config_provider = package_config_provider

    def subvolume_command(self) -> SubvolumeCommand:
        return BtrfsUtilCommand(self._logger_factory, self._package_config_provider)
