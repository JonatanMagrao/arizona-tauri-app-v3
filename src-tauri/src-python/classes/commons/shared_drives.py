import platform
import string
import os
import re
from pathlib import Path

SHARED_DRIVE_LABELS = ["Shared drives", "Drives compartilhados"]
IS_MAC = platform.system().lower() == "darwin"

def get_full_path_win() -> Path:
    def list_drives_os():
        return [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]

    for drive in list_drives_os():
        for root in SHARED_DRIVE_LABELS:
            full_path = Path(drive, root, "Marketing OUT")
            if full_path.exists():
                return Path(drive,root)

    raise Exception("Local Google Drive not found (Windows)")
    

def get_full_path_mac() -> Path:
    home = Path.home()
    for item in home.iterdir():
        if re.match(r".*@superplay\.co - Google Drive", item.name):
            for root in SHARED_DRIVE_LABELS:
                full_path = Path(home, item, root)
                if full_path.exists():
                    return full_path
                
    raise Exception("Local Google Drive not found (macOS)")
    

def full_local_path() -> Path:
    """Automatically selects the correct resolver based on the OS."""
    return get_full_path_mac() if IS_MAC else get_full_path_win()