from functions import ensure_folder_path, find_file_in_tree_from
from classes.GoogleDriveHelper import GoogleDriveHelper
from classes.LocalPathHelper import LocalPathHelper
from classes.ProjectTypeIdentifier import ProjectTypeIdentifier
from classes.FileCopier import FileCopier
from pathlib import Path
import sys
import json
# sys.tracebacklimit = 0

config = {
    "mktout_base_path": r"G:\Drives compartilhados\Marketing OUT",
    "test_path": r"C:\Users\PC\Downloads\marketing_out_master_test",
    "shared_drive_labels": ["Shared drives", "Drives compartilhados"],
    "company_email_domain": "@superplay.co",  # ! implementar e testar no mac
    "google_endpoints": {
        "data_endpoint": "https://script.google.com/macros/s/AKfycby8gizyZ1q6JccTJijV29CgRfWnWnMzbMzpiklu1KzOF_4QCuPfOPtuyHJ2AiadQ9G_wQ/exec",
        "link_endpoint": "https://script.google.com/macros/s/AKfycbxHYtlVBwmY-E5u9D0MJvDk9fISkhGpKny851Odt7ljDa8Q2oj_evQRRS8OsLXWCe6UOw/exec",
        "sheet_endpoint": "https://script.google.com/macros/s/AKfycbylkxY2oDyJV9wovLjdmJrsTi3gMISfTQGvrILdjnVBpyTB7fVncHSVzkU0YgnK4JGDSQ/exec"
    },
    "supported_languages": [
        {"lang": "Arabic", "abbr": "ar"},
        {"lang": "Chinese", "abbr": "zh"},
        {"lang": "Dutch", "abbr": "nl"},
        {"lang": "English", "abbr": "en"},
        {"lang": "French", "abbr": "fr"},
        {"lang": "French Canada", "abbr": "fr-ca"},
        {"lang": "German", "abbr": "de"},
        {"lang": "Hebrew", "abbr": "he"},
        {"lang": "Hungarian", "abbr": "hu"},
        {"lang": "Indonesian", "abbr": "id"},
        {"lang": "Italian", "abbr": "it"},
        {"lang": "Japanese", "abbr": "ja"},
        {"lang": "Korean", "abbr": "kr"},
        {"lang": "Malay", "abbr": "ms"},
        {"lang": "Polish", "abbr": "pl"},
        {"lang": "Portuguese", "abbr": "pt"},
        {"lang": "Portuguese (Brazil)", "abbr": "pt-br"},
        {"lang": "Romanian", "abbr": "ro"},
        {"lang": "Russian", "abbr": "ru"},
        {"lang": "Spanish", "abbr": "es"},
        {"lang": "Spanish (Spain)", "abbr": "es-sp"},
        {"lang": "Spanish (Latin American)", "abbr": "es-la"},
        {"lang": "Spanish Mexico", "abbr": "es-mx"},
        {"lang": "Thai", "abbr": "th"},
        {"lang": "Turkish", "abbr": "tr"},
        {"lang": "Ukrainian", "abbr": "uk"}
    ],
    "project_types": {
        "P": {
            "label": "Playable",
            "folder_path": "06-Playables"
        },
        "V": {
            "label": "Video",
            "folder_path": "07-Videos"
        },
        "H": {
            "label": "Hook",
            "folder_path": "07-Videos"
        },
        "UGC": {
            "label": "UGC",
            "folder_path": "08-UGC"
        },
        "AIV": {
            "label": "AIV",
            "folder_path": "09-SettAI"
        },
    },
    "games": {
        "DS": {
            "name": "Disney Solitaire",
            "mktout_folder_name": "DS_DisneySolitaire_OUT"
        },
        "DD": {
            "name": "Dice Dreams",
            "mktout_folder_name": "DD_DiceDreams_OUT"
        },
        "DX": {
            "name": "Domino Dreams",
            "mktout_folder_name": "DX_DominoDreams_OUT"
        }
    },
    "ignored_copy_file_extensions": [],
    "ignored_copy_folder_names": []

}


DS_V_042_001_EN = "https://drive.google.com/open?id=1tgRQu6s6E3l3NroUGeACmu8q84R482ex&usp=drive_fs"
DS_V_014_023_EN = "https://drive.google.com/open?id=168eU8anxBh3arp8Ds21jyrIjpH8Bl2v_&usp=drive_fs"
DS_V_013_001_JA = "https://drive.google.com/open?id=12myejlO1hw4Io52OMNuBTRhkG4Z4_5be&usp=drive_fs"
DD_V_195_008_EN = "https://drive.google.com/open?id=1dswXXO_WHILNRuOBXmGaBa8BIJRwftF3&usp=drive_fs"
DD_V_195_009_EN = "https://drive.google.com/open?id=1Up552KkWhKtDkBkAf_KlVfQo71C5gE5i&usp=drive_fs"
DD_V_241_002_DE = "https://drive.google.com/open?id=1ktTBb6M3yLmWwBVu2Z3ypi0jvOVAMN-c&usp=drive_fs"

DD_V_137_060_EN = "https://drive.google.com/drive/folders/13xS7EhYaAANwU6GieO5leQtW1mGggVnE"
DD_AIV_202_002_EN = "https://drive.google.com/drive/folders/1XqoC7xW9ldoayOjh3GdnvDlMcaFp_KJf"
DX_H_124_001_NOLANG = "https://drive.google.com/drive/folders/18bVqnWDr7Q9pZUmAmqBUaYWSz4lhzmdc"

# load project data from Google Drive link
try:
    google_helper = GoogleDriveHelper(config)
    google_data = google_helper.get_link_data(DD_V_241_002_DE)
    project_identifier = ProjectTypeIdentifier(config, google_data)
except Exception as e:
    raise e

# create project and copy files
projeto = project_identifier.create_project

game_name = projeto.game_name
project_name = projeto.project_name
language = projeto.language
root_mktout_folder_path = projeto.root_marketing_out_folder_path
marketing_out_game_folder_path = projeto.marketing_out_game_folder_path
root_master_folder_path = projeto.root_master_folder_path
mktout_folder_path = projeto.marketing_out_folder_path
master_folder_path = projeto.master_folder_path
full_local_path = projeto.local_path
google_local_path = projeto.gdrive_local_path_path

print("")
print(f"Game name: {game_name}")
print(f"Project name: {project_name}")
print(f"Project language: {language}")
print(
    f"Marketing out path: {mktout_folder_path}: {mktout_folder_path.exists()}")
print(
    f"Master folder path: {master_folder_path}: {master_folder_path.exists()}")
print(
    f"Root master folder path: {root_master_folder_path}: {root_master_folder_path.exists()}")
print(
    f"Marketing Out game folder path: {marketing_out_game_folder_path}: {marketing_out_game_folder_path.exists()}")
print(
    f"Root marketing out folder path: {root_mktout_folder_path}: {root_mktout_folder_path.exists()}")
print("")
print(f"Local path: {full_local_path}: {full_local_path.exists()}")
print(f"Google local path: {google_local_path}: {google_local_path.exists()}")
print("")

#! talvez implementar uma saída de metadados também já direto dentro de cada tipo de projeto, como no SuperplayVideoProject
#! a ideia é que daqui para baixo, seja tudo interno na classe SuperplayVideoProject, eu implemente o botão de copy e eu só chame ele. simples assim!
#! validações de se é multi_projects, será interno também, facilitando o processo de saída

# projeto.deploy_outputs(google_local_path)
