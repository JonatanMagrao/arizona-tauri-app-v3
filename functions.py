from pathlib import Path
import os
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

def build_copy_plan(structured_local_folders) -> list[tuple[Path, tuple[Path, Path]]]:
    all_project_copy_tasks = []
    for data in structured_local_folders:
        folder_content_to_copy = Path(data["folder_content_to_copy"])
        master_project_path = Path(data["master_project_path"])
        mktout_project_path = Path(data["mktout_project_path"])
        if data.get("mktout_project_path") is None:
            continue
        all_project_copy_tasks.append(
            (folder_content_to_copy, (mktout_project_path, master_project_path)))

    return all_project_copy_tasks