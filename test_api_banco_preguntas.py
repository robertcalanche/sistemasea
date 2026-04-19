import requests


# 1. Listar preguntas (vacío)
BASE = "http://localhost:5000/api/v1/banco-preguntas"
r = requests.get(BASE)
print("Listar preguntas:", r.json())

# 2. Crear pregunta
nueva = {
    "evaluacion": "demo",
    "area": "matematicas",
    "grado": "5",
    "enunciado": "¿Cuánto es 2+2?",
    "opcion_a": "3",
    "opcion_b": "4",
    "opcion_c": "5",
    "opcion_d": "6",
    "correcta": "B",
}
r = requests.post(BASE, json=nueva)
print("Crear pregunta:", r.json())

# 3. Listar preguntas (debe haber 1)
r = requests.get(BASE)
print("Listar preguntas:", r.json())

# 4. Editar pregunta (primer id)
items = r.json().get("items", [])
if items:
    id_preg = items[0]["id"]
    r = requests.put(
        f"{BASE}/{id_preg}",
        json={"enunciado": "¿Cuánto es 3+3?", "opcion_b": "6", "correcta": "B"},
    )
    print("Editar pregunta:", r.json())

    # 5. Eliminar pregunta
    r = requests.delete(f"{BASE}/{id_preg}")
    print("Eliminar pregunta:", r.json())

# 6. Estadísticas
r = requests.get(f"{BASE}/estadisticas")
print("Estadísticas:", r.json())

# 7. Validación de integridad
r = requests.get(f"{BASE}/validar")
print("Validación integridad:", r.json())

# 8. Catálogo grados
r = requests.get(f"{BASE}/catalogo/grados")
print("Catálogo grados:", r.json())

# 9. Catálogo áreas
r = requests.get(f"{BASE}/catalogo/areas")
print("Catálogo áreas:", r.json())

# 10. Catálogo evaluaciones
r = requests.get(f"{BASE}/catalogo/evaluaciones")
print("Catálogo evaluaciones:", r.json())
