import requests
import json

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbz29apvum494bi5YWleI6GxwE-zmqmz6rPbTPxmiWQx-NRj8Cj7LBePZ04SnxvBF1PR/exec"

params = {
    "id": "1VeTiG3Ob04UXBdDFNXACUwWbDwJs73IAcn2tGDEtlkk",  # spreadsheet id
    # "sheet": "slack_oauth_config",                         # aba
    # "sheet": "google_endpoints",                         # aba
    "sheet": "games",                         # aba
    "ttl": "180",                                          # cache em segundos (1..3600)
    "v": "2025-10-09"                                      # opcional: bust/cache version
}

resp = requests.get(WEBAPP_URL, params=params, timeout=60)
resp.raise_for_status()
slack_oauth_config = resp.json()
print(json.dumps(slack_oauth_config, ensure_ascii=False, indent=2, default=str))
