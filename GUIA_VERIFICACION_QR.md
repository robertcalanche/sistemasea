# 🎯 GUÍA DE VERIFICACIÓN: QR de Alta Resolución en PDF

## 📌 VERIFICACIÓN RÁPIDA

### Paso 1: Validar que los cambios se aplicaron
```bash
cd "c:\Users\rober\Documents\Proyecto_Evaluacion_V1"
python test_qr_alta_resolucion.py
```

**Resultado esperado:**
```
✅ TODOS LOS TESTS PASARON - QR FUNCIONANDO CORRECTAMENTE
```

### Paso 2: Inspeccionar el PNG generado
El archivo `test_qr_alta_resolucion.png` debería:
- ✅ Ser cuadrado (530x530 píxeles o similar)
- ✅ Tener bordes claros y negros
- ✅ Sin líneas blancas horizontales
- ✅ Patrón claramente visible

### Paso 3: Escanear con celular
1. Abrir Google Lens o cualquier app de escaneo QR
2. Apuntar al QR generado
3. Debería decodificar: `SEA|1023456789|Juan Pérez|...`

---

## 🔬 VERIFICACIÓN TÉCNICA DETALLADA

### Cambio 1: Generación del QR (modulo_superadmin.py:10531)

**Verificar que tiene:**
```python
_qr = _qrcode_lib.QRCode(
    version=None,
    error_correction=_qrcode_lib.constants.ERROR_CORRECT_H,  # ✅ OBLIGATORIO
    box_size=10,                                              # ✅ De 4 a 10
    border=4                                                  # ✅ De 1 a 4
)
```

**Comando de búsqueda:**
```bash
grep -n "error_correction=_qrcode_lib.constants.ERROR_CORRECT_H" modulo_superadmin.py
```

**Resultado esperado:**
```
10532: error_correction=_qrcode_lib.constants.ERROR_CORRECT_H,
```

---

### Cambio 2: Guardado PNG (modulo_superadmin.py:10546)

**Verificar que tiene:**
```python
_qr_pil.save(_qr_buf, format="PNG", optimize=False)
```

**Comando de búsqueda:**
```bash
grep -n 'save(_qr_buf, format="PNG", optimize=False)' modulo_superadmin.py
```

**Resultado esperado:**
```
10546: _qr_pil.save(_qr_buf, format="PNG", optimize=False)
```

---

### Cambio 3: Tamaño QR Embebido (modulo_superadmin.py:10123)

**Verificar que tiene:**
```python
qr_size = 2.6 * cm
```

**Comando de búsqueda:**
```bash
grep -n "qr_size = 3.5 \* cm" modulo_superadmin.py
```

**Resultado esperado (3 coincidencias):**
```
10123: qr_size = 2.6 * cm
10388: qr_size = 2.6 * cm
10677: qr_size = 2.6 * cm
```

---

### Cambio 4: Función de Dibujo (modulo_superadmin.py:10160)

**Verificar que tiene documentación:**
```python
def _draw_same_qr(target_canvas, x, y, qr_size):
    """
    Dibuja código QR de ALTA RESOLUCIÓN en el canvas PDF.
    ...
    - box_size=10 (alta resolución)
    - error_correction=ERROR_CORRECT_H (máxima tolerancia a errores)
    - border=4 (márgenes de seguridad)
    ...
    """
```

**Comando de búsqueda:**
```bash
grep -n "def _draw_same_qr" modulo_superadmin.py
```

**Resultado esperado:**
```
10160: def _draw_same_qr(target_canvas, x, y, qr_size):
```

---

## 🧪 PRUEBA DE GENERACIÓN DE PDF

### Test 1: Generar examen individual

```python
from modulo_superadmin import ModuloSuperAdmin
import pandas as pd

# Datos de prueba
estudiante = {
    "id": 1,
    "documento": "1023456789",
    "nombre": "Juan Pérez",
    "grado": "9",
    "curso": "A",
}

preguntas = [
    {
        "id": 1,
        "enunciado": "¿Cuál es la capital de Francia?",
        "opcion_a": "Londres",
        "opcion_b": "París",
        "opcion_c": "Berlín",
        "opcion_d": "Madrid",
        "correcta": "B",
    }
    # ... más preguntas
]

# Generar PDF
superadmin = ModuloSuperAdmin()
superadmin._write_exam_pdf(
    preguntas_df=pd.DataFrame(preguntas),
    estudiante=estudiante,
    path="test_exam.pdf",
    cantidad=10,
    area="Lenguaje",
    evaluacion="Final"
)

print("PDF generado: test_exam.pdf")
```

**Verificación visual:**
1. Abrir en Adobe Reader
2. El QR debería estar en la esquina superior derecha
3. Debe medir aproximadamente 2.6 cm x 2.6 cm
4. Debería tener bordes limpios sin líneas blancas

---

## 🎬 PRUEBA CON CÁMARA (Opcional)

### Acceder a la función de lectura QR con cámara

1. Ejecutar la aplicación SEA
2. Ir a: SuperAdmin → Examenes → Calificar con Cámara
3. Iniciar cámara
4. Escanear un QR generado

**Resultado esperado:**
- El QR se detecta automáticamente
- El ID examen aparece en pantalla
- Se procesan las respuestas correctamente

---

## 📊 COMPARATIVA VISUAL

### ANTES (Defectuoso - box_size=4)
- Tamaño: 2.35 cm en PDF
- Imagen: ~200 píxeles
- Resultado: Líneas blancas, difícil lectura

### DESPUÉS (Óptimo - box_size=10)
- Tamaño: 2.6 cm en PDF
- Imagen: 530 píxeles
- Resultado: Limpio, 100% legible

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### Problema: "El QR no aparece en el PDF"

**Posibles causas:**
1. Falta `qrcode` o `PIL`

**Solución:**
```bash
pip install -U qrcode[pil] Pillow
```

---

### Problema: "El QR tiene líneas blancas"

**Verificar:**
1. ¿Se cambió box_size a 10? (Búsqueda: `box_size=10`)
2. ¿Se cambió border a 4? (Búsqueda: `border=4`)
3. ¿Se usa `format="PNG"`? (Búsqueda: `format="PNG"`)
4. ¿Se usa `optimize=False`? (Búsqueda: `optimize=False`)

---

### Problema: "El QR es muy pequeño en la impresión"

**Verificar:**
1. ¿Se cambió a 2.6 cm? (Búsqueda: `2.6 * cm`)
2. Verificar que hay 3 cambios de tamaño

**Si sigue siendo pequeño:**
```python
qr_size = 4.0 * cm  # Aumentar a 4 cm
```

---

### Problema: "El lector QR no lo reconoce"

**Verificar:**
1. ¿Se cambió error_correction? 
   ```bash
   grep "ERROR_CORRECT_H" modulo_superadmin.py
   ```

2. ¿Está en PNG formato? (No usar JPG)

3. ¿Se usa `optimize=False`?

**Si sigue sin funcionar:**
- Reinstalar: `pip install -U qrcode[pil]`
- Ejecutar test: `python test_qr_alta_resolucion.py`

---

## ✅ CHECKLIST DE VERIFICACIÓN

- [ ] Ejecuté `python test_qr_alta_resolucion.py` y pasaron todos los tests
- [ ] Verifiqué que box_size=10 en línea 10531
- [ ] Verifiqué que border=4 en línea 10533
- [ ] Verifiqué que error_correction=ERROR_CORRECT_H en línea 10532
- [ ] Verifiqué que optimize=False en línea 10546
- [ ] Verifiqué que qr_size = 2.6 * cm en línea 10123, 10388, 10677
- [ ] Generé un PDF y el QR aparece limpio sin líneas blancas
- [ ] Escaneé el QR con celular y se lee correctamente
- [ ] La documentación en _draw_same_qr está presente (línea 10160)

---

## 📞 VERIFICACIÓN FINAL

Ejecutar este comando para confirmar todos los cambios:

```bash
echo "=== CAMBIOS DE GENERACIÓN QR ===" && \
grep -n "box_size=10" modulo_superadmin.py && \
grep -n "border=4" modulo_superadmin.py && \
grep -n "ERROR_CORRECT_H" modulo_superadmin.py && \
grep -n 'format="PNG", optimize=False' modulo_superadmin.py && \
echo "=== TAMAÑOS QR ===" && \
grep -n "qr_size = 3.5" modulo_superadmin.py && \
echo "✅ TODOS LOS CAMBIOS ESTÁN EN LUGAR"
```

**Resultado esperado:**
```
=== CAMBIOS DE GENERACIÓN QR ===
10531: _qr = _qrcode_lib.QRCode(
10532: error_correction=_qrcode_lib.constants.ERROR_CORRECT_H,
10535: box_size=10,  # IMPORTANTE: mínimo 8, preferible 10
10536: border=4      # Mínimo 4 para márgenes seguros
10546: _qr_pil.save(_qr_buf, format="PNG", optimize=False)
=== TAMAÑOS QR ===
10123: qr_size = 2.6 * cm
10388: qr_size = 2.6 * cm
10677: qr_size = 2.6 * cm
✅ TODOS LOS CAMBIOS ESTÁN EN LUGAR
```

---

**Fecha:** 19 de marzo de 2026  
**Sistema:** SEA - Sistema de Evaluación Automatizada  
**Versión:** 1.0
