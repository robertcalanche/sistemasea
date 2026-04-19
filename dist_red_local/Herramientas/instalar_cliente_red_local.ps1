param(
    [string]$Fuente,
    [string]$Destino = "C:\SistemaEvaluacion",
    [string]$RutaCompartida,
    [switch]$PermitirBDNueva
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function New-DesktopShortcut {
    param(
        [string]$TargetPath,
        [string]$ShortcutPath,
        [string]$WorkingDir
    )

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $TargetPath
    $shortcut.WorkingDirectory = $WorkingDir
    $shortcut.IconLocation = "$TargetPath,0"
    $shortcut.Save()
}

function Resolve-SharedDatabasePath {
    param([string]$RutaCompartidaInput)

    $ruta = $RutaCompartidaInput.Trim()
    if ($ruta.ToLower().EndsWith(".db")) {
        return $ruta
    }
    return (Join-Path $ruta "sistema.db")
}

if (-not $Fuente) {
    $Fuente = Join-Path $PSScriptRoot "Paquete_Cliente"
}

if (-not (Test-Path -LiteralPath $Fuente)) {
    throw "No se encontro la carpeta origen: $Fuente"
}

if (-not $RutaCompartida) {
    $RutaCompartida = Read-Host "Ingresa la ruta UNC compartida (ej: \\SERVIDOR\SistemaEvaluacion\DatosCompartidos)"
}

$RutaCompartida = $RutaCompartida.Trim()
if ([string]::IsNullOrWhiteSpace($RutaCompartida)) {
    throw "La ruta compartida no puede estar vacia."
}
if (-not $RutaCompartida.StartsWith("\\")) {
    throw "La ruta compartida debe ser UNC y comenzar con \\"
}
if (-not (Test-Path -LiteralPath $RutaCompartida)) {
    throw "No se puede acceder a la ruta compartida: $RutaCompartida"
}

$rutaDbCompartida = Resolve-SharedDatabasePath -RutaCompartidaInput $RutaCompartida
if (-not (Test-Path -LiteralPath $rutaDbCompartida)) {
    if ($PermitirBDNueva) {
        Write-Host "No se encontro sistema.db en la ruta compartida. Se continuara por parametro -PermitirBDNueva." -ForegroundColor Yellow
    }
    else {
        throw "No se encontro sistema.db en: $rutaDbCompartida. Ejecuta preparar_servidor_red_local.ps1 en el servidor o usa -PermitirBDNueva."
    }
}

Write-Step "Creando carpeta destino"
if (-not (Test-Path -LiteralPath $Destino)) {
    New-Item -ItemType Directory -Path $Destino | Out-Null
}

Write-Step "Copiando archivos del cliente"
Copy-Item -Path (Join-Path $Fuente "*") -Destination $Destino -Recurse -Force

Write-Step "Escribiendo config_sistema en modo red"
$configPath = Join-Path $Destino "config_sistema"
$configContent = @"
# Configuracion de despliegue del sistema de evaluacion
# modo: local | red
modo=red

# Ruta UNC de carpeta compartida o ruta UNC directa al archivo sistema.db
ruta_servidor=$RutaCompartida
"@
Set-Content -LiteralPath $configPath -Value $configContent -Encoding UTF8

Write-Step "Creando lanzador local"
$launcherPath = Join-Path $Destino "Iniciar_Sistema_Evaluacion.cmd"
$launcherContent = @"
@echo off
setlocal
cd /d "%~dp0"
start "" "app.exe"
endlocal
"@
Set-Content -LiteralPath $launcherPath -Value $launcherContent -Encoding Ascii

$exePath = Join-Path $Destino "app.exe"
if (-not (Test-Path -LiteralPath $exePath)) {
    throw "No se encontro app.exe en $Destino"
}

Write-Step "Creando acceso directo en escritorio"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcut = Join-Path $desktop "Sistema Evaluacion.lnk"
New-DesktopShortcut -TargetPath $exePath -ShortcutPath $shortcut -WorkingDir $Destino

Write-Step "Instalacion finalizada"
Write-Host "Aplicacion instalada en: $Destino" -ForegroundColor Green
Write-Host "Ruta compartida configurada: $RutaCompartida" -ForegroundColor Green
Write-Host "Base de datos compartida: $rutaDbCompartida" -ForegroundColor Green
Write-Host "Acceso directo: $shortcut" -ForegroundColor Green
