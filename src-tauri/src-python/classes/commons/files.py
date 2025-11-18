from pathlib import Path
import platform

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
            
            if bool(item.suffix) and not item.is_file():
                # erro com o contexto do python rodando com o tauri. se rodar pelo python localmente, funciona normal.
                # se der erro, só rodar o main diretamente pelo python como `python src-tauri/src-python/main.py`
                raise FileNotFoundError("Issue not solved. Please, make this project manually.")

        # depois: desce recursivamente nas subpastas
        for item in folder.iterdir():
            if item.is_dir():
                found = find_file_in_tree_from(item, ext)  # <-- passa `ext`
                if found:
                    return found
                

    except PermissionError:
        return None  # sem permissão em alguma subpasta

    raise FileNotFoundError("⚠️ No files found in the directory tree.")


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


