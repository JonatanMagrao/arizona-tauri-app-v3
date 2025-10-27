from pathlib import Path
import os, json
from classes.commons.shared_drives import full_local_path

def load_config_json(file_name: str | Path) -> dict:
    user_download_path = Path(os.environ["USERPROFILE"]) / "Downloads"
    # config_file_path = Path(__file__).resolve().parent.parent.parent / path
    config_file_path = Path(full_local_path() / "Creative_Marketing_Assets" / "OUT-AUTOMATION-DOCS" / file_name)

    try:
        with open(config_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_file_path}")

    if not isinstance(data, dict):
        raise TypeError("O JSON não é um objeto (dict); conteúdo lido: "
                        f"{type(data).__name__}")
    
    data["mktout_base_path"] = user_download_path / "Marketing OUT"
    data["test_path"] = user_download_path / "marketing_out_master_test"

    return data