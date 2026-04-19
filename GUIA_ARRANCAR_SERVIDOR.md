# Guia Rapida -- Arrancar el Servidor Web SEA

## HTTPS con Certificados Reales

## Opción 1: Tarea de VS Code (Recomendado)

1. En VS Code, presiona **`Ctrl + Shift + B`** (ejecutar tarea por defecto) o **`Ctrl + Shift + P`**
2. Busca y selecciona: **`Servidor Web SEA — HTTPS`**
3. El servidor arrancará en una nueva terminal panel

**Salida esperada:**
```
  SEA -- Sistema de Evaluacion Automatizada
  Arquitectura Hibrida: Escritorio + Web + API Movil
============================================================
  Servidor web:  https://localhost:5000
  Red local:     https://192.168.200.14:5000
  Escáner OMR:   https://192.168.200.14:5000/escanear
  API REST:      https://192.168.200.14:5000/api/info

Los certificados estan firmados por una Autoridad Certificadora local.
Si el navegador muestra advertencia, es normal en la primera conexion.
```

---

## Opción 2: Terminal Manual

Desde PowerShell en la carpeta del proyecto:

```powershell
.\.venv\Scripts\python.exe sea_launch.py --web
```

---

## Acceso desde el Navegador

**Escritorio/laptop:**
```
https://localhost:5000
```

**Movil (misma red):**
```
https://192.168.200.14:5000/escanear
```

> Nota: Reemplaza `192.168.200.14` con la IP real de tu equipo si es diferente.

### Encontrar tu IP real

En PowerShell:
```powershell
ipconfig | findstr "IPv4"
```

---

## Verificación rápida

1. ✅ Abre `https://192.168.200.14:5000/escanear` en el móvil
2. ✅ Acepta la advertencia del certificado local
3. ✅ Permite acceso a la cámara
4. ✅ Presiona "Iniciar escaneo automático"
5. ✅ Deberías ver la línea de escaneo animada

---

## Detener el Servidor

- **Presiona `Ctrl + C`** en la terminal donde corre el servidor

---

## Troubleshooting

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Ejecuta con `.venv\Scripts\python.exe` (no `venv\Scripts`) |
| Certificado no aceptado | Es un certificado local autofirmado — es seguro aceptarlo |
| Cámara no funciona en móvil | Verifica que accedas por `HTTPS` (no HTTP) |
| IP incorrecta | Ejecuta `ipconfig` en tu PC para obtener la IP real |

---

## Configuración Técnica

- **Puerto:** 5000
- **Host:** 0.0.0.0 (escucha en todos los adaptadores)
- **SSL:** HTTPS con certificados locales en `certs/` cuando existen; si no, fallback `adhoc`
- **Entorno:** Python .venv (.venv\Scripts\python.exe)
- **Lanzador:** sea_launch.py --web
