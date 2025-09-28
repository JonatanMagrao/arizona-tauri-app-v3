import re
nome = "DS-V-024-002_Puzzle_DonaldDuck_EN_30s_v02"

resultado = re.sub(r"_v\d{1,3}","",nome,re.IGNORECASE)
print(resultado)