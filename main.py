from classes.commons import (
    load_config_json, build_projects_from_links, copy_projects, notify_slack)
from classes.services import EventTimer
from classes.integrations.google_drive_helper import GoogleDriveHelper
from classes.integrations.slack.slack_superplay import SlackSuperplay
from pathlib import Path
import sys
import json
import os
# sys.tracebacklimit = 0

# ==================== Regular Projects =================
DS_V_042_001_EN = "https://drive.google.com/open?id=1tgRQu6s6E3l3NroUGeACmu8q84R482ex&usp=drive_fs" # archive and versions
DS_V_014_023_EN = "https://drive.google.com/open?id=168eU8anxBh3arp8Ds21jyrIjpH8Bl2v_&usp=drive_fs" # thumbs and endcards
DS_V_013_001_JA = "https://drive.google.com/open?id=12myejlO1hw4Io52OMNuBTRhkG4Z4_5be&usp=drive_fs"
DD_V_195_008_EN = "https://drive.google.com/open?id=1dswXXO_WHILNRuOBXmGaBa8BIJRwftF3&usp=drive_fs"
DD_V_195_009_EN = "https://drive.google.com/open?id=1Up552KkWhKtDkBkAf_KlVfQo71C5gE5i&usp=drive_fs"
DD_V_241_002_DE = "https://drive.google.com/open?id=1ktTBb6M3yLmWwBVu2Z3ypi0jvOVAMN-c&usp=drive_fs"
DS_V_014_025_LOC = "https://drive.google.com/drive/folders/1LW1kRvYLr0ZOgZN0-tNBxguB-bmIpuKh" # with versions in file names
DS_V_011_017_EN = "https://drive.google.com/drive/folders/1OYzPqjTWYuW_60U5OTec8VTbSwur1Q5v"
DS_V_024_002_EN = "https://drive.google.com/drive/folders/1006tvx1QsAkUIOQKzvK5y8apMgu-3U3n" # with thumbs and endcards
DS_V_018_041_LOC = "https://drive.google.com/drive/folders/15zvAuqpXUtQgufTxrq8juM4H6-eRApw-"
DD_V_137_060_EN = "https://drive.google.com/drive/folders/13xS7EhYaAANwU6GieO5leQtW1mGggVnE"

# ==================== AIV Projects =================
DD_AIV_202_002_EN = "https://drive.google.com/drive/folders/1XqoC7xW9ldoayOjh3GdnvDlMcaFp_KJf"

# ==================== Hook Projects =================
DX_H_124_001_NOLANG = "https://drive.google.com/drive/folders/18bVqnWDr7Q9pZUmAmqBUaYWSz4lhzmdc"
DS_H_016_002_NOLANG = "https://drive.google.com/drive/folders/1q2I2T6kRiWbZ0NqQy1qPx-Y6mOAoA5VI"
DS_H_014_001_EN = "https://drive.google.com/drive/folders/1-P4MWisuEDJAKbMXrt_pSSnzSULre19I" #! naming error
TESTE = "https://drive.google.com/drive/folders/1mngFCnuFg-7pB9MHUoKpFfPArj6lLGxv"


# ==================== Carregar projetos ====================
config = load_config_json("config_test.json")
timer = EventTimer()
slack = SlackSuperplay(config)
google = GoogleDriveHelper(config)

projects_links = [
    # DS_V_042_001_EN,
    # DS_V_014_023_EN,
    DS_V_013_001_JA,
    # DD_V_195_008_EN,
    # DD_V_195_009_EN,
    # DD_V_241_002_DE,
    # DS_V_018_041_LOC

    # DX_H_124_001_NOLANG
    # DS_H_016_002_NOLANG
    # DS_H_014_001_EN
    # TESTE
]

projetos = build_projects_from_links(config, projects_links)
# todo gerar um criador de metadados através dos manifestos
print(json.dumps(projetos[0].job_manifest, indent=2, ensure_ascii=False, default=str))
# copy_projects(projetos)
# notify_slack(projetos)

# sequencia lógica
'''
1. build_projects -> cria os projetos
2. projeto.dispatch_out() -> Copia os arquivos e pastas para as outras pastas
3. projeto.send_slack_message() -> envia o log do projeto para o slack
7. Atualiza status do Monday.com
8. Envia log para o Google Sheet
'''
