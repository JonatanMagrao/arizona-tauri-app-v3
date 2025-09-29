from pathlib import Path
from typing import Iterable
from functions import find_file_in_tree_from
from classes.SuperplayVideoProjectCopy import SuperplayVideoProject
from classes.LocalPathHelper import LocalPathHelper


class ProjectTypeIdentifier():
    def __init__(self, config: dict, google_data: dict) -> None:
        self.local_path_helper = LocalPathHelper(config, google_data)
        self.gdrive_local_path = self.local_path_helper.google_drive_local_path
        self.local_path = self.local_path_helper.full_local_path
        self._config = config
        self.project_types: dict = self._config.get("project_types")

    @property
    def _find_file_in_tree(self) -> Path | None:
        return find_file_in_tree_from(self.gdrive_local_path)

    @property
    def _project_type(self):
        file = self._find_file_in_tree
        project_stem = file.stem.split("_")[0]
        project_type = project_stem.split("-")[1]

        if project_type not in self.project_types.keys():
            raise ValueError(
                f"⚠️  Unknown project type: '{project_type}' in {project_stem}")

        return self.project_types.get(project_type).get("label")

    @property
    def _has_only_folder(self) -> bool:
        return all([content.is_dir() for content in self.gdrive_local_path.iterdir()])

    @property
    def _has_only_files(self) -> bool:
        return all([content.is_file() for content in self.gdrive_local_path.iterdir()])

    @property
    def _has_mp4_file(self) -> bool:
        return any([content.suffix.lower() == ".mp4" for content in self.gdrive_local_path.iterdir()])

    @property
    def create_projects(self):
        if self._project_type == "Video":
            return SuperplayVideoProject(self._config, self.gdrive_local_path, self.local_path)

        else:
            raise NotImplementedError(f"⚠️  Project type '{self._project_type}' is not implemented yet.")
