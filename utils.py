from pathlib import Path
import os, re, json, platform
from typing import Callable


def find_file_in_tree_from(folder: Path, ext: str | None = ".") -> Path | None:
    """
    Retorna o primeiro arquivo encontrado a partir de `folder`.
    - `ext` pode ser ".mp4", "mp4", etc.
    - Use ".", ".*", "*", "" ou None para aceitar QUALQUER extensão.
    """
    any_ext = ext in (None, "", ".", ".*", "*")
    norm_ext = None if any_ext else (ext.lower() if ext.startswith(".") else f".{ext.lower()}")

    try:
        # primeiro: checa arquivos na pasta atual
        for item in folder.iterdir():
            if item.is_file() and (any_ext or item.suffix.lower() == norm_ext):
                return item

        # depois: desce recursivamente nas subpastas
        for item in folder.iterdir():
            if item.is_dir():
                found = find_file_in_tree_from(item, ext)  # <-- passa `ext`
                if found:
                    return found

    except PermissionError:
        return None  # sem permissão em alguma subpasta

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

def build_task(sanitizer:Callable[[Path], str], contents: list[str], out_paths: list[Path]):
    """
    Build the tasks to be copied
    sanitizer: a function to be callable. the function must receive a Path and return a string
    contents: a list of the contents (in string)
    out_paths: a list of the output paths
    """
    tasks = []

    try:
        for content in contents:
            new_file_name = sanitizer(Path(content))
            task = [content] # here is the source

            for out_path in out_paths:
                task.append(out_path / f"{new_file_name}")

            tasks.append(task)

        return tasks
    except PermissionError as e:
        raise PermissionError(f"⚠️ Permission denied: {e}")
    
def load_config_json(path: str | Path) -> dict:
    user_download_path = Path(os.environ["USERPROFILE"]) / "Downloads"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError("O JSON não é um objeto (dict); conteúdo lido: "
                        f"{type(data).__name__}")
    
    data["mktout_base_path"] = user_download_path / "Marketing OUT"
    data["test_path"] = user_download_path / "marketing_out_master_test"

    return data