$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Name"
    & $Command
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Invoke-Step "Format backend" {
    .\.venv\Scripts\ruff.exe format .
}

Invoke-Step "Lint backend" {
    .\.venv\Scripts\ruff.exe check .
}

Invoke-Step "Test backend" {
    .\.venv\Scripts\pytest.exe -q
}

Invoke-Step "Run evals" {
    .\.venv\Scripts\python.exe -m evals.run
}

Invoke-Step "Lint frontend" {
    Push-Location web
    try {
        npm run lint
    }
    finally {
        Pop-Location
    }
}

Invoke-Step "Build frontend" {
    Push-Location web
    try {
        npm run build
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "All checks passed."
