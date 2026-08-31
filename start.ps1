[CmdletBinding()]
param(
    [string]$BindHost = "127.0.0.1",
    [ValidateRange(1, 65535)]
    [int]$Port = 8000,
    [switch]$NoReload,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

function Stop-WithMessage {
    param([string]$Message)
    Write-Host "[AlgoRecall] $Message" -ForegroundColor Red
    exit 1
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    Stop-WithMessage "Python was not found. Install Python 3.12+ and add it to PATH."
}

$versionText = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "Python could not be executed."
}

$versionParts = $versionText.Trim().Split('.')
$pythonSupported = ([int]$versionParts[0] -gt 3) -or (
    ([int]$versionParts[0] -eq 3) -and ([int]$versionParts[1] -ge 12)
)
if (-not $pythonSupported) {
    Stop-WithMessage "Python $versionText is installed, but Python 3.12+ is required."
}

if (-not $SkipInstall) {
    & python -c "import fastapi, sqlalchemy, alembic, jinja2, uvicorn" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[AlgoRecall] Installing missing runtime dependencies..." -ForegroundColor Yellow
        & python -m pip install -e .
        if ($LASTEXITCODE -ne 0) {
            Stop-WithMessage "Dependency installation failed. Check the network and Python environment."
        }
    }
}

if (-not (Test-Path -LiteralPath (Join-Path $projectRoot "data"))) {
    New-Item -ItemType Directory -Path (Join-Path $projectRoot "data") | Out-Null
}

$reloadDescription = if ($NoReload) { "disabled" } else { "enabled" }
Write-Host ""
Write-Host "[AlgoRecall] Starting..." -ForegroundColor Green
Write-Host "[AlgoRecall] URL: http://${BindHost}:$Port"
Write-Host "[AlgoRecall] Auto reload: $reloadDescription"
Write-Host "[AlgoRecall] Press Ctrl+C to stop."
Write-Host ""

$uvicornArguments = @(
    "-m", "uvicorn",
    "app.main:app",
    "--host", $BindHost,
    "--port", $Port.ToString()
)
if (-not $NoReload) {
    $uvicornArguments += "--reload"
}

& python @uvicornArguments
exit $LASTEXITCODE
