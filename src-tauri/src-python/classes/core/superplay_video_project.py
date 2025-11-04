from pathlib import Path
from classes.commons import build_task, normalize_old_project_name
from classes.integrations.slack.slack_superplay import SlackSuperplay
from classes.core.superplay_project import SuperplayProject
from classes.services import FileCopier
from classes.core.exceptions import MediaFileNotFoundError
import re
import json
from typing import Optional

LANGUAGE_PATTERN_LIST = [
    r'_([A-Z]{2}(?:-[A-Z]{2})?)_\d{2,3}s',
]

IGNORE_LIST = [
    "Archive",
    "_Archive"
]


class SuperplayVideoProject(SuperplayProject):
    def __init__(self, config: dict, gdrive_local_path: Path, local_path: Path, src_link: str = None):
        super().__init__(config, gdrive_local_path, local_path, src_link)
        self.ignore_list: dict = self.project_types.get(self.project_type).get("ignore_list")
        self.iteration_number = self.project_title.split("-")[3].split("_")[0]

    @property
    def _has_only_folder(self) -> bool:
        return all([content.is_dir() for content in self.content])
    
    @property
    def _all_folder_names_equal_ignoring_duration(self) -> bool:
        """
        Verifica se os nomes das pastas são iguais ao remover:
        - Qualquer trecho de duração como '_15s', '_30s' (em qualquer posição)
        - O segundo grupo numérico do padrão XX-V-000-000
        """

        duration_pattern = re.compile(r'_\d{1,4}s', re.IGNORECASE)
        prefix_pattern = re.compile(
            r'^([A-Z]{2}-[A-Z]-\d{1,4})-\d{1,4}_', re.IGNORECASE)

        def normalize(name: str) -> str:
            name = duration_pattern.sub('', name)
            name = prefix_pattern.sub(r'\1_', name)
            return name
        

        names = [normalize(item.name) for item in self.content]
        return all(name == names[0] for name in names) if names else False
    

    def _get_project_name(self, src_folder: list[str]) -> str:
        path_list = [Path(item) for item in src_folder]

        cleanner_list = [
            # remove resolution in the name
            re.compile(r"_\d{2,4}x\d{2,4}", flags=re.IGNORECASE),
            # remove version in the name
            re.compile(r"_v\d{1,3}", flags=re.IGNORECASE),
        ]

        sanitize_list = [
            # remove extra spaces with the underscore
            re.compile(r"\s*_\s*", flags=re.IGNORECASE),
        ]

        project_title = next((item.stem for item in path_list if item.is_file() and item.suffix.lower() == ".mp4"), None)
        if not project_title:
            raise MediaFileNotFoundError(
                f".mp4 file not found on '{path_list[0].parent.name}' folder")

        for cleaner in cleanner_list:
            project_title = cleaner.sub("", project_title)

        for sanitizer in sanitize_list:
            project_title = sanitizer.sub("_", project_title)

        return project_title

    def _build_project(self, src_folder: Path) -> dict:
        project_content = [*src_folder.iterdir()]
        filtered_project_content = self._filter_solo_content(project_content)
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

        # todo aqui, fazer validação para quando for mais de um projeto para pegar os nomes dos arquivos certinho
        mktout_folder_path = self._marketing_out_folder_path(mktout_game_folder_path, project_name)
        master_folder_path = self._master_folder_path(root_master_folder_path, project_name)

        project = {
            "status": "ready",
            "from_monday": self.from_monday,
            "id": project_id,
            "project_name": project_name,
            "type_label": type_label,
            "game": game,
            "duration": duration,
            "language": language_full_info,
            "producers": self.producer_list,
            "content_to_copy": filtered_project_content,
            "video_to_preview": video_to_preview_path,
            "mktout_folder_path": {
                "path": mktout_folder_path,
                "exists": mktout_folder_path.exists(),
                "is_empty": len(list(mktout_folder_path.iterdir())) == 0
                if mktout_folder_path.exists()
                else False
            },
            "master_folder_path": {
                "path": master_folder_path,
                "exists": master_folder_path.exists(),
                "is_empty": len(list(master_folder_path.iterdir())) == 0
                if master_folder_path.exists()
                else False
            },
            "copy_paths": build_task(self._sanitize_video_file_name, filtered_project_content, [mktout_folder_path, master_folder_path])
        }

        return project

    def job_manifest(self):
        #! @property seria ideal apenas para recuperar dados sem risco de erro, quando dados já estão prontos e disponíveis e sem I/O. por conta do contents e project com o _build_project, seria interessante ou criar uma validação pra isso com try catch antes ou criar uma outra função auxiliar apenas para ajudar na construção disso. se der algum erro, nem chega aqui e avisa o usuário
        #! preciso adaptar para o novo formato. aqui ele tá passando o path da pasta, não dos arquivos. eu preciso dos arquivos para pegar o nome
        if self._has_only_folder:
            projetos = []
            for src_folder in self.content:
                contents = [*Path(src_folder).iterdir()]
                content_path = contents[0].parent
                
                # had issues when projects have different iteration numbers on gdrive provided
                # it may fix some iteration number based on each project folder content. 
                for item in content_path.iterdir():
                    if item.is_file() and item.suffix.lower() == ".mp4":
                        self.iteration_number = item.stem.split("-")[3].split("_")[0]
                        break

                project = self._build_project(content_path)
                projetos.append(project)
            return projetos

        else:

            return [self._build_project(self.gdrive_local_path)]

    def _sanitize_video_file_name(self, file_path: Path) -> str:
        remove_version = re.compile(r"_v\d{1,3}", flags=re.IGNORECASE)
        final_file_path_name = remove_version.sub("", file_path.name)

        return final_file_path_name

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

    def _filter_solo_content(self, content: list[Path]) -> list[Path]:
        contents = []
        ignore_file_extensions: list[str] = self.ignore_list.get(
            "file_extensions")
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
        if self.is_test:
            return Path(self.test_path) / "Render" / "MASTER" / language.upper()
        else:
            return self.find_path_anchor("Render") / "MASTER" / language.upper()

    def _video_to_preview_path(self, src_folder: list[str]) -> Path:
        # .mp4 exists?
        if not any(Path(item).is_file() and Path(item).suffix.lower() == ".mp4" for item in src_folder):
            raise FileNotFoundError("Video to preview not found")

        # working only with .mp4 and Path
        mp4_files = [Path(item) for item in src_folder if Path(
            item).is_file() and Path(item).suffix.lower() == ".mp4"]

        # 1º stop: 1080x1080
        for item in mp4_files:
            if re.search(r"_1080x1080", item.stem, flags=re.IGNORECASE):
                return item

        # 2º stopa: 1920x1080
        for item in mp4_files:
            if re.search(r"_1920x1080", item.stem, flags=re.IGNORECASE):
                return item

        # fallback: any .mp4 file
        return mp4_files[0]

    def _root_marketing_out_folder_path(self, language: str) -> Path:

        try:
            project_type = self.id.get("project_type")
            game_code = self.id.get("game_code").upper()
            game_code_path = self.game_info.get(
                game_code).get("mktout_folder_name")
            game_type_cfg = self.project_types.get(project_type)
            shared_drive_name = game_type_cfg.get("shared_drive_name")
            type_folder_relpath = game_type_cfg.get("folder_path")

            if self.is_test:
                # return Path(self.test_path) / "Marketing OUT" / game_code_path / type_folder_path / language
                return Path(self.test_path, shared_drive_name, game_code_path, *type_folder_relpath, language)
            else:
                # return Path(self.local_path) / "Marketing OUT" / game_code_path / type_folder_path / language
                return Path(self.local_path, shared_drive_name, game_code_path, *type_folder_relpath, language)

        except Exception as e:
            raise e

    def _master_folder_path(self, root_master_folder_path: Path, project_name) -> Path:
        sanitized_project_name = re.sub(
            r"_v\d{1,3}", "", project_name, flags=re.IGNORECASE)

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
        sanitized_project_name = re.sub(r"_v\d{1,3}", "", project_name, flags=re.IGNORECASE)

        if not marketing_out_game_folder_path.exists():
            return marketing_out_game_folder_path / sanitized_project_name

        if not marketing_out_game_folder_path.is_dir():
            raise NotADirectoryError(f"⚠️  Marketing OUT root path is not a directory: {marketing_out_game_folder_path}")

        # verifying if project name is found in marketing out language folder
        for folder_path in sorted(marketing_out_game_folder_path.iterdir()):
            if re.match(f"{self.game_code}-{self.project_type}-{self.project_number}-{self.iteration_number}_", folder_path.stem, flags=re.IGNORECASE):
                return folder_path

        return marketing_out_game_folder_path / sanitized_project_name

    def dispatch_out(self):
        job_manifest: dict = self.job_manifest()
        file_copier = FileCopier()
        metadata = []

        for job in job_manifest:

            task = job.get("copy_paths")
            file_copier.copy_variadic_groups(task)
            job["status"] = "copied"
            job["mktout_folder_path"]["exists"] = True
            job["master_folder_path"]["exists"] = True
            job["mktout_folder_path"]["is_empty"] = False
            job["master_folder_path"]["is_empty"] = False
            metadata.append(job)

            # metadata.append({
            #     "project_name": job["project_name"],
            #     "copy_source_folder": str(Path(job["content_to_copy"][0]).parent),
            #     "mktout_folder_path": job["mktout_folder_path"]["path"],
            #     "master_folder_path": job["master_folder_path"]["path"],
            #     "content_to_copy": [Path(item).name for item in job["content_to_copy"]],
            # })

        return metadata

    def build_slack_payload(self):
        payload = []
        for job in self.job_manifest():
            project_name = job.get("project_name")
            links = self.google_util.get_mktout_folder_link(project_name) or []
            channel_id = (job.get("game") or {}).get("slack_channel_id")

            if self.is_test:
                channel_id = self.test_env["slack_channel_test_id"]

            item = {
                "channel_id": channel_id,
                "producers": self.producer_list,
                "project_name": project_name,
                "video_path": job.get("video_to_preview"),
                "language": ((job.get("language") or {}).get("abbr") or "").upper(),
                "project_link": None,
                "error": None,
            }

            if not links:
                item["error"] = f"Project link not found for: {project_name}"
            elif len(links) > 1:
                item["error"] = f"More than one project link found for: {project_name}"
            else:
                item["project_link"] = links[0]

            payload.append(item)
        return payload

    def send_slack_message(self):
        self.slack_util = SlackSuperplay(self.config)
        payload = self.build_slack_payload()
        # nome do canal (pega do primeiro que tiver id)
        channel_name = None
        for p in payload:
            if p.get("channel_id"):
                channel_name = self.slack_util.get_channel_name_by_id(
                    p["channel_id"])
                break

        errors = []

        # for localized projects with multiple languages
        if self._has_only_folder and not self._all_folder_names_equal_ignoring_duration:
            valid = [p for p in payload if p.get(
                "project_link") and not p.get("error")]
            if not valid:
                errors = [{"project": p["project_name"],
                           "msg": p["error"] or "invalid"} for p in payload]
                return {
                    "status": "error",
                    "project_name": self.project_title,
                    "producers": self.producer_list,
                    "channel_name": channel_name,
                    "errors": errors
                }

            base = valid[0]
            lines = [
                f'{p["language"] or "UNK"} - {p["project_link"]}' for p in valid]
            self.slack_util.send_out_msg(
                base["channel_id"],
                base["producers"],
                base["project_name"],
                "\n".join(lines),
                base["video_path"],
            )

        # for multiple projects with different iteration numbers
        elif self._all_folder_names_equal_ignoring_duration:
            for p in payload:
                if p.get("error") or not p.get("project_link"):
                    if p.get("error"):
                        errors.append(
                            {"project": p["project_name"], "msg": p["error"]})
                    continue
                self.slack_util.send_out_msg(
                    p["channel_id"],
                    p["producers"],
                    p["project_name"],
                    p["project_link"],
                    p["video_path"],
                )

        # for single projects
        else:
            for p in payload:
                if p.get("error") or not p.get("project_link"):
                    if p.get("error"):
                        errors.append(
                            {"project": p["project_name"], "msg": p["error"]})
                    continue
                self.slack_util.send_out_msg(
                    p["channel_id"],
                    p["producers"],
                    p["project_name"],
                    p["project_link"],
                    p["video_path"],
                )

        job_manifest = self.job_manifest()
        for job in job_manifest:
            job["status"] = "notified"

        print(json.dumps(job_manifest, ensure_ascii=False, indent=2, default=str))

        return job_manifest

        # return {
        #     "status": "success" if not errors else "partial",
        #     "project_name": self.project_title,
        #     "producers": self.producer_list,
        #     "channel_name": channel_name,
        #     "errors": errors
        # }

    @property
    def remove_from_out(self):
        print("Implement")
