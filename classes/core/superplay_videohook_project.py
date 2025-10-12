from pathlib import Path
from classes.commons import build_task, normalize_old_project_name
from classes.core.superplay_project import SuperplayProject
from classes.services import FileCopier
import re, json
from typing import Optional


class SuperplayVideoHookProject(SuperplayProject):
    def __init__(self, config: dict, gdrive_local_path: Path, local_path: Path):
        super().__init__(config, gdrive_local_path, local_path)
        self.ignore_list: dict = self.project_types.get(self.project_type).get("ignore_list")   

    def _get_project_name(self, src_folder: list[str]) -> str:
        path_list = [Path(item) for item in src_folder]

        cleanner_list = [
            re.compile(r"_\d{2,4}x\d{2,4}", flags=re.IGNORECASE), # remove resolution in the name
            re.compile(r"_reference", flags=re.IGNORECASE), # remove reference in the name
            re.compile(r"_v\d{1,3}", flags=re.IGNORECASE), # remove version in the name
        ]

        sanitize_list = [
            re.compile(r"\s*_\s*", flags=re.IGNORECASE), # remove extra spaces with the underscore
        ]

        project_title = next(item.stem for item in path_list if item.is_file() and item.suffix.lower() == ".mp4")

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
        video_to_preview_path = self._video_to_preview_path(project_content)

        root_master_folder_path = self._root_master_folder_path()
        root_mktout_folder_path = self._root_marketing_out_folder_path()
        mktout_game_folder_path = self._marketing_out_game_folder_path(root_mktout_folder_path)

        #todo aqui, fazer validação para quando for mais de um projeto para pegar os nomes dos arquivos certinho
        mktout_folder_path = self._marketing_out_folder_path(mktout_game_folder_path, project_name)
        master_folder_path = self._master_folder_path(root_master_folder_path, project_name)

        project = {
            "id": project_id,
            "project_name": project_name,
            "type_label": type_label,
            "game": game,
            "duration": duration,
            "producers": self.producer_list,
            "content_to_copy": filtered_project_content,
            "video_to_preview": video_to_preview_path,
            "mktout_folder_path":{"path":mktout_folder_path,"exists":mktout_folder_path.exists()},
            "master_folder_path":{"path":master_folder_path,"exists":master_folder_path.exists()},
            "copy_paths": build_task(self._sanitize_video_file_name, filtered_project_content, [mktout_folder_path,master_folder_path])
        }

        return project
    

    @property
    def job_manifest(self):
        try:
            return [self._build_project(self.gdrive_local_path)]
        except Exception as e:
            raise e
        
        
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


    def _filter_solo_content(self,content:list[Path]) -> list[Path]:
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
    
    def _root_master_folder_path(self) -> Path:
        if self.test:
            return Path(self.test_path) / "Render" / "MASTER" 
        else:
            return self.find_path_anchor("Render") / "MASTER" 

    def _video_to_preview_path(self, src_folder: list[str]) -> Path:
        # .mp4 exists?
        if not any(Path(item).is_file() and Path(item).suffix.lower() == ".mp4" for item in src_folder):
            raise FileNotFoundError("Video to preview not found")

        # working only with .mp4 and Path
        mp4_files = [Path(item) for item in src_folder if Path(item).is_file() and Path(item).suffix.lower() == ".mp4"]

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

    def _root_marketing_out_folder_path(self) -> Path:

        try:
            project_type = self.id.get("project_type")
            game_code = self.id.get("game_code").upper()
            game_code_path = self.game_info.get(game_code).get("mktout_folder_name")
            type_folder_path = self.project_types.get(project_type).get("folder_path")

            if self.test:
                return Path(self.test_path) / "Marketing OUT" / game_code_path / type_folder_path.replace("<GAME_CODE>",self.game_code) / "Hooks"
            else:
                return Path(self.mktout_base_path) / game_code_path / type_folder_path.replace("<GAME_CODE>",self.game_code) / "Hooks"

        except Exception as e:
            raise e

    def _master_folder_path(self, root_master_folder_path: Path, project_name) -> Path:
        sanitized_project_name = re.sub(r"_v\d{1,3}", "", project_name, flags= re.IGNORECASE)

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
            raise NotADirectoryError(
                f"⚠️  Marketing OUT root path is not a directory: {marketing_out_game_folder_path}")

        for folder_path in sorted(marketing_out_game_folder_path.iterdir()):
            if re.match(f"{self.game_code}-{self.project_type}-{self.project_number}-{self.iteration_number}_", folder_path.stem, flags=re.IGNORECASE):
                return folder_path
            
        return marketing_out_game_folder_path / sanitized_project_name
    
    def dispatch_out(self):
        #! está funcionando apenas com projeto solo, não com localized ou combo
        job_manifest: dict = self.job_manifest
        file_copier = FileCopier()

        for job in job_manifest:            
            task = job.get("copy_paths")
            file_copier.copy_variadic_groups(task)

    def build_slack_payload(self):
        #! @property seria ideal apenas para recuperar dados sem risco de erro, quando dados já estão prontos e disponíveis e sem I/O. por conta do contents e project com o _build_project, seria interessante ou criar uma validação pra isso com try catch antes ou criar uma outra função auxiliar apenas para ajudar na construção disso. se der algum erro, nem chega aqui e avisa o usuário
        job_manifest = self.job_manifest
        slack_payload = []
        for job in job_manifest:
            
            slack_channel_id = job.get("game").get("slack_channel_id")
            producers = self.producer_list
            project_name = job.get("project_name")
            project_link = self.google_util.get_mktout_folder_link(project_name)
            video_path = job.get("video_to_preview")

            #! estudar forma para retornar caso dê erro. volta pro usuário? cancela toda a operação do slack? manda apenas os que foram processados? etc
            if len(project_link) < 1:
                print(f"Project link not found for: {project_name}")
                continue

            if len(project_link) > 2:
                print(f"More than one project link found for: {project_name}")
                continue

            slack_payload.append({
                "channel_id": slack_channel_id,
                "producers": producers,
                "project_name": project_name,
                "project_link": project_link[0],
                "video_path": video_path,
            })
        
        return slack_payload

    def send_slack_message(self):

        #todo preciso implementar quando for combos também aqui
        slack_payload = self.build_slack_payload()
        
        channel_id = slack_payload[0].get("channel_id")
        producers = slack_payload[0].get("producers")
        video_path = slack_payload[0].get("video_path")
        project_name = slack_payload[0].get("project_name")            
        project_link = slack_payload[0].get("project_link")
        video_path = slack_payload[0].get("video_path")

        self.slack_util.send_out_msg(channel_id, producers, project_name, project_link, video_path)



    @property
    def remove_from_out(self):
        print("Implement")

