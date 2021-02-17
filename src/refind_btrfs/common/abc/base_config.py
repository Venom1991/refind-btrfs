from abc import ABC
from os import stat_result
from pathlib import Path
from typing import Optional

from refind_btrfs.utility.helpers import none_throws


class BaseConfig(ABC):
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._file_stat: Optional[stat_result] = None

        self.refresh_file_stat()

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True

        if isinstance(other, BaseConfig):
            self_file_path_resolved = self.file_path.resolve()
            other_file_path_resolved = other.file_path.resolve()

            return self_file_path_resolved == other_file_path_resolved

        return False

    def __hash__(self) -> int:
        return hash(self.file_path.resolve())

    def refresh_file_stat(self):
        file_path = self.file_path

        if file_path.exists():
            self._file_stat = file_path.stat()

    def has_been_modified(self, actual_file_path: Path) -> bool:
        current_file_path = self.file_path

        if current_file_path != actual_file_path:
            return True

        current_file_stat = none_throws(self.file_stat)
        actual_file_stat = actual_file_path.stat()

        return current_file_stat.st_mtime != actual_file_stat.st_mtime

    @property
    def file_path(self) -> Path:
        return self._file_path

    @property
    def file_stat(self) -> Optional[stat_result]:
        return self._file_stat
