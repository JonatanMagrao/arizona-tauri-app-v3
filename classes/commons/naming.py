import re

def normalize_old_project_name(project_name: str) -> str:
    match = re.match(r"([A-Z]{2})_(\d{3,4})_(.*)", project_name, re.IGNORECASE)
    if not match:
        return project_name

    game_prefix = match.group(1).upper()
    game_number = match.group(2)
    rest = match.group(3)
    
    return f"{game_prefix}-V-{game_number}_{rest}"