from project_discovery import build_projects
from utils import load_config_json
from classes.FileCopier import FileCopier
from classes.slack.SlackSuperplay import SlackSuperplay
from classes.GoogleDriveHelper import GoogleDriveHelper
from classes.EventTimer import EventTimer
from pathlib import Path
import sys, json, os
# sys.tracebacklimit = 0

DS_V_042_001_EN = "https://drive.google.com/open?id=1tgRQu6s6E3l3NroUGeACmu8q84R482ex&usp=drive_fs" # archive and versions
DS_V_014_023_EN = "https://drive.google.com/open?id=168eU8anxBh3arp8Ds21jyrIjpH8Bl2v_&usp=drive_fs"
DS_V_013_001_JA = "https://drive.google.com/open?id=12myejlO1hw4Io52OMNuBTRhkG4Z4_5be&usp=drive_fs" # thumbs and endcards
DD_V_195_008_EN = "https://drive.google.com/open?id=1dswXXO_WHILNRuOBXmGaBa8BIJRwftF3&usp=drive_fs"
DD_V_195_009_EN = "https://drive.google.com/open?id=1Up552KkWhKtDkBkAf_KlVfQo71C5gE5i&usp=drive_fs"
DD_V_241_002_DE = "https://drive.google.com/open?id=1ktTBb6M3yLmWwBVu2Z3ypi0jvOVAMN-c&usp=drive_fs"
DS_V_014_025_LOC = "https://drive.google.com/drive/folders/1LW1kRvYLr0ZOgZN0-tNBxguB-bmIpuKh"
DS_V_011_017_EN = "https://drive.google.com/drive/folders/1OYzPqjTWYuW_60U5OTec8VTbSwur1Q5v" # with versions in file names
DS_V_024_002_EN = "https://drive.google.com/drive/folders/1006tvx1QsAkUIOQKzvK5y8apMgu-3U3n"
DS_V_018_041_LOC = "https://drive.google.com/drive/folders/15zvAuqpXUtQgufTxrq8juM4H6-eRApw-" # with thumbs and endcards
DD_V_137_060_EN = "https://drive.google.com/drive/folders/13xS7EhYaAANwU6GieO5leQtW1mGggVnE"
DD_AIV_202_002_EN = "https://drive.google.com/drive/folders/1XqoC7xW9ldoayOjh3GdnvDlMcaFp_KJf"
DX_H_124_001_NOLANG = "https://drive.google.com/drive/folders/18bVqnWDr7Q9pZUmAmqBUaYWSz4lhzmdc"

# ==================== Carregar projetos ====================
config = load_config_json("config.json")
timer = EventTimer()
slack = SlackSuperplay()
google = GoogleDriveHelper(config)

timer.start("build_projects")
projeto = build_projects(config, DS_V_042_001_EN)
timer.end("build_projects")

timer.start("job_manifest")
job_manifest: list[dict] = projeto.job_manifest
print(json.dumps(job_manifest, indent=2, ensure_ascii=False, default=str))
timer.end("job_manifest")

# timer.start("dispatch_out")
# projeto.dispatch_out()
# timer.end("dispatch_out")

# timer.start("build_slack_payload")
# slack_payload = projeto.build_slack_payload()
# print(json.dumps(slack_payload, indent=2, ensure_ascii=False, default=str))
# timer.end("build_slack_payload")

# timer.start("send_slack_message")
# projeto.send_slack_message()
# timer.end("send_slack_message")

timer.log()


# sequencia lógica
'''
1. build_projects -> cria os projetos
2. projeto.dispatch_out() -> Copia os arquivos e pastas para as outras pastas
3. projeto.send_slack_message() -> envia o log do projeto para o slack
7. Atualiza status do Monday.com
8. Envia log para o Google Sheet
'''
