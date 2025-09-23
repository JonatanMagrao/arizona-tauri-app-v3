import shutil
from pathlib import Path
import re
from typing import Optional

# origem = Path(r"G:\Drives compartilhados\Marketing_DS_2025_H2\Creative Projects\Video\DS-V-042_ChefBurger\Comp\DS-V-042-001_ChefBurger_30s\Render\(Internal Review)")
# origem = Path(r"G:\Drives compartilhados\Marketing_DD_MGX_Masters_01\DD_195_Stickers_LastSticker-Retro\Render\(Internal Review)\03\DD-V-195-008_LastSticker_DD-VEO-001-001_EN_30s")
origem = Path(r"G:\Drives compartilhados\Marketing_DD_MGX_Masters_01\DD_195_Stickers_LastSticker-Retro\Render\(Internal Review)\03\DD-V-195-008_LastSticker_DD-VEO-001-001_EN_30s")

# origem = Path(r"G:\Drives compartilhados\Marketing_DD_MGX_Masters_01\DD_241_2024StoreVid_ASO\Render\(Internal Review)\03\DE\DD-V-241-002_2024StoreVid_DE_30s-ASO")
# origem = Path(r"G:\Drives compartilhados\Marketing_DX_MGX_Masters_01\DX_015_SimpleIntro\Render\(Internal Review)\11\DX-V-015-015_SimpleIntro_Park_DE_15s")
destino_pasta = Path(r"C:\Users\PC\Downloads\lixo_temp_superplay")

FILE_NAME_SUB_NORMALIZER = [
    r"_v\d{1,3}",
]

FOLDER_NAME_SUB_NORMALIZER = [
    r"_v\d{1,3}",
    r"_\d{2,4}x\d{2,4}",
    r"\.mp4"
]

LANGUAGE_PATTERN_LIST = [
    r'_([A-Z]{2}(?:-[A-Z]{2})?)_\d{2,3}s',    # Ex: _PT-BR_120s
    r'\b([A-Z]{2}(?:-[A-Z]{2})?)_\d{2,3}s\b'  # Ex: PT-BR isolado
]





def normalize_file_name_on_copy(origem: Path, FILE_NAME_SUB_NORMALIZER: list[str]) -> str:
    for sub in FILE_NAME_SUB_NORMALIZER:
        origem = origem.with_name(
            re.sub(sub, "", origem.name, flags=re.IGNORECASE))
    return origem.name





projeto = SuperplayProject(origem)
projeto_name = projeto.get_project_language(LANGUAGE_PATTERN_LIST)
print(projeto_name)

# project_path_parts = origem.parts
# project_contents = [*origem.iterdir()]
# render_path = path_until(project_path_parts, "Render")
# project_name = get_project_name(project_contents, FOLDER_NAME_SUB_NORMALIZER)

# project_lang = get_project_language(project_name, LANGUAGE_PATTERN_LIST)
# project_duration = get_duration(project_name)
# project_id = get_prefix(project_name)

# game_code = project_id.get("game_code")
# project_type = project_id.get("project_type")
# project_number = project_id.get("project_number")
# iteration_number = project_id.get("iteration_number")

# print(project_path_parts)
# print(project_contents)
# print(render_path)
# print(project_name)

# print(project_lang)
# print(project_duration)
# print(project_id)

# destino = destino_pasta / normalize_file_name_on_copy(project_name, FOLDER_NAME_SUB_NORMALIZER)
# shutil.copy2(origem, destino)
# print(f"Arquivo copiado para: {destino}")
