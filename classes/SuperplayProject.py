from functions import find_file_in_tree_from
import os, re
from pathlib import Path
import re
from typing import Optional

FILE_NAME_SUB_NORMALIZER = [
    r"_v\d{1,3}",
]

FOLDER_NAME_SUB_NORMALIZER = [
    r"_v\d{1,3}",
    r"_\d{2,4}x\d{2,4}"
]


class SuperplayProject:
    def __init__(self, config: dict, gdrive_local_path: Path, local_path: Path):

        self.gdrive_local_path = gdrive_local_path
        self.local_path = local_path
        self.project_types: dict = config.get("project_types")
        self.game_info: dict = config.get("games")
        self.supported_languages: dict = config.get("supported_languages")

        self.project_path_parts = self.gdrive_local_path.parts
        self.content = [*self.gdrive_local_path.iterdir()]
        self._parse_project_id()
        self.mktout_base_path = config.get("mktout_base_path")

        self.test_path = config.get("test_path")
        self.test = True

    @property
    def game_name(self) -> Optional[str]:
        """
        Procura pelo nome do projeto em uma lista de partes de caminho.
        1. Primeiro tenta o padrão: 'AA-BBB-0000_'
        2. Se não encontrar, tenta: 'AA_0000_'
        3. Se nada for encontrado, retorna None.
        """
        pattern_old = re.compile(r"[A-Z]{2}_\d{3,4}_",            flags=re.IGNORECASE)
        pattern_new = re.compile(r"[A-Z]{2}-[A-Z]{1,3}-\d{3,4}_", flags=re.IGNORECASE)

        for item in self.project_path_parts:
            if pattern_old.match(item):
                return item
            if pattern_new.match(item):
                return item

        # --- Fallback ---
        # Nenhum padrão bateu: retorna None ou, se preferir,
        raise ValueError("Project name not found in path parts.")

    @property
    def project_title(self) -> Optional[str]:
        file = find_file_in_tree_from(self.gdrive_local_path,".mp4")
        remove_resolution = re.compile(r"_\d{2,4}x\d{2,4}", flags=re.IGNORECASE)
        return remove_resolution.sub("", file.stem)

    def _parse_project_id(self) -> None:
        parts = self.project_title.split("-")
        self.game_code = parts[0]
        self.project_type = parts[1]
        self.project_number = parts[2]
        self.iteration_number = parts[3].split("_")[0]

    @property
    def id(self) -> dict:
        return {
            "game_code": self.game_code,
            "project_type": self.project_type,
            "project_number": self.project_number,
            "project_iteration": self.iteration_number
        }    

    def find_path_anchor(self, folder_name: str, First: bool = True) -> Optional[Path]:
        """
        Retorna o Path desde a raiz até (e incluindo) a pasta `folder_name`.
        Se `First=False`, usa a última ocorrência da âncora.
        Retorna None se a âncora não existir no caminho.
        """
        parts = list(self.gdrive_local_path.parts)

        # Aviso opcional
        if "Marketing OUT" in parts:
            print("Marketing OUT")

        # Descobre o índice da âncora
        try:
            idx = (len(parts) - 1 - parts[::-1].index(folder_name)
                   ) if First else parts.index(folder_name)
        except ValueError:
            return None  # âncora não encontrada

        # Remonta o path até a âncora
        root = Path(parts[0])
        return root.joinpath(*parts[1:idx + 1])
