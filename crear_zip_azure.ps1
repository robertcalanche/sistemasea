# PowerShell script para crear sea_azure.zip listo para Azure App Service
# Excluye carpetas y archivos temporales, .venv, __pycache__, .git, .vscode, node_modules, *.pyc

$dest = "sea_azure.zip"
if (Test-Path $dest) { Remove-Item $dest }

$include = @(
    "app.py",
    "web_app.py",
    "sea_launch.py",
    "requirements.txt",
    "Procfile",
    "startup.txt",
    "Dockerfile",
    ".env.example",
    "AZURE_DEPLOY.md",
    "templates",
    "static"
)


# Recopilar archivos y carpetas a incluir
$files = @()
foreach ($item in $include) {
    if (Test-Path $item) {
        $files += $item
    }
}

# Comprimir
Compress-Archive -Path $files -DestinationPath $dest -Force
Write-Host "Archivo $dest creado. Verifica el contenido antes de subir a Azure."