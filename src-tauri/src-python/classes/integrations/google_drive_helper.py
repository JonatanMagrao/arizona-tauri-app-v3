import requests
from urllib.parse import (urlencode, urlparse)
from classes.core.exceptions import (
    LinkDataRetrievalError, InvalidURL, GoogleSheetLogError)


class GoogleDriveHelper:
    def __init__(self, config: dict):
        self.config = config
        self._google_endpoints: dict = config.get("google_endpoints", {})
        self.data_endpoint = self._google_endpoints.get("data_endpoint")
        self.link_endpoint = self._google_endpoints.get("link_endpoint")
        self.sheet_endpoint = self._google_endpoints.get("sheet_endpoint")

    ALLOWED_NETLOCS = {"drive.google.com", "docs.google.com", "www.drive.google.com", "www.docs.google.com"}

    def _normalize_google_url(self, url: str) -> str:
        """
        Normaliza links do Drive/Docs:
        - Aceita sem esquema (ex.: 'drive.google.com/open?...') e prefixa https://
        - Remove pontuação final comum
        - Garante netloc permitido
        Retorna a URL normalizada ou levanta InvalidURL.
        """
        if not url:
            raise InvalidURL(url)

        u = url.strip().rstrip(").,;")
        # se veio sem esquema, prefixa https://
        if not u.lower().startswith(("http://", "https://")):
            u = "https://" + u

        parsed = urlparse(u)
        if parsed.netloc not in self.ALLOWED_NETLOCS:
            raise InvalidURL(u)

        # opcional: garantir que seja rota do Drive/Docs de arquivo/pasta/open/uc
        # if not parsed.path.startswith(("/open", "/file/", "/drive/", "/uc", "/document/")):
        #     raise InvalidURL(u)

        return u

    def sheet_log(self, info: dict):
        try:
            response = requests.post(
                self.sheet_endpoint, json=info, timeout=120)
            response.raise_for_status()
        except requests.RequestException as e:
            raise GoogleSheetLogError(str(e))

    def validate_google_drive_url(self, url: str) -> str:
        """
        Mantém o nome, mas agora devolve a URL normalizada (ou levanta InvalidURL).
        """
        return self._normalize_google_url(url)

    def get_link_data(self, folder_link: str):
        # usar a versão normalizada + params para não quebrar '&'
        norm = self.validate_google_drive_url(folder_link)
        try:
            response = requests.get(self.data_endpoint, params={"link": norm}, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise LinkDataRetrievalError(str(e))

    def get_mktout_folder_link(self, folder_name):
        """
        Tenta localizar a(s) pasta(s) 'Marketing OUT' referentes a *folder_name*.

        Retorna:
        • []               → falha de rede OU nenhuma pasta encontrada
        • [link1, link2…]  → uma ou várias pastas encontradas
        • link             → string, caso haja exatamente uma pasta
        O chamador decide depois como lidar com múltiplos/nenhum link.
        """
        params = {"folderName": folder_name, "driveName": "Marketing OUT"}
        url = f"{self.link_endpoint}?{urlencode(params)}"

        try:
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
            data = resp.json() or []
        except requests.RequestException as exc:
            raise LinkDataRetrievalError(str(exc))

        if not data:                          # nenhuma pasta
            return []

        links = [
            f"https://drive.google.com/drive/folders/{item['id']}"
            for item in data
            if item.get("id")                 # segurança extra
        ]

        # devolve string se for só um link; lista caso contrário
        return links
