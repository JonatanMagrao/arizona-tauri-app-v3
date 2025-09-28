from project_discovery import (
    build_projects,
    collect_copy_paths,
    get_full_metadata,
)
from classes.FileCopier import FileCopier
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
    "supported_languages": {
        "ar": {"lang": "Arabic", "abbr": "ar"},
        "zh": {"lang": "Chinese", "abbr": "zh"},
        "nl": {"lang": "Dutch", "abbr": "nl"},
        "en": {"lang": "English", "abbr": "en"},
        "fr": {"lang": "French", "abbr": "fr"},
        "fr-ca": {"lang": "French Canada", "abbr": "fr-ca"},
        "de": {"lang": "German", "abbr": "de"},
        "he": {"lang": "Hebrew", "abbr": "he"},
        "hu": {"lang": "Hungarian", "abbr": "hu"},
        "id": {"lang": "Indonesian", "abbr": "id"},
        "it": {"lang": "Italian", "abbr": "it"},
        "ja": {"lang": "Japanese", "abbr": "ja"},
        "kr": {"lang": "Korean", "abbr": "kr"},
        "ms": {"lang": "Malay", "abbr": "ms"},
        "pl": {"lang": "Polish", "abbr": "pl"},
        "pt": {"lang": "Portuguese", "abbr": "pt"},
        "pt-br": {"lang": "Portuguese (Brazil)", "abbr": "pt-br"},
        "ro": {"lang": "Romanian", "abbr": "ro"},
        "ru": {"lang": "Russian", "abbr": "ru"},
        "es": {"lang": "Spanish", "abbr": "es"},
        "es-sp": {"lang": "Spanish (Spain)", "abbr": "es-sp"},
        "es-la": {"lang": "Spanish (Latin American)", "abbr": "es-la"},
        "es-mx": {"lang": "Spanish Mexico", "abbr": "es-mx"},
        "th": {"lang": "Thai", "abbr": "th"},
        "tr": {"lang": "Turkish", "abbr": "tr"},
        "uk": {"lang": "Ukrainian", "abbr": "uk"}
    },
    "project_types": {
        "P": {
            "label": "Playable",
            "folder_path": "06-Playables",
            "ignore_list": {
                "files_extensions": [],
                "folder_names": []
            }
        },
        "V": {
            "label": "Video",
            "folder_path": "07-Videos",
            "ignore_list": {
                "file_extensions": [".mov", ".avi", ".mkv"],
                "folder_names": ["Archive", "_Archive"]
            }
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
    "ignored_copy_folder_names": ["_Archive"]

}


DS_V_042_001_EN = "https://drive.google.com/open?id=1tgRQu6s6E3l3NroUGeACmu8q84R482ex&usp=drive_fs"
DS_V_014_023_EN = "https://drive.google.com/open?id=168eU8anxBh3arp8Ds21jyrIjpH8Bl2v_&usp=drive_fs"
DS_V_013_001_JA = "https://drive.google.com/open?id=12myejlO1hw4Io52OMNuBTRhkG4Z4_5be&usp=drive_fs"
DD_V_195_008_EN = "https://drive.google.com/open?id=1dswXXO_WHILNRuOBXmGaBa8BIJRwftF3&usp=drive_fs"
DD_V_195_009_EN = "https://drive.google.com/open?id=1Up552KkWhKtDkBkAf_KlVfQo71C5gE5i&usp=drive_fs"
DD_V_241_002_DE = "https://drive.google.com/open?id=1ktTBb6M3yLmWwBVu2Z3ypi0jvOVAMN-c&usp=drive_fs"
DS_V_014_025_LOC = "https://drive.google.com/drive/folders/1LW1kRvYLr0ZOgZN0-tNBxguB-bmIpuKh"
DS_V_011_017_EN = "https://drive.google.com/drive/folders/1OYzPqjTWYuW_60U5OTec8VTbSwur1Q5v"
DS_V_024_002_EN = "https://drive.google.com/drive/folders/1006tvx1QsAkUIOQKzvK5y8apMgu-3U3n"

DD_V_137_060_EN = "https://drive.google.com/drive/folders/13xS7EhYaAANwU6GieO5leQtW1mGggVnE"
DD_AIV_202_002_EN = "https://drive.google.com/drive/folders/1XqoC7xW9ldoayOjh3GdnvDlMcaFp_KJf"
DX_H_124_001_NOLANG = "https://drive.google.com/drive/folders/18bVqnWDr7Q9pZUmAmqBUaYWSz4lhzmdc"


# file_copier = FileCopier(config)
projetos = build_projects(config, DS_V_024_002_EN)
tasks = collect_copy_paths(projetos)
metadata = get_full_metadata(projetos)
file_copier = FileCopier(metadata[0].get("ignore_list"))

print(json.dumps(metadata, indent=2, ensure_ascii=False, default=str))

file_copier.copy_all_projects(tasks)

# project_types = config.get("project_types").get("V").get("ignore_list").get("file_extensions")

# print(json.dumps(project_types, indent=2, ensure_ascii=False, default=str))
