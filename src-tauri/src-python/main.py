import bootstrap
from classes.commons import (
    load_config_json, build_projects_from_links, copy_projects,
    notify_slack, generate_project_metadata, update_monday_status
)
from classes.services import (EventTimer, TestEnvStore)
from classes.integrations.google_drive_helper import GoogleDriveHelper
from classes.integrations.slack.slack_superplay import SlackSuperplay
from classes.integrations.monday.monday_client import MondayClient
from pathlib import Path
import sys
import json
import os
import subprocess
# sys.tracebacklimit = 0

# ==================== Regular Projects =================
# archive and versions
DS_V_042_001_EN = "https://drive.google.com/open?id=1tgRQu6s6E3l3NroUGeACmu8q84R482ex&usp=drive_fs"
# thumbs and endcards
DS_V_014_023_EN = "https://drive.google.com/open?id=168eU8anxBh3arp8Ds21jyrIjpH8Bl2v_&usp=drive_fs"
DS_V_013_001_JA = "https://drive.google.com/open?id=12myejlO1hw4Io52OMNuBTRhkG4Z4_5be&usp=drive_fs"
DD_V_195_008_EN = "https://drive.google.com/open?id=1dswXXO_WHILNRuOBXmGaBa8BIJRwftF3&usp=drive_fs"
DD_V_195_009_EN = "https://drive.google.com/open?id=1Up552KkWhKtDkBkAf_KlVfQo71C5gE5i&usp=drive_fs"
DD_V_241_002_DE = "https://drive.google.com/open?id=1ktTBb6M3yLmWwBVu2Z3ypi0jvOVAMN-c&usp=drive_fs"
# with versions in file names
DS_V_014_025_LOC = "https://drive.google.com/drive/folders/1LW1kRvYLr0ZOgZN0-tNBxguB-bmIpuKh"
DS_V_011_017_EN = "https://drive.google.com/drive/folders/1OYzPqjTWYuW_60U5OTec8VTbSwur1Q5v"
# with thumbs and endcards
DS_V_024_002_EN = "https://drive.google.com/drive/folders/1006tvx1QsAkUIOQKzvK5y8apMgu-3U3n"
DS_V_018_041_LOC = "https://drive.google.com/drive/folders/15zvAuqpXUtQgufTxrq8juM4H6-eRApw-"
DD_V_137_060_EN = "https://drive.google.com/drive/folders/13xS7EhYaAANwU6GieO5leQtW1mGggVnE"

# ==================== AIV Projects =================
DD_AIV_202_002_EN = "https://drive.google.com/drive/folders/1XqoC7xW9ldoayOjh3GdnvDlMcaFp_KJf"

# ==================== Hook Projects =================
DX_H_124_001_NOLANG = "https://drive.google.com/drive/folders/18bVqnWDr7Q9pZUmAmqBUaYWSz4lhzmdc"
DS_H_016_002_NOLANG = "https://drive.google.com/drive/folders/1q2I2T6kRiWbZ0NqQy1qPx-Y6mOAoA5VI"
DS_H_014_001_EN = "https://drive.google.com/drive/folders/1-P4MWisuEDJAKbMXrt_pSSnzSULre19I"  # ! naming error
TESTE = "https://drive.google.com/drive/folders/1mngFCnuFg-7pB9MHUoKpFfPArj6lLGxv"


# ==================== Carregar projetos ====================
config = load_config_json("config.json")
timer = EventTimer()
slack = SlackSuperplay(config)
google = GoogleDriveHelper(config)
monday = MondayClient(config)
test_store = TestEnvStore()

projects_links = [
    # DS_V_042_001_EN,
    # DS_V_014_023_EN,
    # DS_V_013_001_JA,
    # DD_V_195_008_EN,
    # DD_V_195_009_EN,
    # DD_V_241_002_DE,
    # DS_V_018_041_LOC,

    # DX_H_124_001_NOLANG,
    # DS_H_016_002_NOLANG,
    # DS_H_014_001_EN,
    # TESTE,
    # "https://superplay.monday.com/boards/5239196091/views/115751609/pulses/18113029198/posts/4562215920",
    # "https://superplay.monday.com/boards/5239196091/pulses/18142354137/posts/4566450446",
    # "https://superplay.monday.com/boards/5239196091/pulses/18147479438/posts/4566449384",
    # "https://superplay.monday.com/boards/5239196091/pulses/18075962660/posts/4547143430?reply=reply-4580074122",
    # "https://superplay.monday.com/boards/10072840854/pulses/10072841002",
    # "https://superplay.monday.com/boards/5239196091/pulses/9736143323",
    # "https://superplay.monday.com/boards/5239196091/pulses/18199074206/posts/4591896756?reply=reply-4593131909",
    # "https://superplay.monday.com/boards/5239196091/pulses/18199215678/posts/4591896239?reply=reply-4593132440",
    # "https://superplay.monday.com/boards/5239196091/pulses/9864252617",
    # "https://drive.google.com/drive/folders/1TeGwKhhkd_lOyiTPfrqsiVMnR67PeAce",
    "https://superplay.monday.com/boards/5239196091/pulses/18147477761/posts/4569309015?reply=reply-4605634061"
]

_tauri_plugin_functions = [
    "loadProject",
    "copiar",
    "slackMessage",
    "mondayStatus",
    "openFolder",
    "openThumbnail",
    "openParentFileFolder",
    "getProjectMetadata"
]

_projetos = None
_project_metadata = None

def getProjectMetadata():
    global _project_metadata
    return json.dumps(_project_metadata or [], ensure_ascii=False, indent=2, default=str)

def loadProject(link_list: list):
    timer.start("Loading")
    projetos = build_projects_from_links(config, link_list)
    project_metadata = generate_project_metadata(projetos)
    global _projetos, _project_metadata
    _projetos = projetos
    _project_metadata = project_metadata
    result = json.dumps(project_metadata, ensure_ascii=False,
                        indent=2, default=str)
    timer.end("Loading")
    print(timer.log())
    print(result)
    return result


def copiar():
    copy_metadata = copy_projects(_projetos)
    result = json.dumps(copy_metadata, ensure_ascii=False,
                        indent=2, default=str)
    
    # update_project_metadata = generate_project_metadata(_projetos)
    global _project_metadata

    _project_metadata = copy_metadata

    print(result)
    return result


def slackMessage():
    slack_metadata = notify_slack(_projetos)
    result = json.dumps(slack_metadata, ensure_ascii=False,
                        indent=2, default=str)
    print(result)
    return result


def mondayStatus():
    monday_status_metadata = update_monday_status(
        config, monday, _project_metadata)
    result = json.dumps(monday_status_metadata,
                        ensure_ascii=False, indent=2, default=str)
    print(result)
    return result


def openParentFileFolder(filePath:str):
    parent_path = str(Path(filePath).parent)
    os.startfile(parent_path)

def openFolder(filePath: str):
    os.startfile(filePath)

def openThumbnail(filePath: str):
    subprocess.run(["thumbnail",filePath])

# projetos = build_projects_from_links(config, projects_links)

# project_metadata = generate_project_metadata(projetos)
# print(json.dumps(project_metadata, ensure_ascii=False, indent=2, default=str))

# copy_metadata = copy_projects(projetos)
# print(json.dumps(copy_metadata, ensure_ascii=False, indent=2, default=str))

# slack_metadata = notify_slack(projetos)
# print(json.dumps(slack_metadata, ensure_ascii=False, indent=2, default=str))

# monday_status_metadata = update_monday_status(config, monday, project_metadata)
# print(json.dumps(monday_status_metadata, ensure_ascii=False, indent=2, default=str))


# logic sequence
'''
1. build_projects → get project info and build (metadata)
2. project.dispatch_out() → copies files and folders to the specified directories
3. project.send_slack_message() → sends the project log to Slack
4. Update Monday.com status
5. Miro (or the equivalent in Google Sheets or a proprietary app)
6. Send log to Google Sheets
'''
