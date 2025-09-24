from pathlib import Path
from functions import normalize_old_project_name
from classes.SuperplayProject import SuperplayProject
import re
from typing import Optional

LANGUAGE_PATTERN_LIST = [
    r'_([A-Z]{2}(?:-[A-Z]{2})?)_\d{2,3}s',
]

IGNORE_LIST = [
    "Archive"
]

class SuperplayVideoProject(SuperplayProject):
    def __init__(self, config: dict, gdrive_local_path: Path, local_path: Path):
        super().__init__(config, gdrive_local_path, local_path)

    @property
    def duration(self) -> Optional[str]:
        """
        Retorna a duração em segundos encontrada no nome do primeiro .mp4
        (ex.: '120s' -> '120'), ou None se não encontrar.
        """
        for item in self.content:
            if item.is_file() and item.suffix.lower() == ".mp4":
                duration = re.search(
                    r"_(\d{2,3})s", item.stem, flags=re.IGNORECASE)
                if duration:
                    return duration.group(1)
        return None

    @property
    def language(self) -> str | None:
        # Tenta os padrões em ordem de mais específico para mais genérico
        for pattern in LANGUAGE_PATTERN_LIST:
            match = re.search(pattern, self.project_name)
            if match:
                return match.group(1)

        raise ValueError("Language not found in project name.")
    

    @property
    def root_master_folder_path(self) -> Path:
        if self.test:
            return Path(self.test_path) / "Render" / "MASTER" / self.language.upper()
        else:
            return self.find_path_anchor("Render") / "MASTER" / self.language.upper()

    @property
    def root_marketing_out_folder_path(self) -> Path:

        try:
            project_type = self.id.get("project_type")
            game_code = self.id.get("game_code").upper()
            game_code_path = self.game_info.get(
                game_code).get("mktout_folder_name")
            type_folder_path = self.project_types.get(
                project_type).get("folder_path")

            if self.test:
                return Path(self.test_path) / "Marketing OUT" / game_code_path / type_folder_path / self.language
            else:
                return Path(self.marketing_out_folder_path) / game_code_path / type_folder_path / self.language

        except Exception as e:
            raise e

    @property
    def master_folder_path(self) -> Path:
        root_master_folder_path = self.root_master_folder_path

        if not root_master_folder_path.exists():
            return root_master_folder_path / self.project_name

        if not root_master_folder_path.is_dir():
            raise NotADirectoryError(
                f"⚠️  Master root path is not a directory: {root_master_folder_path}")

        for folder_path in sorted(root_master_folder_path.iterdir()):
            if re.match(f"{self.game_code}-{self.project_type}-{self.project_number}-{self.iteration_number}_", folder_path.stem, flags=re.IGNORECASE):
                return folder_path

        return root_master_folder_path / self.project_name

    @property
    def marketing_out_game_folder_path(self) -> Path:
        root_marketing_out_folder_path: Path = self.root_marketing_out_folder_path

        if not root_marketing_out_folder_path.exists():
            return root_marketing_out_folder_path / normalize_old_project_name(self.game_name)

        if not root_marketing_out_folder_path.is_dir():
            raise NotADirectoryError(
                f"⚠️  Marketing OUT root path is not a directory: {root_marketing_out_folder_path}")

        for folder_path in sorted(root_marketing_out_folder_path.iterdir()):
            if re.match(f"{self.game_code}_{self.project_number}_", folder_path.stem, flags=re.IGNORECASE):
                return folder_path

            if re.match(f"{self.game_code}-{self.project_type}-{self.project_number}_", folder_path.stem, flags=re.IGNORECASE):
                return folder_path

        return root_marketing_out_folder_path / normalize_old_project_name(self.game_name)

    @property
    def marketing_out_folder_path(self) -> Path:
        marketing_out_game_folder_path: Path = self.marketing_out_game_folder_path

        if not marketing_out_game_folder_path.exists():
            return marketing_out_game_folder_path / self.project_name

        if not marketing_out_game_folder_path.is_dir():
            raise NotADirectoryError(
                f"⚠️  Marketing OUT root path is not a directory: {marketing_out_game_folder_path}")

        for folder_path in sorted(marketing_out_game_folder_path.iterdir()):
            if re.match(f"{self.game_code}-{self.project_type}-{self.project_number}-{self.iteration_number}_", folder_path.stem, flags=re.IGNORECASE):
                return folder_path

        return marketing_out_game_folder_path / self.project_name

    @property
    def remove_from_out(self):
        print("Implement")

    @property
    def job_manifest(self):
        
        if not self.language.lower() in self.supported_languages:
            raise ValueError(f"Language '{self.language}' is not supported.") 

        task = [self.gdrive_local_path, self.marketing_out_folder_path, self.master_folder_path]
        project = {
            "id": self.id,
            "project_name": self.project_name,
            "game": self.games.get(self.game_code).get("name"),
            "type_label": self.project_types.get(self.project_type).get("label"),
            "duration": self.duration,
            "language": self.supported_languages.get(self.language.lower()),
            "copy_paths": task
        }
        return project
