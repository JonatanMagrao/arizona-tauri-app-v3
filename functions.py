from pathlib import Path
import os
import re
import platform


def find_file_in_tree_from(folder: Path) -> Path | None:
    try:
        for item in folder.iterdir():
            if item.is_file():
                return item
        for item in folder.iterdir():
            if item.is_dir():
                file = find_file_in_tree_from(item)
                return file
    except PermissionError:
        pass

    raise FileNotFoundError("⚠️ No files found in the directory tree.")


def ensure_folder_path(path: Path) -> Path:
    # path = rename_wip_path(path)
    path.mkdir(parents=True, exist_ok=True)
    return Path(path)


def long_path(path: Path | str) -> Path:
    """
    Se estiver no Windows e o caminho tiver ≥260 chars,
    adiciona o prefixo \\?\\ para habilitar long-paths.
    """
    path = Path(path)
    if platform.system() == "Windows":
        path = path.resolve()
        string_path = str(path)
        if len(string_path) >= 260 and not string_path.startswith(r"\\?\\"):
            return Path(f"\\\\?\\{string_path}")
    return path


def normalize_old_project_name(project_name: str) -> str:
    match = re.match(r"([A-Z]{2})_(\d{3,4})_(.*)", project_name, re.IGNORECASE)
    if not match:
        return project_name

    game_prefix = match.group(1).upper()
    game_number = match.group(2)
    rest = match.group(3)
    
    return f"{game_prefix}-V-{game_number}_{rest}"
