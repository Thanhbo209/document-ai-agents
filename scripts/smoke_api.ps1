param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

$targets = @(
    @{
        Name = "health"
        Url = "$ApiBaseUrl/health"
        Contains = '"status":"ok"'
    },
    @{
        Name = "ready"
        Url = "$ApiBaseUrl/ready"
        Contains = '"database":"ok"'
    },
    @{
        Name = "metrics"
        Url = "$ApiBaseUrl/metrics"
        Contains = "rag_platform_requests_total"
    }
)

foreach ($target in $targets) {
    Write-Host "Checking $($target.Name): $($target.Url)"
    $response = Invoke-WebRequest -Uri $target.Url -UseBasicParsing
    $body = $response.Content -replace "\s", ""

    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
        throw "$($target.Name) returned status $($response.StatusCode)"
    }

    if ($body -notlike "*$($target.Contains)*") {
        throw "$($target.Name) response did not contain expected text: $($target.Contains)"
    }

    Write-Host "OK $($response.StatusCode) $($target.Name)"
}

Write-Host "API smoke checks passed."
