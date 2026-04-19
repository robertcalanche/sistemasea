import re

path = r"c:\Users\rober\Documents\Proyecto_Evaluacion\modulo_superadmin.py"
with open(path, encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if '"""' in line:
            print(i, line.rstrip(), line.count('"""'))

text = open(path, encoding="utf-8").read()
print("total triple quotes", text.count('"""'))
