from pathlib import Path
import os, json

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