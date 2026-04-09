param(
    [string]$BaseUrl = "http://localhost:3000",
    [string]$Username = "demo_worker_user",
    [string]$Password = "DemoWorkerPass123!",
    [string]$Site = "expiring-demo.local",
    [int]$WaitSeconds = 40
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Text)
    Write-Host "`n=== $Text ===" -ForegroundColor Cyan
}

function Invoke-JsonRequest {
    param(
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers,
        $Body
    )

    $params = @{
        Method      = $Method
        Uri         = $Url
        ContentType = "application/json"
        Headers     = $Headers
    }

    if ($null -ne $Body) {
        $params.Body = ($Body | ConvertTo-Json -Depth 6)
    }

    return Invoke-RestMethod @params
}

Write-Step "Preparar entorno"
Write-Host "Asegurando servicios en ejecucion..."
docker compose up -d | Out-Null

Write-Step "Paso 1: crear usuario, login y secreto con expiracion"

try {
    Invoke-JsonRequest -Method "POST" -Url "$BaseUrl/auth/register" -Headers @{} -Body @{
        username = $Username
        password = $Password
    } | Out-Null
    Write-Host "Usuario creado: $Username"
}
catch {
    Write-Host "Usuario ya existe o no se pudo crear (continuando): $($_.Exception.Message)" -ForegroundColor Yellow
}

$login = Invoke-JsonRequest -Method "POST" -Url "$BaseUrl/auth/login" -Headers @{} -Body @{
    username = $Username
    password = $Password
}

$token = $login.access_token
if (-not $token) {
    throw "No se obtuvo token de acceso."
}

$headers = @{ Authorization = "Bearer $token" }

Invoke-JsonRequest -Method "POST" -Url "$BaseUrl/vault/secret" -Headers $headers -Body @{
    site = $Site
    password = "super-secret"
    expires_in_days = 1
} | Out-Null

$secretsBefore = Invoke-JsonRequest -Method "GET" -Url "$BaseUrl/vault/secret" -Headers $headers -Body $null
$target = $secretsBefore | Where-Object { $_.site -eq $Site } | Select-Object -Last 1
if (-not $target) {
    throw "No se encontro el secreto recien creado para '$Site'."
}

$secretId = [int]$target.id
Write-Host "Secreto creado id=$secretId site=$Site"

Write-Step "Paso 2: forzar expiracion corta y esperar worker"

$nowEpoch = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$member = "$Username`:$secretId"
Write-Host "Forzando expiracion en Redis member=$member score=$nowEpoch"

docker compose exec -T redis redis-cli ZADD jobs:secret_expirations $nowEpoch $member | Out-Null

Write-Host "Esperando $WaitSeconds segundos para ciclo de limpieza del worker..."
Start-Sleep -Seconds $WaitSeconds

Write-Step "Paso 3: verificar eliminacion automatica"

$secretsAfter = Invoke-JsonRequest -Method "GET" -Url "$BaseUrl/vault/secret" -Headers $headers -Body $null
$stillExists = $secretsAfter | Where-Object { [int]$_.id -eq $secretId }

if ($stillExists) {
    Write-Host "Resultado: el secreto sigue presente (worker no lo elimino aun)." -ForegroundColor Yellow
    Write-Host "Sugerencia: revisar logs con 'docker compose logs worker --tail=100'"
    exit 1
}

Write-Host "Resultado: secreto expirado eliminado correctamente por worker." -ForegroundColor Green
Write-Host "Demo completada."
