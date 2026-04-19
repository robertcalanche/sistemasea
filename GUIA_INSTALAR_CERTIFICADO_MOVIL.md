# Instalacion de Certificado CA en Dispositivos Moviles

## Requisito Previo

Los certificados se encuentran en: `certs/ca.pem` (Autoridad Certificadora)

---

## Android (Recomendado)

### Paso 1: Transferir Certificado

```powershell
# Desde PowerShell, copiar el archivo ca.pem a la nube o dispositivo:
# - Google Drive
# - Carpeta sincronizada
# - Via cable USB
# - Via correo (como adjunto)
```

### Paso 2: Instalar en Android

1. Abre el Administrador de archivos en Android
2. Busca el archivo `ca.pem` (tal como se descargo)
3. Toca el archivo → El sistema pregunta donde instalarlo
4. Selecciona: **Guardar en... > Seguridad > Instalar certificado**
5. Aparecera instalar como certificado CA
6. Pon nombre: "SEA Local CA"
7. Toca **OK**

Resultado esperado:
- Configuracion > Seguridad > Certificados de confianza
- Veras "SEA Local CA" en la lista

---

## iOS (iPhone/iPad)

### Paso 1: Transferir Certificado

Usa AirDrop o copia el archivo `ca.pem` a iCloud Drive

### Paso 2: Instalar en iOS

1. Abre Files (Archivos) en iOS
2. Descarga el archivo `ca.pem`
3. El sistema iOS abre "Mostrar perfil"
4. Selecciona: **Instalar**
5. Confirma la instalacion

Resultado esperado:
- Configuracion > General > Acerca de > Configuracion de confianza de cert.
- Veras "SEA Local CA" habilitado

---

## Windows (Desktop/Laptop)

### Opcion 1: Instalar via Sistema (Recomendado)

```powershell
# Abre PowerShell as Administrator

# 1. Busca la ubicacion del certificado
$certPath = "C:\Users\[usuario]\Documents\Proyecto_Evaluacion_V1\certs\ca.pem"

# 2. Importa el certificado (requiere conversion a CER)
certutil -encode $certPath ca.cer

# 3. Instala el archivo CER generado
Start-Process mmc.exe

# En MMC:
#   File > Add/Remove Snap-in > Certificates > Local Computer
#   Trusted Root Certification Authorities > Certificates > Derecha > All Tasks > Import
#   Selecciona ca.cer
```

### Opcion 2: Instalar via Navegador (Firefox)

Firefox tiene su propio almacen de certificados separado del sistema:

1. Abre Firefox
2. Opciones > Privacidad y Seguridad > Certificados
3. Ver Certificados > Pestaña Autoridades
4. Importar > Selecciona ca.pem
5. Marca: "Confiar en esta CA para identificar sitios web"

---

## Mac (macOS)

### Paso 1: Transferir Certificado

Copia `ca.pem` al Mac via Airdrop o correo

### Paso 2: Instalar en macOS

```bash
# 1. Abre Llavero (Keychain Access)
open /Applications/Utilities/Keychain\ Access.app

# 2. Arrastra el archivo ca.pem al Llavero
#    O: Archivo > Importar Elementos > ca.pem

# 3. Busca "SEA Local CA" en el Llavero
# 4. Haz doble clic > expandir seccion "Confiar"
# 5. Establece "Al conectar a este sitio" en "Siempre confiar"
```

---

## Verificacion - Despues de Instalar

### Test en Android:

```
1. Abre el navegador Chrome/Firefox en Android
2. Navega a: https://192.168.200.14:5000
3. Esperado: SIN advertencia de certificado (candado verde)
4. La camara debe funcionar sin errores
```

### Test en iOS:

```
1. Abre Safari en iOS
2. Navega a: https://192.168.200.14:5000/escanear
3. Esperado: SIN advertencia (candado completo)
4. La camara debe funcionar
```

### Test en Desktop:

```
1. Abre navegador (Chrome, Firefox, Edge)
2. Navega a: https://localhost:5000
3. Esperado: SIN advertencia (candado)
4. Todos los servicios accesibles
```

---

## Resolucion de Problemas

### Error: "Certificado no valido" o "Conexion no segura"

Posible causa: El certificado NO fue instalado correctamente.

Solucion:
1. Repite los pasos de instalacion
2. Verifica que el archivo ca.pem sea accesible
3. Reinicia el navegador y el servidor

### Error: "El certificado no coincide con el dominio"

Posible causa: Estas accediendo con una IP diferente.

Solucion:
1. Verifica tu IP actual: `ipconfig | findstr "IPv4"`
2. Actualiza los accesos a esa IP
3. Si cambio la IP, regenera certificados: `python generar_certificados.py [NUEVA_IP]`

### Android: Certificado descargado pero no se ve en archivos

Posible causa: Se instalo automaticamente sin mostrar pantalla.

Solucion:
1. Ve a Configuracion > Seguridad > Certificados de confianza
2. Verifica que veas "SEA Local CA"

---

## Regeneracion de Certificados (Si es Necesario)

Si cambio tu IP local o necesitas certificados nuevos:

```powershell
# 1. Ejecuta el generador con la IP actual
python generar_certificados.py 192.168.XXX.XXX

# 2. Espera a que complete
# 3. Reinstala ca.pem en los dispositivos
# 4. Reinicia el servidor
```

---

## Duracion de Certificados

- **CA**: 10 anos (valido hasta 2036)
- **Servidor**: 1 ano (se regenera automaticamente si necesarias)

No requieren renovacion a menos que cambies IP o cambies de maquina.
