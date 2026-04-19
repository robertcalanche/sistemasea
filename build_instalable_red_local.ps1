param(
    [string]$ProjectRoot = $PSScriptRoot,
    [string]$OutputRoot = (Join-Path $PSScriptRoot "dist_red_local"),
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function New-DirectoryIfMissing {
    param([string]$PathToCreate)
    if (-not (Test-Path -LiteralPath $PathToCreate)) {
        New-Item -ItemType Directory -Path $PathToCreate | Out-Null
    }
}

function New-DatabaseSeedFile {
    param(
        [string]$ProjectRootPath,
        [string]$DatabaseDestination
    )

    $sourceDb = Join-Path $ProjectRootPath "sistema.db"
    if (Test-Path -LiteralPath $sourceDb) {
        Copy-Item -LiteralPath $sourceDb -Destination $DatabaseDestination -Force
        return
    }

    New-Item -ItemType File -Path $DatabaseDestination -Force | Out-Null
}

function Compress-WithRetry {
    param(
        [string]$SourceDir,
        [string]$DestinationZip,
        [int]$MaxAttempts = 3
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            if (Test-Path -LiteralPath $DestinationZip) {
                Remove-Item -LiteralPath $DestinationZip -Force
            }

            Compress-Archive -Path (Join-Path $SourceDir "*") -DestinationPath $DestinationZip -Force -ErrorAction Stop
            return
        }
        catch {
            if ($attempt -eq $MaxAttempts) {
                throw
            }
            Start-Sleep -Seconds 2
        }
    }
}

Write-Step "Verificando estructura del proyecto"
$specPath = Join-Path $ProjectRoot "app.spec"
if (-not (Test-Path -LiteralPath $specPath)) {
    throw "No se encontro app.spec en $ProjectRoot"
}
$webSpecPath = Join-Path $ProjectRoot "web_server.spec"
if (-not (Test-Path -LiteralPath $webSpecPath)) {
    throw "No se encontro web_server.spec en $ProjectRoot"
}

if (-not $SkipBuild) {
    Write-Step "Verificando PyInstaller"
    $pyi = Get-Command pyinstaller -ErrorAction SilentlyContinue
    $venvCandidates = @(
        (Join-Path $ProjectRoot ".venv\Scripts\python.exe"),
        (Join-Path $ProjectRoot "venv\Scripts\python.exe")
    )
    $venvPython = $null
    foreach ($candidate in $venvCandidates) {
        if (Test-Path -LiteralPath $candidate) {
            $venvPython = $candidate
            break
        }
    }
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pyi -and -not $venvPython -and -not $pyLauncher) {
        throw "PyInstaller no esta disponible. Instala con: pip install pyinstaller"
    }

    Write-Step "Instalando dependencias de Python (requirements.txt)"
    $requirementsPath = Join-Path $ProjectRoot "requirements.txt"
    if (Test-Path -LiteralPath $requirementsPath) {
        $prevPreference2 = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        if ($venvPython) {
            & $venvPython -m pip install -r $requirementsPath --quiet 2>&1 | ForEach-Object { Write-Host $_ }
        }
        elseif ($pyi) {
            & python -m pip install -r $requirementsPath --quiet 2>&1 | ForEach-Object { Write-Host $_ }
        }
        else {
            & py -m pip install -r $requirementsPath --quiet 2>&1 | ForEach-Object { Write-Host $_ }
        }
        $ErrorActionPreference = $prevPreference2
    }
    else {
        Write-Host "requirements.txt no encontrado, se omite instalacion de dependencias." -ForegroundColor Yellow
    }

    Write-Step "Compilando ejecutable con app.spec"
    Push-Location $ProjectRoot
    try {
        foreach ($legacyOutput in @(
            (Join-Path $ProjectRoot "dist\preguntas.xlsx"),
            (Join-Path $ProjectRoot "dist\estudiantes.xlsx")
        )) {
            if (Test-Path -LiteralPath $legacyOutput) {
                Remove-Item -LiteralPath $legacyOutput -Force
            }
        }

        if (Test-Path -LiteralPath (Join-Path $ProjectRoot "dist\app")) {
            Remove-Item -LiteralPath (Join-Path $ProjectRoot "dist\app") -Recurse -Force
        }
        if (Test-Path -LiteralPath (Join-Path $ProjectRoot "dist\app.exe")) {
            Remove-Item -LiteralPath (Join-Path $ProjectRoot "dist\app.exe") -Force
        }
        if (Test-Path -LiteralPath (Join-Path $ProjectRoot "dist\sea_web")) {
            Remove-Item -LiteralPath (Join-Path $ProjectRoot "dist\sea_web") -Recurse -Force
        }
        if (Test-Path -LiteralPath (Join-Path $ProjectRoot "dist\sea_web.exe")) {
            Remove-Item -LiteralPath (Join-Path $ProjectRoot "dist\sea_web.exe") -Force
        }

        $prevPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        if ($venvPython) {
            & $venvPython -m PyInstaller --noconfirm --clean $specPath 2>&1 | ForEach-Object { Write-Host $_ }
            if ($LASTEXITCODE -eq 0) {
                & $venvPython -m PyInstaller --noconfirm --clean $webSpecPath 2>&1 | ForEach-Object { Write-Host $_ }
            }
        }
        elseif ($pyi) {
            & pyinstaller --noconfirm --clean $specPath 2>&1 | ForEach-Object { Write-Host $_ }
            if ($LASTEXITCODE -eq 0) {
                & pyinstaller --noconfirm --clean $webSpecPath 2>&1 | ForEach-Object { Write-Host $_ }
            }
        }
        else {
            & py -m PyInstaller --noconfirm --clean $specPath 2>&1 | ForEach-Object { Write-Host $_ }
            if ($LASTEXITCODE -eq 0) {
                & py -m PyInstaller --noconfirm --clean $webSpecPath 2>&1 | ForEach-Object { Write-Host $_ }
            }
        }
        $ErrorActionPreference = $prevPreference
        if ($LASTEXITCODE -ne 0) {
            throw "PyInstaller termino con codigo $LASTEXITCODE"
        }
    }
    finally {
        $ErrorActionPreference = "Stop"
        Pop-Location
    }
}

$distAppDir = Join-Path $ProjectRoot "dist\app"
$distAppExe = Join-Path $ProjectRoot "dist\app.exe"
if (-not (Test-Path -LiteralPath $distAppDir) -and -not (Test-Path -LiteralPath $distAppExe)) {
    throw "No existe salida en dist\\app ni dist\\app.exe. Ejecuta sin -SkipBuild o revisa app.spec"
}

$distWebDir = Join-Path $ProjectRoot "dist\sea_web"
$distWebExe = Join-Path $ProjectRoot "dist\sea_web.exe"
if (-not (Test-Path -LiteralPath $distWebDir) -and -not (Test-Path -LiteralPath $distWebExe)) {
    throw "No existe salida en dist\\sea_web ni dist\\sea_web.exe. Ejecuta sin -SkipBuild o revisa web_server.spec"
}

Write-Step "Preparando carpeta de salida"
if (Test-Path -LiteralPath $OutputRoot) {
    Remove-Item -LiteralPath $OutputRoot -Recurse -Force
}

$clienteDir = Join-Path $OutputRoot "Paquete_Cliente"
$servidorDir = Join-Path $OutputRoot "Paquete_Servidor"
$datosCompartidos = Join-Path $servidorDir "DatosCompartidos"
$herramientasDir = Join-Path $OutputRoot "Herramientas"

New-DirectoryIfMissing -PathToCreate $clienteDir
New-DirectoryIfMissing -PathToCreate $servidorDir
New-DirectoryIfMissing -PathToCreate $datosCompartidos
New-DirectoryIfMissing -PathToCreate $herramientasDir

Write-Step "Copiando ejecutable del cliente"
if (Test-Path -LiteralPath $distAppDir) {
    Copy-Item -Path (Join-Path $distAppDir "*") -Destination $clienteDir -Recurse -Force
}
else {
    Copy-Item -LiteralPath $distAppExe -Destination $clienteDir -Force
}

Write-Step "Incluyendo instalador y lanzador en paquete cliente"
$installerScriptSource = Join-Path $ProjectRoot "instalar_cliente_red_local.ps1"
if (Test-Path -LiteralPath $installerScriptSource) {
    Copy-Item -LiteralPath $installerScriptSource -Destination $clienteDir -Force
}

$launcherPath = Join-Path $clienteDir "Iniciar_Sistema_Evaluacion.cmd"
$launcherContent = @"
@echo off
setlocal
cd /d "%~dp0"
start "" "app.exe"
endlocal
"@
Set-Content -LiteralPath $launcherPath -Value $launcherContent -Encoding Ascii

Write-Step "Generando config_sistema de cliente en modo red"
$clienteConfigPath = Join-Path $clienteDir "config_sistema"
$clienteConfigContent = @"
# Configuracion de despliegue del sistema de evaluacion
# modo: local | red
modo=red

# Ruta UNC de la carpeta compartida del servidor o ruta UNC directa a sistema.db
# Ejemplo carpeta: \\SERVIDOR_EVALUACION\SistemaEvaluacion\DatosCompartidos
# Ejemplo archivo: \\SERVIDOR_EVALUACION\SistemaEvaluacion\DatosCompartidos\sistema.db
ruta_servidor=\\SERVIDOR_EVALUACION\SistemaEvaluacion\DatosCompartidos
"@
Set-Content -LiteralPath $clienteConfigPath -Value $clienteConfigContent -Encoding UTF8

Write-Step "Copiando base de datos y recursos del servidor"
New-DatabaseSeedFile -ProjectRootPath $ProjectRoot -DatabaseDestination (Join-Path $datosCompartidos "sistema.db")

$imagenesSource = Join-Path $ProjectRoot "imagenes_preguntas"
if (Test-Path -LiteralPath $imagenesSource) {
    Copy-Item -LiteralPath $imagenesSource -Destination $datosCompartidos -Recurse -Force
}

Write-Step "Copiando servidor web al paquete servidor"
if (Test-Path -LiteralPath $distWebDir) {
    Copy-Item -Path (Join-Path $distWebDir "*") -Destination $servidorDir -Recurse -Force
}
else {
    Copy-Item -LiteralPath $distWebExe -Destination $servidorDir -Force
}

$serverConfigPath = Join-Path $servidorDir "config_sistema"
$serverConfigContent = @"
# Configuracion del servidor web en red local
modo=red
ruta_servidor=DatosCompartidos
"@
Set-Content -LiteralPath $serverConfigPath -Value $serverConfigContent -Encoding UTF8

$serverLauncherPath = Join-Path $servidorDir "Iniciar_Servidor_Web_SEA.cmd"
$serverLauncherContent = @"
@echo off
setlocal
cd /d "%~dp0"
start "" "sea_web.exe"
endlocal
"@
Set-Content -LiteralPath $serverLauncherPath -Value $serverLauncherContent -Encoding Ascii

$serverReadmePath = Join-Path $servidorDir "LEEME_SERVIDOR.txt"
$serverReadme = @"
PASOS RAPIDOS SERVIDOR

1) Mueve todo el contenido de Paquete_Servidor a una ruta estable, por ejemplo:
   D:\SistemaEvaluacion

2) Dentro de esa ruta debe existir la carpeta DatosCompartidos y el ejecutable sea_web.exe.

3) Comparte D:\SistemaEvaluacion con nombre de recurso compartido SistemaEvaluacion.

4) Verifica acceso desde otro equipo con la ruta UNC:
   \\NOMBRE_SERVIDOR\SistemaEvaluacion\DatosCompartidos

5) Dentro de DatosCompartidos debe existir sistema.db.
    Si no tenias una base previa, este paquete ya incluye una vacia lista para inicializarse.

6) Inicia el servidor web con Iniciar_Servidor_Web_SEA.cmd.

7) En cada cliente, configura config_sistema en modo red con esa ruta UNC.
"@
Set-Content -LiteralPath $serverReadmePath -Value $serverReadme -Encoding UTF8

Write-Step "Copiando scripts y guia"
$supportFiles = @(
    "instalar_cliente_red_local.ps1",
    "preparar_servidor_red_local.ps1",
    "GUIA_INSTALABLE_RED_LOCAL.md"
)
foreach ($fileName in $supportFiles) {
    $source = Join-Path $ProjectRoot $fileName
    if (Test-Path -LiteralPath $source) {
        Copy-Item -LiteralPath $source -Destination $herramientasDir -Force
    }
}

Write-Step "Generando ZIP de distribucion"
$zipCliente = Join-Path $OutputRoot "Paquete_Cliente.zip"
$zipServidor = Join-Path $OutputRoot "Paquete_Servidor.zip"
$zipHerramientas = Join-Path $OutputRoot "Herramientas.zip"

Compress-WithRetry -SourceDir $clienteDir -DestinationZip $zipCliente
Compress-WithRetry -SourceDir $servidorDir -DestinationZip $zipServidor
Compress-WithRetry -SourceDir $herramientasDir -DestinationZip $zipHerramientas

Write-Step "Empaquetado completado"
Write-Host "Salida: $OutputRoot" -ForegroundColor Green
Write-Host "- Cliente:   $clienteDir" -ForegroundColor Green
Write-Host "- Servidor:  $servidorDir" -ForegroundColor Green
Write-Host "- Scripts:   $herramientasDir" -ForegroundColor Green
Write-Host "- ZIP Cliente:      $zipCliente" -ForegroundColor Green
Write-Host "- ZIP Servidor:     $zipServidor" -ForegroundColor Green
Write-Host "- ZIP Herramientas: $zipHerramientas" -ForegroundColor Green
