# CHECKLIST - HTTPS REAL CON CERTIFICADOS LOCALES

## Pre-requisitos Verificados
- [x] Python .venv con cryptography instalado
- [x] Certificados generados en `certs/` directorio
- [x] web_app.py actualizada con soporte a certificados reales
- [x] sea_launch.py compatible (sin cambios necesarios)

---

## Fase 1: Preparacion (Una sola vez)

### Generar Certificados

**OPCION A: Desde Terminal**
```powershell
cd c:\Users\rober\Documents\Proyecto_Evaluacion_V1
.\.venv\Scripts\python.exe generar_certificados.py 192.168.200.14
```

**OPCION B: Desde Python IDE/Notebook**
```python
import subprocess
subprocess.run([
    ".venv/Scripts/python.exe",
    "generar_certificados.py",
    "192.168.200.14"
])
```

**Resultado esperado:**
```
============================================================
  SEA -- Generador de Certificados SSL Locales
============================================================
  Directorio: C:\Users\rober\Documents\Proyecto_Evaluacion_V1\certs
  IP del servidor: 192.168.200.14
============================================================
[OK] CA local ya existe...
[*] Generando certificado del servidor...
[OK] Certificado generado...
============================================================
  [OK] Certificados listos para usar
============================================================
```

- [ ] Certificados generados sin errores
- [ ] `certs/` directorio tiene 4 archivos
- [ ] Cada archivo > 0 bytes

---

## Fase 2: Instalar en Dispositivos Moviles

### Android (Chrome/Firefox)

- [ ] Transfiere `certs/ca.pem` a Android
- [ ] Abre archivo en gestor de archivos
- [ ] Selecciona instalar como certificado CA
- [ ] Verifica en: Configuracion > Seguridad > Certificados de confianza

**Test:**
```
https://192.168.200.14:5000/escanear
→ Candado VERDE (SIN advertencia)
→ Camara solicita permiso
```

### iOS (Safari)

- [ ] Transfiere `certs/ca.pem` a iCloud Drive
- [ ] Descarga en Files
- [ ] iOS solicita instalar perfil
- [ ] Confirma instalacion

**Test:**
```
https://192.168.200.14:5000/escanear
→ Candado COMPLETO (SIN advertencia)
→ Camara solicita permiso
```

### Windows Desktop

**Chrome/Firefox/Edge:**
- [ ] Abre: https://localhost:5000
- [ ] Debe mostrar candado VERDE
- [ ] NO debe mostrar: "Tu conexion no es segura"

---

## Fase 3: Arrancar Servidor con Certificados

### Metodo 1: VS Code Task (Recomendado)
1. [ ] Abre proyecto en VS Code
2. [ ] Presiona **Ctrl + Shift + B** (ejecutar tarea por defecto)
3. [ ] O busca: Ctrl + Shift + P > "Servidor Web SEA -- HTTPS"
4. [ ] Terminal nueva mostrara logs

**Salida esperada:**
```
[INFO] Servidor web: https://localhost:5000
[INFO] Red local:    https://192.168.200.14:5000
[INFO] Escaner OMR:  https://192.168.200.14:5000/escanear
```

### Metodo 2: Terminal Manual
```powershell
cd c:\Users\rober\Documents\Proyecto_Evaluacion_V1
.\.venv\Scripts\python.exe sea_launch.py --web --port 5000
```

- [ ] Servidor arranca sin errores
- [ ] No menciona "adhoc"
- [ ] Menciona direcciones HTTPS

---

## Fase 4: Verificacion Funcional

### Desktop - https://localhost:5000
- [ ] Carga pagina principal
- [ ] Dashboard visible
- [ ] Candado VERDE
- [ ] Sin advertencias

### Desktop - https://192.168.200.14:5000/escanear
- [ ] Carga pagina escaner
- [ ] Botones visibles
- [ ] Candado VERDE
- [ ] Sin advertencias

### Movil - https://192.168.200.14:5000/escanear
- [ ] Carga correctamente
- [ ] Candado COMPLETO/VERDE
- [ ] Sin dialogo de advertencia de certificado
- [ ] Solicita permiso de camara
- [ ] Camara FUNCIONA

### API REST - https://192.168.200.14:5000/api/info
```powershell
$response = Invoke-WebRequest -Uri "https://192.168.200.14:5000/api/info" -SkipCertificateCheck
$response.StatusCode  # Debe ser 200
```

- [ ] API responde con estado 200
- [ ] JSON con informacion del servidor

---

## Fase 5: Troubleshooting

### Problema: "Su conexion no es segura" en navegador

**Diagnostico:**
- [ ] Certificados existen en `certs/`?
  ```powershell
  dir certs\
  ```
- [ ] Verifica que veas 4 archivos (ca.pem, ca_key.pem, server.pem, server_key.pem)

**Solucion A: Reinstalar certificados en movil**
1. Ve a Configuracion > Seguridad > Certificados de confianza
2. Busca "SEA Local CA"
3. Si no esta: Repite instalacion del ca.pem

**Solucion B: Regenerar certificados**
```powershell
# Elimina carpeta antigua
Remove-Item -Recurse -Force certs/

# Regenera
python generar_certificados.py 192.168.200.14

# Reinstala en movil
```

**Solucion C: Limpiar cache del navegador**
- Chrome: Ctrl + Shift + Del > Cookies y datos / imagenes almacenadas
- Firefox: Ctrl + Shift + Del > Cookies y datos sitio
- Safari: Menu > Historial > Limpiar historial

### Problema: Camara no funciona en movil

**Diagnostico:**
- [ ] Certificado CA esta instalado y confiable?
- [ ] Navegas via HTTPS (no HTTP)?
- [ ] Navegador permite acceso a camara?

**Solucion:**
1. Verifica URL: Debe ser `https://` NO `http://`
2. Ve a Configuracion > Apps > [Navegador]
3. Permisos > Camara > Permitir
4. Recarga pagina

### Problema: Python error "valor deseado IPv4Address"

**Razon:** Script intenta usar string IP directamente en `x509.IPAddress()`

**Solucion:** Ya fue corregido en generar_certificados.py actual.
Si aun ocurre: Elimina script antiguo y usa version actual.

---

## Fase 6: Duracion y Mantenimiento

### Validez de Certificados
- Certificado CA: 10 anos (valido hasta ~2036)
- Certificado Servidor: 1 ano (regenerar segun sea necesario)

### Si cambias tu IP:

```powershell
# 1. Obtener nueva IP
ipconfig | findstr "IPv4"

# 2. Elimina certificados viejos
Remove-Item -Recurse -Force certs/

# 3. Regenera con IP nueva
python generar_certificados.py [NUEVA_IP]

# 4. Reinstala ca.pem en todos los dispositivos
```

### Si cambias de maquina:
- [x] Los certificados actuales NO sirven en otra maquina
- [x] Crea certificados nuevos en la otra maquina

---

## Completitud

**Marca cuando se completen:**

- [ ] Fase 1: Certificados generados
- [ ] Fase 2: CA instalada en movil
- [ ] Fase 3: Servidor arranca con certificados
- [ ] Fase 4: Todas las URLs cargan sin advertencias
- [ ] Fase 5: Camara funciona en movil
- [ ] Fase 6: Confirmas duracion y mantenimiento

**Si todas las casillas estan marcadas:**

:arrow_right: **MIGRACION A HTTPS REAL COMPLETADA CON EXITO**

---

## Referencia Rapida

| Accion | Comando |
|--------|---------|
| Generar certs | `python generar_certificados.py 192.168.200.14` |
| Arrancar servidor | `python sea_launch.py --web` |
| Solo escaner | `https://192.168.200.14:5000/escanear` |
| Ver dashboard | `https://192.168.200.14:5000` |
| API info | `https://192.168.200.14:5000/api/info` |
| Limpiar cache | Usuario: Ctrl+Shift+Del en navegador |
| Mi IP | `ipconfig &#124; findstr "IPv4"` |

---

Completado: Marzo 21, 2026
Sistema: SEA (Sistema de Evaluacion Automatizada)
