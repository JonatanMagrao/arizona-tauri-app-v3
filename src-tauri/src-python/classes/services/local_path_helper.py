import platform
import string
import os
import re
from pathlib import Path
import sys
from classes.commons.shared_drives import full_local_path

class LocalPathHelper:
    def __init__(self, config: dict, google_data: dict):
        self.is_mac = platform.system().lower() == "darwin"
        self._config = config
        self.shared_drive_labels = self._config.get("shared_drive_labels")
        self.google_path = google_data.get("path")        

    @property
    def full_local_path(self) -> Path:
        """Automatically selects the correct resolver based on the OS."""
        return full_local_path()
    
    @property
    def google_drive_local_path(self) -> Path:
        level = 5 if self.is_mac else 2
        return Path(self._get_path_levels(level)).joinpath(*self.google_path)

    def _get_path_levels(self, levels: int = 2) -> Path | None:
        """
        Returns the top N levels of a given path as a new Path object.

        :param path: Input path (str or Path)
        :param levels: Number of top levels to include (must be >= 2)
        :return: A new Path object with the top levels, or None if invalid
        """
        if levels < 2:
            print("The number of levels must be at least 2.")
            return None

        path = self.full_local_path

        if levels > len(path.parts):
            print(
                "The requested number of levels exceeds the path depth.")
            return None

        return Path(*path.parts[:levels])
