[CmdletBinding()]
param(
    [string]$BindHost = "127.0.0.1",
    [ValidateRange(1, 65535)]
    [int]$Port = 8000,
    [switch]$NoReload,
    [switch]$NoBrowser,
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

$venvDirectory = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvDirectory "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    $systemPython = Get-Command python -ErrorAction SilentlyContinue
    if (-not $systemPython) {
        Stop-WithMessage "Python was not found. Install Python 3.12+ and add it to PATH."
    }

    $systemVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Python could not be executed."
    }

    $systemVersionParts = $systemVersion.Trim().Split('.')
    $systemPythonSupported = ([int]$systemVersionParts[0] -gt 3) -or (
        ([int]$systemVersionParts[0] -eq 3) -and ([int]$systemVersionParts[1] -ge 12)
    )
    if (-not $systemPythonSupported) {
        Stop-WithMessage "Python $systemVersion is installed, but Python 3.12+ is required."
    }

    Write-Host "[AlgoRecall] Creating virtual environment in .venv..." -ForegroundColor Yellow
    & python -m venv $venvDirectory
    if (($LASTEXITCODE -ne 0) -or (-not (Test-Path -LiteralPath $venvPython))) {
        Stop-WithMessage "Virtual environment creation failed."
    }
}

$versionText = & $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "The .venv Python interpreter could not be executed. Recreate .venv."
}

$versionParts = $versionText.Trim().Split('.')
$pythonSupported = ([int]$versionParts[0] -gt 3) -or (
    ([int]$versionParts[0] -eq 3) -and ([int]$versionParts[1] -ge 12)
)
if (-not $pythonSupported) {
    Stop-WithMessage "The .venv uses Python $versionText, but Python 3.12+ is required."
}

if (-not $SkipInstall) {
    & $venvPython -c "import fastapi, sqlalchemy, alembic, jinja2, uvicorn, pydantic_settings, multipart, tzdata" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[AlgoRecall] Installing missing runtime dependencies..." -ForegroundColor Yellow
        & $venvPython -m pip install -e .
        if ($LASTEXITCODE -ne 0) {
            Stop-WithMessage "Dependency installation failed. Check the network and Python environment."
        }
    }
}

if (-not (Test-Path -LiteralPath (Join-Path $projectRoot "data"))) {
    New-Item -ItemType Directory -Path (Join-Path $projectRoot "data") | Out-Null
}

$reloadDescription = if ($NoReload) { "disabled" } else { "enabled" }
$browserHost = if ($BindHost -in @("0.0.0.0", "::", "[::]")) { "127.0.0.1" } else { $BindHost }
$appUrl = "http://${browserHost}:$Port/"
Write-Host ""
Write-Host "[AlgoRecall] Starting..." -ForegroundColor Green
Write-Host "[AlgoRecall] Python: $venvPython"
Write-Host "[AlgoRecall] URL: $appUrl"
Write-Host "[AlgoRecall] Auto reload: $reloadDescription"
Write-Host "[AlgoRecall] Open browser: $(if ($NoBrowser) { 'disabled' } else { 'enabled' })"
Write-Host "[AlgoRecall] Press Ctrl+C to stop."
Write-Host ""

if (-not $NoBrowser) {
    $browserJob = Start-Job -ScriptBlock {
        param([string]$Url)
        for ($attempt = 0; $attempt -lt 60; $attempt++) {
            try {
                $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 1
                if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                    Start-Process $Url
                    return
                }
            }
            catch {
                Start-Sleep -Milliseconds 500
            }
        }
    } -ArgumentList $appUrl
}

$uvicornArguments = @(
    "-m", "uvicorn",
    "app.main:app",
    "--host", $BindHost,
    "--port", $Port.ToString()
)
if (-not $NoReload) {
    $uvicornArguments += "--reload"
}

& $venvPython @uvicornArguments
$serverExitCode = $LASTEXITCODE
if ($browserJob) {
    Stop-Job -Job $browserJob -ErrorAction SilentlyContinue
    Remove-Job -Job $browserJob -Force -ErrorAction SilentlyContinue
}
exit $serverExitCode
