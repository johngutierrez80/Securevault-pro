# ==============================================================
# SecureVault Pro - Download images from Docker Hub
#
# Usage:
#   .\scripts\pull-images.ps1
# ==============================================================

$TAG = "v1.0.0"
$REGISTRY = "necromanoger"

$IMAGES = @(
    "$REGISTRY/securevault-auth:$TAG",
    "$REGISTRY/securevault-vault:$TAG",
    "$REGISTRY/securevault-worker:$TAG",
    "$REGISTRY/securevault-frontend:$TAG"
)

Write-Host ""
Write-Host "Checking Docker..." -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker not found. Install Docker Desktop and retry." -ForegroundColor Red
    Write-Host "https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker Desktop is not running." -ForegroundColor Red
    exit 1
}

Write-Host "OK - Docker available." -ForegroundColor Green

Write-Host ""
Write-Host "Downloading SecureVault Pro images..." -ForegroundColor Cyan
Write-Host "Tag: $TAG" -ForegroundColor Cyan
Write-Host ""

$failed = @()

foreach ($img in $IMAGES) {
    Write-Host "  >> docker pull $img" -ForegroundColor DarkGray
    docker pull $img

    if ($LASTEXITCODE -ne 0) {
        $failed += $img
        Write-Host "  FAIL: $img" -ForegroundColor Red
    }
    else {
        Write-Host "  OK: $img" -ForegroundColor Green
    }

    Write-Host ""
}

if ($failed.Count -gt 0) {
    Write-Host "The following images could not be downloaded:" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "Check your network connection and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "================================================" -ForegroundColor Green
Write-Host "All images downloaded successfully" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Local images:" -ForegroundColor Cyan
docker image ls "$REGISTRY/*"
