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
import signal
from signal import signal as register_signal_handler
from types import FrameType
from typing import Optional

import systemd.daemon as systemd_daemon
from injector import inject
from pid import PidFile, PidFileAlreadyRunningError
from watchdog.events import FileSystemEventHandler

from refind_btrfs.common import CheckableObserver, constants
from refind_btrfs.common.abc import BaseRunner
from refind_btrfs.common.abc.factories import BaseLoggerFactory
from refind_btrfs.common.abc.providers import BasePackageConfigProvider
from refind_btrfs.common.exceptions import UnsupportedConfiguration
from refind_btrfs.utility.helpers import checked_cast


class WatchdogRunner(BaseRunner):
    @inject
    def __init__(
        self,
        logger_factory: BaseLoggerFactory,
        package_config_provider: BasePackageConfigProvider,
        observer: CheckableObserver,
        event_handler: FileSystemEventHandler,
    ) -> None:
        self._logger = logger_factory.logger(__name__)
        self._package_config_provider = package_config_provider
        self._observer = observer
        self._snapshot_event_handler = event_handler
        self._current_pid = os.getpid()

        register_signal_handler(signal.SIGTERM, self._terminate)

    def run(self) -> int:
        logger = self._logger
        package_config_provider = self._package_config_provider
        observer = self._observer
        event_handler = self._snapshot_event_handler
        current_pid = self._current_pid
        exit_code = os.EX_OK

        try:
            with PidFile(
                pidname=constants.BACKGROUND_MODE_PID_NAME, lock_pidfile=False
            ) as pid_file:
                current_pid = pid_file.pid
                package_config = package_config_provider.get_config()
                directories_for_watch = [
                    str(directory)
                    for directory in sorted(package_config.directories_for_watch)
                ]

                logger.info(
                    "Scheduling watch for directories: "
                    f"{constants.DEFAULT_ITEMS_SEPARATOR.join(directories_for_watch)}."
                )

                for directory in directories_for_watch:
                    observer.schedule(
                        event_handler,
                        directory,
                        recursive=False,
                    )

                logger.info(f"Starting the observer with PID {current_pid}.")

                observer.start()
                systemd_daemon.notify(constants.NOTIFICATION_READY, pid=current_pid)

                while observer.is_alive():
                    observer.join(constants.WATCH_TIMEOUT)

                observer.join()
        except PidFileAlreadyRunningError as e:
            exit_code = constants.EX_NOT_OK
            running_pid = checked_cast(int, e.pid)

            logger.error(e.message)
            systemd_daemon.notify(
                constants.NOTIFICATION_STATUS.format(
                    f"Detected an attempt to run subsequently with PID {current_pid}."
                ),
                pid=running_pid,
            )
        else:
            try:
                observer.check()
            except UnsupportedConfiguration:
                pass
            except Exception:
                exit_code = constants.EX_NOT_OK

        if exit_code != os.EX_OK:
            systemd_daemon.notify(
                constants.NOTIFICATION_ERRNO.format(exit_code), pid=current_pid
            )

        return exit_code

    # pylint: disable=unused-argument
    def _terminate(self, signal_number: int, frame: Optional[FrameType]) -> None:
        logger = self._logger
        observer = self._observer
        current_pid = self._current_pid

        logger.info(
            f"Received terminating signal {signal_number}, stopping the observer..."
        )
        systemd_daemon.notify(constants.NOTIFICATION_STOPPING, pid=current_pid)

        if observer.is_alive():
            observer.stop()
            observer.join()
