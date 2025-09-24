nomes = [
  ["Jonatan","Dani","Ricardo"],
  ["José","Antonia","Pedro"]
]

for collection in nomes:
  print(f"From: {collection[0]}")
  for name in collection[1:]:
    print(f"\tTo: {name}")
  print("")


