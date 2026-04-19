# improved quote checker
path = r"c:\Users\rober\Documents\Proyecto_Evaluacion\modulo_superadmin.py"
with open(path, encoding="utf-8") as f:
    state = False
    for i, line in enumerate(f, 1):
        count = line.count('"""')
        if count > 0:
            print(i, repr(line.rstrip()), count)
            for _ in range(count):
                state = not state
    if state:
        print("UNMATCHED OPEN at EOF")

text = open(path, encoding="utf-8").read()
print("total triple quotes", text.count('"""'))
