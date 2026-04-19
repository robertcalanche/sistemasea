param(
    [string[]]$Domains = @("sea.local", "evaluaciones.local", "admin.local"),
    [string]$IpAddress = "127.0.0.1"
)

$hostsPath = Join-Path $env:SystemRoot "System32\drivers\etc\hosts"
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)

if (-not $isAdmin) {
    Write-Error "Ejecuta este script en PowerShell como Administrador para modificar el archivo hosts."
    exit 1
}

if (-not (Test-Path $hostsPath)) {
    Write-Error "No se encontró el archivo hosts en $hostsPath"
    exit 1
}

$currentLines = Get-Content -Path $hostsPath -ErrorAction Stop
$normalizedCurrent = $currentLines | ForEach-Object { $_.Trim().ToLowerInvariant() }
$added = @()

foreach ($domain in $Domains) {
    if ([string]::IsNullOrWhiteSpace($domain)) {
        $cleanDomain = ""
    }
    else {
        $cleanDomain = $domain.Trim().ToLowerInvariant()
    }
    if (-not $cleanDomain) {
        continue
    }

    $entry = "$IpAddress`t$cleanDomain"
    if ($normalizedCurrent -contains $entry.ToLowerInvariant()) {
        continue
    }

    Add-Content -Path $hostsPath -Value $entry
    $added += $cleanDomain
}

if ($added.Count -eq 0) {
    Write-Host "No se agregaron cambios. Los dominios ya estaban configurados en hosts." -ForegroundColor Yellow
    exit 0
}

Write-Host "Dominios locales configurados correctamente:" -ForegroundColor Green
$added | ForEach-Object { Write-Host " - $IpAddress $_" }
Write-Host "Ahora puedes abrir http://$($Domains[0]):5000 en este PC." -ForegroundColor Cyan