param(
    [string]$RutaServidor = "D:\SistemaEvaluacion",
    [string]$NombreCompartido = "SistemaEvaluacion",
    [string]$SemillaServidor = (Join-Path $PSScriptRoot "dist_red_local\Paquete_Servidor")
)

$ErrorActionPreference = "Stop"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        throw "Este script requiere PowerShell ejecutado como Administrador para crear/gestionar recursos SMB."
    }
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

Assert-Administrator

$datosDestino = Join-Path $RutaServidor "DatosCompartidos"

Write-Step "Creando estructura en servidor"
if (-not (Test-Path -LiteralPath $RutaServidor)) {
    New-Item -ItemType Directory -Path $RutaServidor | Out-Null
}
if (-not (Test-Path -LiteralPath $datosDestino)) {
    New-Item -ItemType Directory -Path $datosDestino | Out-Null
}

if (Test-Path -LiteralPath $SemillaServidor) {
    Write-Step "Copiando archivos del paquete servidor"
    Get-ChildItem -LiteralPath $SemillaServidor | ForEach-Object {
        if ($_.PSIsContainer -and $_.Name -eq "DatosCompartidos") {
            Get-ChildItem -LiteralPath $_.FullName | ForEach-Object {
                $destino = Join-Path $datosDestino $_.Name
                if ($_.Name -ieq "sistema.db" -and (Test-Path -LiteralPath $destino)) {
                    Write-Host "Se conserva la base de datos existente en el servidor." -ForegroundColor Yellow
                }
                else {
                    Copy-Item -LiteralPath $_.FullName -Destination $destino -Recurse -Force
                }
            }
        }
        else {
            Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $RutaServidor $_.Name) -Recurse -Force
        }
    }
}
else {
    Write-Host "No se encontro paquete servidor en: $SemillaServidor" -ForegroundColor Yellow
    Write-Host "Continuando sin copiar datos iniciales." -ForegroundColor Yellow
}

$dbDestino = Join-Path $datosDestino "sistema.db"
if (-not (Test-Path -LiteralPath $dbDestino)) {
    Write-Step "Creando sistema.db vacio en servidor"
    New-Item -ItemType File -Path $dbDestino -Force | Out-Null
}

Write-Step "Publicando recurso compartido SMB"
$existing = Get-SmbShare -Name $NombreCompartido -ErrorAction SilentlyContinue
if (-not $existing) {
    New-SmbShare -Name $NombreCompartido -Path $RutaServidor -FullAccess "Everyone" | Out-Null
}
else {
    if ($existing.Path -ne $RutaServidor) {
        throw "Ya existe un recurso compartido '$NombreCompartido' en otra ruta: $($existing.Path). Usa otro nombre o corrige -NombreCompartido."
    }
    Write-Host "El recurso compartido ya existe y apunta a la ruta esperada: $NombreCompartido" -ForegroundColor Yellow
}

$serverName = $env:COMPUTERNAME
$uncDataPath = "\\$serverName\$NombreCompartido\DatosCompartidos"

Write-Step "Servidor preparado"
Write-Host "Ruta local: $datosDestino" -ForegroundColor Green
Write-Host "Ruta UNC para clientes: $uncDataPath" -ForegroundColor Green
Write-Host "Lanzador web: $(Join-Path $RutaServidor 'Iniciar_Servidor_Web_SEA.cmd')" -ForegroundColor Green
Write-Host "Usa esa ruta en instalar_cliente_red_local.ps1" -ForegroundColor Green
