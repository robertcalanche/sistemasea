# GUIA - DOMINIO LOCAL PARA SEA

## Objetivo

Permitir acceso local amigable en Windows usando dominios como:

- sea.local
- evaluaciones.local
- admin.local

## Configuracion del archivo hosts

Abre PowerShell como Administrador y ejecuta:

```powershell
Set-Location "C:\Users\rober\Documents\Proyecto_Evaluacion_V1"
.\configurar_dominios_locales.ps1
```

Esto agrega entradas como:

```text
127.0.0.1 sea.local
127.0.0.1 evaluaciones.local
127.0.0.1 admin.local
```

Archivo modificado:

- C:\Windows\System32\drivers\etc\hosts

## Arranque recomendado

En VS Code usa la tarea:

- Servidor Web SEA — HTTP Local

O desde PowerShell:

```powershell
Set-Location "C:\Users\rober\Documents\Proyecto_Evaluacion_V1"
& ".\.venv\Scripts\python.exe" ".\sea_launch.py" --web
```

## URLs esperadas

- Acceso local: http://sea.local:5000
- Alias local: http://evaluaciones.local:5000
- Red local: http://IP_LOCAL:5000
- Escaner OMR: http://IP_LOCAL:5000/escanear
- API: http://IP_LOCAL:5000/api/info

## Celular en la misma red

Los dominios .local configurados en hosts solo resuelven en el PC donde se agregaron.

Para celular:

- usa la IP local mostrada en consola
- ejemplo: http://192.168.1.5:5000

## Nota sobre camara OMR

Muchos navegadores moviles permiten abrir el sitio por HTTP en red local, pero algunos bloquean getUserMedia fuera de un contexto seguro.

Si la camara no abre en el movil:

1. usa la tarea Servidor Web SEA — HTTPS
2. o instala certificados validos para desarrollo

## Puerto 80

Es viable, pero no se recomienda como predeterminado en desarrollo porque:

- requiere permisos elevados
- puede entrar en conflicto con IIS u otros servicios
- dificulta el flujo normal de desarrollo

Por eso SEA conserva el puerto 5000 como puerto local por defecto.

## Futuro Azure

La transicion a dominio real queda preparada manteniendo:

- host Flask en 0.0.0.0
- deteccion automatica de IP local
- posibilidad de habilitar HTTPS por variable de entorno
- separacion entre acceso local y acceso por red