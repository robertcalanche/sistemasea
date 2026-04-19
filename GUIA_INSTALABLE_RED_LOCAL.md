# Guia de instalable en red local (sin internet)

Esta guia deja el sistema como programa instalable para trabajar en red local.
No requiere internet durante la operacion diaria.
El despliegue usa solo la base de datos SQLite `sistema.db`; los archivos Excel no forman parte del instalable.

## 1) Requisitos

- Windows en servidor y clientes.
- Red local con conectividad entre equipos.
- Permisos para crear carpeta compartida SMB en el servidor.
- Python solo en la maquina de compilacion (no en clientes).

## 2) Compilar el paquete instalable

En la raiz del proyecto, ejecutar:

```powershell
.\build_instalable_red_local.ps1
```

Resultado generado en:

- `dist_red_local/Paquete_Cliente`
- `dist_red_local/Paquete_Servidor`
- `dist_red_local/Herramientas`
- `dist_red_local/Paquete_Cliente.zip`
- `dist_red_local/Paquete_Servidor.zip`
- `dist_red_local/Herramientas.zip`

## 3) Preparar servidor web y datos

### Opcion automatica (recomendada)

Ejecuta en el servidor (PowerShell como Administrador):

```powershell
.\preparar_servidor_red_local.ps1
```

Por defecto crea:

- Carpeta local: `D:\SistemaEvaluacion`
- Ejecutable web: `D:\SistemaEvaluacion\sea_web.exe`
- Recurso compartido SMB: `\\NOMBRE_SERVIDOR\SistemaEvaluacion`
- Ruta UNC para clientes: `\\NOMBRE_SERVIDOR\SistemaEvaluacion\DatosCompartidos`

### Opcion manual

1. Crear carpeta local del servidor: `D:\SistemaEvaluacion`
2. Copiar completo el contenido de `dist_red_local/Paquete_Servidor` a `D:\SistemaEvaluacion`.
3. Compartir `D:\SistemaEvaluacion` por SMB con nombre `SistemaEvaluacion`.
4. Verificar desde otro equipo acceso a:

```text
\\NOMBRE_SERVIDOR\SistemaEvaluacion\DatosCompartidos
```

5. Iniciar el servidor web con:

```text
D:\SistemaEvaluacion\Iniciar_Servidor_Web_SEA.cmd
```

6. Abrir la URL que muestre la consola del servidor desde otro equipo de la LAN.

## 4) Instalar cliente en cada PC

En cada cliente, copiar `Paquete_Cliente` y ejecutar:

```powershell
.\instalar_cliente_red_local.ps1 -Fuente "C:\Ruta\Paquete_Cliente" -Destino "C:\SistemaEvaluacion" -RutaCompartida "\\NOMBRE_SERVIDOR\SistemaEvaluacion\DatosCompartidos"
```

El instalador ahora valida automaticamente:

- Que la ruta UNC exista y sea accesible.
- Que exista `sistema.db` en la carpeta compartida.

El paquete generado ya no distribuye `preguntas.xlsx` ni `estudiantes.xlsx`.
Las funciones de Excel quedan disponibles solo dentro de la aplicacion cuando el usuario importa o exporta manualmente desde sus botones.

Si estas inicializando desde cero y aun no existe `sistema.db`, puedes permitirlo con:

```powershell
.\instalar_cliente_red_local.ps1 -Fuente "C:\Ruta\Paquete_Cliente" -Destino "C:\SistemaEvaluacion" -RutaCompartida "\\NOMBRE_SERVIDOR\SistemaEvaluacion\DatosCompartidos" -PermitirBDNueva
```

Esto hace automaticamente:

- Copia del ejecutable y dependencias.
- Escritura de `config_sistema` en modo red.
- Creacion de acceso directo en el escritorio.

## 5) Prueba funcional

1. Inicia `Iniciar_Servidor_Web_SEA.cmd` en el servidor.
2. Abre la app web desde otro equipo de la LAN.
3. Valida login y carga de datos.
4. Ejecuta una accion de escritura.
5. Abre otro cliente y valida que vea la misma informacion.

## 6) Operacion sin internet

- El sistema usa archivos locales + recurso SMB.
- La app web del servidor usa `sea_web.exe` y la base compartida en `DatosCompartidos\sistema.db`.
- No consume APIs web ni servicios cloud.
- Si la LAN esta activa, el sistema funciona aunque no haya internet.
- En `modo=red`, la app valida la conectividad al recurso SMB al iniciar y muestra error claro si no hay acceso.

## 7) Mantenimiento recomendado

- Respaldo diario de `sistema.db` en el servidor.
- No editar `sistema.db` manualmente mientras haya clientes abiertos.
- Evitar apagar el servidor durante examenes en curso.
- Si necesitas cargar estudiantes o preguntas desde Excel, hazlo desde los botones de importacion de la aplicacion, no copiando archivos `.xlsx` al servidor.

## 8) Comandos utiles

Si PowerShell bloquea scripts (`PSSecurityException`), usa una de estas opciones:

```powershell
# Solo para la sesion actual (recomendado)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

```powershell
# Persistente para tu usuario
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

Tambien puedes ejecutar cualquier script sin cambiar politica global:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_instalable_red_local.ps1
```

Recompilar sin volver a construir exe (reusar dist existente):

```powershell
.\build_instalable_red_local.ps1 -SkipBuild
```

Preparar servidor en ruta personalizada:

```powershell
.\preparar_servidor_red_local.ps1 -RutaServidor "E:\Evaluacion" -NombreCompartido "Evaluacion"
```
