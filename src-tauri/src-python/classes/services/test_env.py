import os, json, platform
from pathlib import Path

def get_user_config_dir(app_name: str) -> Path:
    """Retorna a pasta de configuração por usuário (Roaming no Windows; Application Support no macOS)."""
    if platform.system().lower() == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif platform.system().lower() == "windows":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))       

    d = base / app_name
    d.mkdir(parents=True, exist_ok=True)
    return d


class TestEnvStore:
    def __init__(self, app_name="com.superplay.out-process.test-env"):
        self.config_file = get_user_config_dir(app_name) / "test.json"
        if not self.config_file.exists():
            self._write(True)

    def _write(self, is_test: bool):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump({"is_test": is_test}, f, indent=2)

    def _read(self):
        if not self.config_file.exists():
            return None
        with open(self.config_file, "r", encoding="utf-8") as f:
            return json.load(f).get("is_test", False)

    # CRUD
    def enable(self):
        """Ativa o modo de teste"""
        self._write(True)

    def disable(self):
        """Desativa o modo de teste"""
        self._write(False)

    @property
    def is_test(self):
        """Retorna o estado atual (True/False ou None se não existir)"""
        return self._read()

    def delete(self):
        """Remove o arquivo de configuração"""
        try:
            self.config_file.unlink()
        except FileNotFoundError:
            pass


