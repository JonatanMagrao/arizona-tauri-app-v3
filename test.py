import re
import json
from pathlib import Path
from classes.FileCopier import FileCopier
from typing import Callable

ignore_list = {
    "file_extensions": [".mov", ".avi", ".mkv", ".gif"],
    "folder_names": ["Archive", "_Archive", " Thumbs", "EndCards"]
}

content = [
    r"G:\Drives compartilhados\Marketing_DS_2025_H2\Creative Projects\Video\DS-V-024_Puzzle_LiloStitch\Comp\EN\DS-V-024-002_Puzzle_DonaldDuck_EN_30s\Render\(Internal Review)\EN\DS-V-024-002_Puzzle_DonaldDuck_EN_30s_1080x1920_v02.mp4",
    r"G:\Drives compartilhados\Marketing_DS_2025_H2\Creative Projects\Video\DS-V-024_Puzzle_LiloStitch\Comp\EN\DS-V-024-002_Puzzle_DonaldDuck_EN_30s\Render\(Internal Review)\EN\DS-V-024-002_Puzzle_DonaldDuck_EN_30s_1920x1080_v02.mp4",
    r"G:\Drives compartilhados\Marketing_DS_2025_H2\Creative Projects\Video\DS-V-024_Puzzle_LiloStitch\Comp\EN\DS-V-024-002_Puzzle_DonaldDuck_EN_30s\Render\(Internal Review)\EN\DS-V-024-002_Puzzle_DonaldDuck_EN_30s_1080x1080_v03.mp4",
    r"G:\Drives compartilhados\Marketing_DS_2025_H2\Creative Projects\Video\DS-V-024_Puzzle_LiloStitch\Comp\EN\DS-V-024-002_Puzzle_DonaldDuck_EN_30s\Render\(Internal Review)\EN\DS-V-024-002_Puzzle_DonaldDuck_EN_30s_1080x1350_v02.mp4"
]

mktout_path = r"C:\Users\PC\Downloads\marketing_out_master_test\teste_mktout"
master_path = r"C:\Users\PC\Downloads\marketing_out_master_test\teste_master"


def sanitize_file_name(file: Path) -> str:
    remove_version = re.compile(r"_v\d{1,3}", flags=re.IGNORECASE)
    final_file_path_name = remove_version.sub("", file.name)

    return final_file_path_name

def build_task(sanitizer:Callable[[Path], str], contents: list[str], out_paths: list[Path]):
    """
    Build the tasks to be copied
    sanitizer: a function to be callable. the function must receive a Path and return a string
    contents: a list of the contents (in string)
    out_paths: a list of the output paths
    """
    tasks = []

    for content in contents:
        new_file_name = sanitizer(Path(content))
        task = [content] # here is the source

        for out_path in out_paths:
            task.append(out_path / f"{new_file_name}")

        tasks.append(task)

    return tasks

# out_paths = [Path(mktout_path), Path(master_path)]
# tasks = build_task(sanitize_file_name, content, out_paths)

# file_copier = FileCopier()
# file_copier.copy_variadic_groups(tasks)

# print(json.dumps(tasks, indent=2, ensure_ascii=False, default=str))

name = "DS-V-014-025_BuildSplit _MoanaReverse_DS-H-009-001_EN_35s"

compilar = re.compile(r"\s*_\s*", flags=re.IGNORECASE)
print(compilar.sub("_", name))