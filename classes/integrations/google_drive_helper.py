import requests
from urllib.parse import (urlencode, urlparse)
from classes.services import LoggerManager
logger = LoggerManager.get_logger(__name__)


class GoogleDriveHelper:
    def __init__(self, config: dict):
        self.config = config
        self._google_endpoints:dict = config.get("google_endpoints", {})
        self.data_endpoint = self._google_endpoints.get("data_endpoint")
        self.link_endpoint = self._google_endpoints.get("link_endpoint")
        self.sheet_endpoint = self._google_endpoints.get("sheet_endpoint")

    def sheet_log(self, info: dict):
        try:
            response = requests.post(self.sheet_endpoint, json=info, timeout=120)
            response.raise_for_status()
            logger.debug(f"Sheet log response: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Error sending sheet log: {e}")

    def validate_google_drive_url(self, url: str):
        parsed = urlparse(url)
        if parsed.netloc != "drive.google.com":
            print(f"Invalid Google Drive URL: {url}")
            # raise InvalidURL(url)

    def get_link_data(self, folder_link):
        self.validate_google_drive_url(folder_link)
        url = f"{self.data_endpoint}?link={folder_link}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error while calling Google Drive API: {e}")
            # raise LinkDataRetrievalError(str(e))
            print(f"Error while calling Google Drive API: {e}")

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
            logger.warning("Fail retrieving link for '%s': %s", folder_name, exc)
            return []                         # indica erro de rede

        if not data:                          # nenhuma pasta
            return []

        links = [
            f"https://drive.google.com/drive/folders/{item['id']}"
            for item in data
            if item.get("id")                 # segurança extra
        ]

        # devolve string se for só um link; lista caso contrário
        return links
