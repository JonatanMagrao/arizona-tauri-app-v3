from pathlib import Path
from functions import normalize_old_project_name
from classes.SuperplayProject import SuperplayProject
from classes.FileCopier import FileCopier
import re
from typing import Optional

LANGUAGE_PATTERN_LIST = [
    r'_([A-Z]{2}(?:-[A-Z]{2})?)_\d{2,3}s',
]

IGNORE_LIST = [
    "Archive",
    "_Archive"
]


class SuperplayVideoProject(SuperplayProject):
    def __init__(self, config: dict, gdrive_local_path: Path, local_path: Path):
        super().__init__(config, gdrive_local_path, local_path)
        self.ignore_list: dict = self.project_types.get(
            self.project_type).get("ignore_list")

    @property
    def _has_only_folder(self) -> bool:
        return all([content.is_dir() for content in self.content])

    def _get_project_name(self, src_folder: list[Path]) -> str:
        remove_resolution = re.compile(
            r"_\d{2,4}x\d{2,4}", flags=re.IGNORECASE)
        for item in src_folder:
            if item.is_file() and item.suffix.lower() == ".mp4":
                return remove_resolution.sub("", item.stem)

        raise Exception("Video to preview not found")

    def _build_project(self, src_folder: Path):
        project_content = [*src_folder.iterdir()]
        project_id = self.id
        project_name = self._get_project_name(project_content)
        game = self.game_info.get(self.game_code)
        type_label = self.project_types.get(self.project_type).get("label")
        duration = self._duration(project_content)
        language = self._language(project_name)
        language_full_info = self.supported_languages.get(language.lower())
        video_to_preview_path = self._video_to_preview_path(project_content)

        root_master_folder_path = self._root_master_folder_path(language)
        root_mktout_folder_path = self._root_marketing_out_folder_path(language)
        mktout_game_folder_path = self._marketing_out_game_folder_path(root_mktout_folder_path)

        src_folder_path = Path(src_folder)
        mktout_folder_path = self._marketing_out_folder_path(mktout_game_folder_path, project_name)
        master_folder_path = self._master_folder_path(root_master_folder_path, project_name)

        project = {
            "id": project_id,
            "project_name": project_name,
            "game": game,
            "type_label": type_label,
            "duration": duration,
            "language": language_full_info,
            "content": self._filter_content(project_content),
            "video_to_preview": video_to_preview_path,
            "copy_paths": [src_folder_path, mktout_folder_path, master_folder_path]
        }

        return project

    @property
    def job_manifest(self):
        if self._has_only_folder:
            projetos = []
            for src_folder in self.content:
                project = self._build_project(src_folder)
                projetos.append(project)
            return projetos

        else:
            return [self._build_project(self.gdrive_local_path)]

    def _duration(self, src_folder: list[Path]) -> Optional[str]:
        """
        Retorna a duração em segundos encontrada no nome do primeiro .mp4
        (ex.: '120s' -> '120'), ou None se não encontrar.
        """
        for item in src_folder:
            if item.is_file() and item.suffix.lower() == ".mp4":
                duration = re.search(
                    r"_(\d{2,3})s", item.stem, flags=re.IGNORECASE)
                if duration:
                    return duration.group(1)
        return None

    def _language(self, project_name: str) -> str | None:
        # Tenta os padrões em ordem de mais específico para mais genérico
        #! implementar caso encontre um idioma mas não está cadastrado
        for pattern in LANGUAGE_PATTERN_LIST:
            match = re.search(pattern, project_name)
            if match:
                return match.group(1)

        raise ValueError("Language not found in project name.")

    def _filter_content(self,content:list[Path]) -> list[Path]:
        contents = []
        ignore_file_extensions: list[str] = self.ignore_list.get("file_extensions")
        ignore_folder_names: list[str] = self.ignore_list.get("folder_names")

        ignore_exts = {ext.lower().strip() for ext in ignore_file_extensions}
        ignore_folders = {name.lower().strip() for name in ignore_folder_names}

        for item in content:
            if item.is_file() and item.suffix.lower().strip() not in ignore_exts:
                contents.append(item)

            if item.is_dir() and item.stem.lower().strip() not in ignore_folders:
                contents.append(item)

        return contents

    def _root_master_folder_path(self, language: str) -> Path:
        if self.test:
            return Path(self.test_path) / "Render" / "MASTER" / language.upper()
        else:
            return self.find_path_anchor("Render") / "MASTER" / language.upper()

    def _video_to_preview_path(self, src_folder: list):
        for item in src_folder:
            if item.is_file() and item.suffix.lower() == ".mp4":
                if re.search(r"_1080x1080", item.stem, flags=re.IGNORECASE):
                    return item

                if re.search(r"_1920x1080", item.stem, flags=re.IGNORECASE):
                    return item

                return item

        raise Exception("Video to preview not found")

    def _root_marketing_out_folder_path(self, language: str) -> Path:

        try:
            project_type = self.id.get("project_type")
            game_code = self.id.get("game_code").upper()
            game_code_path = self.game_info.get(
                game_code).get("mktout_folder_name")
            type_folder_path = self.project_types.get(
                project_type).get("folder_path")

            if self.test:
                return Path(self.test_path) / "Marketing OUT" / game_code_path / type_folder_path / language
            else:
                return Path(self.marketing_out_folder_path) / game_code_path / type_folder_path / language

        except Exception as e:
            raise e

    def _master_folder_path(self, root_master_folder_path: Path, project_name) -> Path:
        sanitized_project_name = re.sub(
            r"_v\d{1,3}", "", project_name, re.IGNORECASE)

        if not root_master_folder_path.exists():
            return root_master_folder_path / sanitized_project_name

        if not root_master_folder_path.is_dir():
            raise NotADirectoryError(
                f"⚠️  Master root path is not a directory: {root_master_folder_path}")

        for folder_path in sorted(root_master_folder_path.iterdir()):
            if re.match(f"{self.game_code}-{self.project_type}-{self.project_number}-{self.iteration_number}_", folder_path.stem, flags=re.IGNORECASE):
                return folder_path

        return root_master_folder_path / sanitized_project_name

    def _marketing_out_game_folder_path(self, root_marketing_out_folder_path: Path) -> Path:

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

    def _marketing_out_folder_path(self, marketing_out_game_folder_path: Path, project_name: str) -> Path:
        sanitized_project_name = re.sub(
            r"_v\d{1,3}", "", project_name, re.IGNORECASE)

        if not marketing_out_game_folder_path.exists():
            return marketing_out_game_folder_path / sanitized_project_name

        if not marketing_out_game_folder_path.is_dir():
            raise NotADirectoryError(
                f"⚠️  Marketing OUT root path is not a directory: {marketing_out_game_folder_path}")

        for folder_path in sorted(marketing_out_game_folder_path.iterdir()):
            if re.match(f"{self.game_code}-{self.project_type}-{self.project_number}-{self.iteration_number}_", folder_path.stem, flags=re.IGNORECASE):
                return folder_path

        return marketing_out_game_folder_path / sanitized_project_name

    @property
    def remove_from_out(self):
        print("Implement")

