# ==============================================================
# SecureVault Pro — Descarga de imagenes desde Docker Hub
#
# Ejecuta este script para descargar todas las imagenes del
# proyecto antes de correrlo por primera vez.
#
# Uso:
#   .\scripts\pull-images.ps1
#
# Requisito: tener Docker Desktop instalado y corriendo.
#   https://www.docker.com/products/docker-desktop
# ==============================================================

$TAG      = "v1.0.0"
$REGISTRY = "necromanoger"

$IMAGES = @(
    "$REGISTRY/securevault-auth:$TAG",
    "$REGISTRY/securevault-vault:$TAG",
    "$REGISTRY/securevault-worker:$TAG",
    "$REGISTRY/securevault-frontend:$TAG"
)

# ── Verificar Docker ────────────────────────────────────────
Write-Host ""
Write-Host "Verificando Docker..." -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker no encontrado. Instala Docker Desktop y vuelve a intentarlo." -ForegroundColor Red
    Write-Host "       https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker Desktop no esta corriendo. Inicialo y vuelve a ejecutar este script." -ForegroundColor Red
    exit 1
}

Write-Host "OK — Docker disponible." -ForegroundColor Green

# ── Descargar imagenes ──────────────────────────────────────
Write-Host ""
Write-Host "Descargando imagenes de SecureVault Pro (tag: $TAG)..." -ForegroundColor Cyan
Write-Host ""

$failed = @()

foreach ($img in $IMAGES) {
    Write-Host "  >> docker pull $img" -ForegroundColor DarkGray
    docker pull $img
    if ($LASTEXITCODE -ne 0) {
        $failed += $img
        Write-Host "  FALLO: $img" -ForegroundColor Red
    } else {
        Write-Host "  OK: $img" -ForegroundColor Green
    }
    Write-Host ""
}

# ── Resultado ───────────────────────────────────────────────
if ($failed.Count -gt 0) {
    Write-Host "Las siguientes imagenes no pudieron descargarse:" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "Verifica tu conexion a internet e intenta de nuevo." -ForegroundColor Yellow
    exit 1
}

Write-Host "================================================" -ForegroundColor Green
Write-Host "  Todas las imagenes descargadas correctamente" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Imagenes disponibles localmente:"
foreach ($img in $IMAGES) {
    Write-Host "  - $img"
}

