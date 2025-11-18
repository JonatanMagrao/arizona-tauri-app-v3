import re

lista = ["jonatan","shared drives","es"]
lista2 = ["c:","drives compartilhados","pt-br"]

for i in lista2:
  if re.match(r"^[a-z]{2}(-[a-z]{2})?$",i,flags=re.IGNORECASE):
    print(i)