from __future__ import annotations
import json
from typing import Any, Optional
import keyring
import keyring.errors as ke

class KeyringEntry:
    """Wrapper simples para um item no keyring do SO."""
    def __init__(self, service: str, account: str):
        self.service = service
        self.account = account

    def get(self) -> Optional[str]:
        return keyring.get_password(self.service, self.account)

    def set(self, secret: str) -> None:
        keyring.set_password(self.service, self.account, secret)

    def delete(self) -> bool:
        try:
            keyring.delete_password(self.service, self.account)
            return True
        except ke.PasswordDeleteError:
            return False

    def exists(self) -> bool:
        return self.get() is not None

    # opcionais para quem quer JSON
    def set_json(self, obj: Any) -> None:
        keyring.set_password(self.service, self.account, json.dumps(obj))

    def get_json(self) -> Optional[Any]:
        raw = self.get()
        return json.loads(raw) if raw else None

    @staticmethod
    def backend_name() -> str:
        kr = keyring.get_keyring()
        return f"{kr.__class__.__module__}.{kr.__class__.__name__}"

    def __repr__(self) -> str:
        return f"<KeyringEntry service='{self.service}' account='{self.account}' exists={self.exists()}>"

if __name__ == "__main__":
    kr = KeyringEntry("OutApp", "slack_user_token")
    # resp = kr.delete()
    # if resp:
    #     print("Token deleted")
    print(kr.get())
