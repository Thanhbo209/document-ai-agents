$ErrorActionPreference = "Stop"

$targets = @(
    "http://127.0.0.1:8000/health",
    "http://127.0.0.1:8000/ready",
    "http://127.0.0.1:8000/metrics",
    "http://127.0.0.1:3000"
)

foreach ($target in $targets) {
    Write-Host "Checking $target"
    $response = Invoke-WebRequest -Uri $target -UseBasicParsing
    Write-Host "OK $($response.StatusCode) $target"
}
