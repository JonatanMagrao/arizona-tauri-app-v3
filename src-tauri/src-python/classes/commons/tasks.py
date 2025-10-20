from pathlib import Path
from typing import Callable

def build_task(sanitizer:Callable[[Path], str], contents: list[str], out_paths: list[Path]):
    """
    Build the tasks to be copied
    sanitizer: a function to be callable. the function must receive a Path and return a string
    contents: a list of the contents (in string)
    out_paths: a list of the output paths
    """
    tasks = []

    try:
        for content in contents:
            new_file_name = sanitizer(Path(content))
            task = [content] # here is the source

            for out_path in out_paths:
                task.append(out_path / new_file_name)

            tasks.append(task)

        return tasks
    except PermissionError as e:
        raise PermissionError(f"⚠️ Permission denied: {e}")