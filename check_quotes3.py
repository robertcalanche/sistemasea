path = r"c:\Users\rober\Documents\Proyecto_Evaluacion\modulo_superadmin.py"
state = False
with open(path, encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        count = line.count('"""')
        if count > 0:
            for j in range(count):
                state = not state
                print(f"line {i} {'OPEN' if state else 'CLOSE'}")

print("FINAL STATE", state)
