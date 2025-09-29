import re, json
from pathlib import Path
ignore_list = {
    "file_extensions": [".mov", ".avi", ".mkv", ".gif"],
    "folder_names": ["Archive", "_Archive"," Thumbs", "EndCards"]
}

path = Path(r"G:\\Drives compartilhados\\Marketing_DD_MGX_Masters_01\\DD_195_Stickers_LastSticker-Retro\\Render\\(Internal Review)\\03\\DD-V-195-008_LastSticker_DD-VEO-001-001_EN_30s")

content = []
ignore_exts = {ext.lower().strip() for ext in ignore_list["file_extensions"]}
ignore_folders = {name.lower().strip() for name in ignore_list["folder_names"]}
for item in path.iterdir():
    
    if item.is_file() and item.suffix.lower().strip() not in ignore_exts:
        content.append(item)

    if item.is_dir() and item.stem.lower().strip() not in ignore_folders:
        content.append(item)

print(json.dumps(content, indent=2, ensure_ascii=False, default=str))