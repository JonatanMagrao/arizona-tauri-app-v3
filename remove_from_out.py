import sys
from pathlib import Path
import re
import shutil
import os

# ===================== FUNCTIONS =====================


def get_project_language(name: str) -> str | None:
    # Tenta os padrões em ordem de mais específico para mais genérico
    for pattern in [
        r'_([A-Z]{2}(?:-[A-Z]{2})?)_\d{2,3}s',  # Ex: _PT-BR_120s
        r'\b([A-Z]{2}(?:-[A-Z]{2})?)_\d{2,3}s\b'         # Ex: PT-BR isolado
    ]:
        match = re.search(pattern, name)
        if match:
            return match.group(1)

    return None


def parse_project(project_name: str) -> tuple:
    game = project_name.split("-")[0]
    proj_type = project_name.split("-")[1]
    proj_num = project_name.split("-")[2]
    ite_num = project_name.split("-")[3].split("_")[0]
    language = get_project_language(project_name)

    return {
        "game": game,
        "proj_type": proj_type,
        "proj_num": proj_num,
        "ite_num": ite_num,
        "language": language
    }


def build_lang_folder_path(BASE_MKTOUT_PATH, project_data):
    base_path = Path(BASE_MKTOUT_PATH)

    game = project_data["game"]
    proj_type = project_data["proj_type"]
    language = project_data["language"]

    language_folder = base_path / GAMES[game] / TYPES[proj_type] / language
    return language_folder


def list_project_folders(language_folder_path: Path, project_data: dict):

    if not language_folder_path.is_dir():
        print(f"Language folder not found: {language_folder_path}")
        return []

    folders = []

    game = project_data["game"]
    proj_type = project_data["proj_type"]
    proj_num = project_data["proj_num"]

    # 1) formato principal: GAME-TYPE-PROJ
    prefix1 = f"{game}-{proj_type}-{proj_num}"
    folders = [n for n in language_folder_path.iterdir()
               if n.is_dir() and n.name.startswith(prefix1)]

    # 2) fallback: GAME_PROJ (só roda se o 1º não achou nada)
    if not folders:
        prefix2 = f"{game}_{proj_num}"
        folders = [n for n in language_folder_path.iterdir()
                   if n.is_dir() and n.name.startswith(prefix2)]

    return folders


# ===================== CONFIG =====================

GAMES = {
    "DS": "DS_DisneySolitaire_OUT",
    "DD": "DD_DiceDreams_OUT",
    "DX": "DX_DominoDreams_OUT"
}

TYPES = {
    "V": "07-Videos",
    "H": "07-Videos",
    "P": "06-Playables",  # playables não tem idioma
    "G": "05-Gifs",
    "B": "04-Banners",
}

BASE_MKTOUT_PATH = r"G:\Drives compartilhados\Marketing OUT"
LIXO = r"C:\Users\PC\Downloads\lixo_temp_superplay"

# ==================== MAIN =====================

# project_name = "DS-V-002-057_Scenes_BeastReviesd_VO_DS-H-001-001_JA_30s"
# project_name = "DS-V-002-059_Scenes_ToyStoryReviesd_VO_DS-H-004-001_JA_60s_1080x1080"
# project_name = "DS-V-024-009_Puzzle_LiloStitch_VO_JA_30s_1080x1080"
# project_name = "DS-V-002-060_Scenes_ToyStoryReviesd_NoFrame_VO_JA_30s_1080x1080"
# project_name = "DS-V-018-047_NewWorld_VO_JA_60s_1080x1080"
# project_name = "DS-V-017-021_HookLaunch_What_sGoingOn_DS-V-001-009_JA_30s_1080x1080_DS_V_002_015_Japan_30s"
project_name = "DS-V-014-020_BuildSplit_Stitch_DS-H-010-001_JA_30s"

# project_name = "DD-V-076-007_NLBurst2022_NewCastle_NL_08s"
# project_name = "DD-V-278-001_BingoBash_EN_30s"

# project_name = "DX-V-028-005_ImpossibleLevel_DX-H-054-001(Pinata)_EN_24s"
# project_name = "DX-P-006-002_Wheel_HLWN_CB [Flex]"

project_data = parse_project(project_name)
lang_folder_path = build_lang_folder_path(BASE_MKTOUT_PATH, project_data)
folders = list_project_folders(lang_folder_path, project_data)

if len(folders) > 1:
    print("More than one folder found, please fix it!")
    sys.exit(1)

folder = folders[0]
os.startfile(folder)

# for x in folder.iterdir():
#     prefix = f"{game}-{type}-{proj_num}-{iteration_num}_"
#     if x.name.startswith(prefix):
#         src = Path(x).resolve()
#         dstn = Path(LIXO).resolve()
#         print(folder)
# shutil.move(src, dstn)
# os.startfile(dstn)

# os.startfile(folders[0])
