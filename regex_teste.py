import re

name = "DD-V-295-001_FindPeon jonatan_EN_30s_1080x1080_V01"
regex = re.compile(r"([A-Z]{2})-([A-Z]{1,3})-\d{3,4}-(\d{3,4})_([a-z\s]+)_",re.IGNORECASE)
result = regex.search(name)

code_game = result.group(1)
type = result.group(2)
game_number = result.group(3)
game_name = result.group(4)

print(f"{code_game}-{type}-{game_number}_{game_name}")