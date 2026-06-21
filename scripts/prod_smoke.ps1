param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8000",
    [string]$WebBaseUrl = "http://127.0.0.1:3000"
)

$ErrorActionPreference = "Stop"

& "$PSScriptRoot\smoke_api.ps1" -ApiBaseUrl $ApiBaseUrl

Write-Host "Checking web: $WebBaseUrl"
$response = Invoke-WebRequest -Uri $WebBaseUrl -UseBasicParsing

if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
    throw "web returned status $($response.StatusCode)"
}

Write-Host "OK $($response.StatusCode) web"
Write-Host "Production smoke checks passed."
