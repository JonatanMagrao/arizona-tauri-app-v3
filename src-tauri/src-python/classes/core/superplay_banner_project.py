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

class SuperplayBannerProject(SuperplayProject):
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
    
    def _language(self, src_folder: Path) -> str | None:
        # Tenta os padrões em ordem de mais específico para mais genérico
        #! implementar caso encontre um idioma mas não está cadastrado

        if not "Localizations" in src_folder.parts:
            return "EN"

        project_parts = src_folder.parts
        for part in project_parts:
            if re.match(r"^[a-z]{2}(-[a-z]{2})?$",part,flags=re.IGNORECASE):
                return part
            
        raise ValueError(f"Language not found in path :'{src_folder}'")


    def _build_project(self, src_folder: Path) -> dict:

        try:

            is_localization_folder = src_folder.parent.name == "Localizations"
            project_content = [src_folder] if is_localization_folder else [*src_folder.iterdir()] 
            filtered_project_content = self._filter_solo_content(project_content)

            project_id = self.id
            project_name = self.project_title
            game = self.game_info.get(self.game_code)
            type_label = self.project_types.get(self.project_type).get("label")

            language = self._language(src_folder)
            language_full_info = self.supported_languages.get(language.lower())

            if src_folder.parent.name == "Localizations":
                root_mktout_folder_path = self._root_marketing_out_folder_path() / src_folder.name
                mktout_game_folder_path = self._marketing_out_game_folder_path(root_mktout_folder_path)
                mktout_folder_path = self._marketing_out_folder_path(mktout_game_folder_path, self.project_title)
            else:
                root_mktout_folder_path = self._root_marketing_out_folder_path() / "EN"
                mktout_game_folder_path = self._marketing_out_game_folder_path(root_mktout_folder_path)
                mktout_folder_path = self._marketing_out_folder_path(mktout_game_folder_path, project_name)

            project = {
                "status": "ready",
                "from_monday": self.from_monday,
                "id": project_id,
                "project_name": project_name,
                "type_label": type_label,
                "game": game,
                "duration": None,
                "language": language_full_info,
                "producers": self.producer_list,
                "content_to_copy": filtered_project_content,
                "video_to_preview": None,
                "src_folder_path": src_folder,
                "mktout_folder_path": {
                    "path": mktout_folder_path,
                    "exists": mktout_folder_path.exists(),
                    "is_empty": len(list(mktout_folder_path.iterdir())) == 0
                    if mktout_folder_path.exists()
                    else False
                },
                "master_folder_path":{
                    "path":None,
                    "exists":False,
                    "is_empty":True
                },
                "copy_paths": build_task(self._sanitize_out_path, filtered_project_content, [mktout_folder_path])
            }

            return project
        except Exception as e:
            raise e

    def job_manifest(self):
        localizations = self.gdrive_local_path / "Localizations"
        projects = [self._build_project(self.gdrive_local_path)]      

        if not localizations.exists():
            return projects  
        
        for localized in localizations.iterdir():
            projects.append(self._build_project(localizations / localized.name))

        return projects
                    

    def _sanitize_out_path(self, file_path: Path) -> str:

        if file_path.name.lower() == "master psd":
            return "Master PSD"

        _ = file_path
        return ""
    
    
    def _filter_solo_content(self, content: list[Path]) -> list[Path]:

        contents = []
        ignore_file_extensions: list[str] = self.ignore_list.get("file_extensions")
        ignore_folder_names: list[str] = self.ignore_list.get("folder_names")
        ignore_folder_names.append("Localizations")

        ignore_exts = {ext.lower().strip() for ext in ignore_file_extensions}
        ignore_folders = {name.lower().strip() for name in ignore_folder_names}

        for item in content:
            if item.is_file() and item.suffix.lower().strip() not in ignore_exts:
                contents.append(item)

            if item.is_dir() and item.stem.lower().strip() not in ignore_folders:
                contents.append(item)

        return contents

    def _root_marketing_out_folder_path(self) -> Path:

        try:
            project_type = self.id.get("project_type")
            game_code = self.id.get("game_code").upper()
            game_code_path = self.game_info.get(game_code).get("mktout_folder_name")
            game_type_cfg = self.project_types.get(project_type)
            shared_drive_name = game_type_cfg.get("shared_drive_name")
            type_folder_relpath = game_type_cfg.get("folder_path")

            if self.is_test:
                # return Path(self.test_path) / "Marketing OUT" / game_code_path / type_folder_path 
                return Path(self.test_path, shared_drive_name, game_code_path, *type_folder_relpath)
            else:
                # return Path(self.local_path) / "Marketing OUT" / game_code_path / type_folder_path 
                return Path(self.local_path, shared_drive_name, game_code_path, *type_folder_relpath)

        except Exception as e:
            raise e
            

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

        if not marketing_out_game_folder_path.exists():
            return marketing_out_game_folder_path / project_name

        if not marketing_out_game_folder_path.is_dir():
            raise NotADirectoryError(f"⚠️  Marketing OUT root path is not a directory: {marketing_out_game_folder_path}")

        # verifying if project name is found in marketing out language folder
        for folder_path in sorted(marketing_out_game_folder_path.iterdir()):
            if re.match(f"{self.game_code}-{self.project_type}-{self.project_number}-{self.iteration_number}_", folder_path.stem, flags=re.IGNORECASE):
                return folder_path

        return marketing_out_game_folder_path / project_name
    

    def dispatch_out(self):
        job_manifest: dict = self.job_manifest()
        file_copier = FileCopier()
        metadata = []

        for job in job_manifest:

            task = job.get("copy_paths")
            file_copier.copy_variadic_groups(task)
            job["status"] = "copied"
            job["mktout_folder_path"]["exists"] = True
            job["master_folder_path"]["exists"] = False
            job["mktout_folder_path"]["is_empty"] = False
            job["master_folder_path"]["is_empty"] = True
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
                item["error"] = f"Google's project link not found with name: {project_name}"
            elif len(links) > 1:
                error_msg = (
                    f"More than one project link found with name: {project_name}\n"
                    + "\n".join(f"- {link}" for link in links)
                )
                item["error"] = error_msg
            else:
                item["project_link"] = links[0]

            payload.append(item)
        return payload

    def send_slack_message(self):
        self.slack_util = SlackSuperplay(self.config)

        # monta payload e manifesto base
        payload = self.build_slack_payload()
        job_manifest = self.job_manifest()

        # segurança: tenta alinhar payload e manifest por ordem;
        # se der diferença de tamanho, faz um fallback por project_name
        if len(payload) != len(job_manifest):
            jobs_by_name = {j["project_name"]: j for j in job_manifest}
            aligned_manifest = []
            for p in payload:
                j = jobs_by_name.get(p["project_name"])
                if not j:
                    j = {
                        "project_name": p["project_name"],
                        "status": "error",
                        "msg": "No job manifest entry found for this payload item."
                    }
                aligned_manifest.append(j)
            job_manifest = aligned_manifest

        # descobre o nome do canal (se existir algum channel_id válido)
        channel_name = None
        for p in payload:
            cid = p.get("channel_id")
            if cid:
                channel_name = self.slack_util.get_channel_name_by_id(cid)
                break

        # ============================================================
        # 1) Cenário: projetos localizados (pastas) com múltiplos idiomas
        #    -> envia UMA mensagem consolidada com todas as linguagens válidas
        # ============================================================
        if self._has_only_folder and not self._all_folder_names_equal_ignoring_duration:
            valid = [p for p in payload if p.get("project_link") and not p.get("error")]

            # nenhum link válido: marca todos como erro e retorna lista
            if not valid:
                for idx, p in enumerate(payload):
                    j = job_manifest[idx]
                    j["status"] = "error"
                    j["channel_name"] = channel_name
                    j["msg"] = p.get("error") or "Project link not found for Slack notification."
                return job_manifest

            # há links válidos -> monta mensagem única
            base = valid[0]
            lines = [
                f'{(p.get("language") or "UNK")} - {p["project_link"]}'
                for p in valid
            ]

            self.slack_util.send_out_msg(
                base["channel_id"],
                base["producers"],
                base["project_name"],
                "\n".join(lines),
                base["video_path"],
            )

            # marca jobs: válidos = notified, inválidos = error
            for idx, p in enumerate(payload):
                j = job_manifest[idx]
                j["channel_name"] = channel_name
                if p in valid:
                    j["status"] = "notified"
                else:
                    j["status"] = "error"
                    j["msg"] = p.get("error") or "Skipped from multi-language notification (no valid link)."

            return job_manifest

        # ============================================================
        # 2) Demais cenários:
        #    - múltiplos projetos com iter diferente
        #    - projeto único
        #    Tratamos todos de forma uniforme: um send por payload válido.
        # ============================================================
        for idx, p in enumerate(payload):
            j = job_manifest[idx]
            j["channel_name"] = channel_name

            # erro detectado na construção do payload
            if p.get("error"):
                j["status"] = "error"
                j["msg"] = p["error"]
                continue

            # sem link de projeto -> não dá pra notificar
            if not p.get("project_link"):
                j["status"] = "error"
                j["msg"] = "Project link not found for Slack notification."
                continue

            # sem canal -> erro de config
            if not p.get("channel_id"):
                j["status"] = "error"
                j["msg"] = "Slack channel_id not defined for this project."
                continue

            # se chegou aqui, podemos enviar
            self.slack_util.send_out_msg(
                p["channel_id"],
                p["producers"],
                p["project_name"],
                p["project_link"],
                p["video_path"],
            )
            j["status"] = "notified"

        return job_manifest


    @property
    def remove_from_out(self):
        print("Implement")
