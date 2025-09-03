param([string]$Repo)
if (-not $env:ADMIN_TOKEN) { Write-Error "ADMIN_TOKEN not set"; exit 1 }
if (-not $Repo) { Write-Error "Repo (owner/name) required"; exit 1 }

$Headers = @{
  "Authorization" = "token $($env:ADMIN_TOKEN)"
  "Accept"        = "application/vnd.github+json"
}

$body1 = @{
  enforce_admins = $true
  required_linear_history = $true
  allow_force_pushes = $false
  allow_deletions = $false
  required_status_checks = @{
    strict = $true
    contexts = @("CI","CodeQL","Dependency Audit")
  }
  required_pull_request_reviews = @{
    require_code_owner_reviews = $true
    required_approving_review_count = 2
    dismiss_stale_reviews = $true
  }
  restrictions = $null
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Put -Headers $Headers -Uri "https://api.github.com/repos/$Repo/branches/main/protection" -Body $body1

$body2 = @{
  security_and_analysis = @{
    secret_scanning = @{ status = "enabled" }
    secret_scanning_push_protection = @{ status = "enabled" }
    dependabot_security_updates = @{ status = "enabled" }
  }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Patch -Headers $Headers -Uri "https://api.github.com/repos/$Repo" -Body $body2

Write-Host "Hardened $Repo"
