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

import os
import signal
from signal import signal as register_signal_handler
from types import FrameType
from typing import Optional

from injector import inject
from pid import PidFile, PidFileAlreadyRunningError
from watchdog.events import FileSystemEventHandler

from refind_btrfs.common import CheckableObserver, constants
from refind_btrfs.common.abc import (
    BaseLoggerFactory,
    BasePackageConfigProvider,
    BaseRunner,
)
from refind_btrfs.common.exceptions import PackageConfigError, UnsupportedConfiguration
from refind_btrfs.utility import helpers


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
            helpers.check_access_rights()

            with PidFile(lock_pidfile=False) as pid_file:
                current_pid = pid_file.pid
                package_config = package_config_provider.get_config()
                watched_directories = sorted(
                    set(package_config.get_directories_for_watch())
                )
                separator = constants.COLUMN_SEPARATOR + constants.SPACE
                watched_directories_str = separator.join(
                    [str(directory) for directory in watched_directories]
                )

                logger.info(
                    f"Scheduling watch for directories {watched_directories_str}."
                )

                for directory in watched_directories:

                    observer.schedule(
                        event_handler,
                        str(directory),
                        recursive=False,
                    )

                logger.info(f"Starting the observer with PID {current_pid}.")

                observer.start()
        except PermissionError as e:
            exit_code = e.errno
            logger.error(e.strerror)
        except PidFileAlreadyRunningError as e:
            exit_code = constants.EX_NOT_OK
            logger.error(e.message)
        except PackageConfigError as e:
            exit_code = constants.EX_NOT_OK
            logger.error(e.formatted_message)
        except Exception:
            exit_code = constants.EX_NOT_OK
            logger.exception(constants.MESSAGE_UNEXPECTED_ERROR)
        else:
            while observer.is_alive():
                observer.join(constants.WATCH_TIMEOUT)

            observer.join()

            try:
                observer.check()
            except UnsupportedConfiguration:
                pass
            except Exception:
                exit_code = constants.EX_NOT_OK

        return exit_code

    def _terminate(self, signal_number: int, frame: Optional[FrameType]) -> None:
        # pylint: disable=unused-argument
        logger = self._logger
        observer = self._observer

        logger.info(
            f"Received terminating signal {signal_number}, stopping the observer..."
        )

        if observer.is_alive():
            observer.stop()
            observer.join()
