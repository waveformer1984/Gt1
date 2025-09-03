param(
  [string]$Org = "protoforge",
  [string]$RepoSlug = ""
)
if (-not $RepoSlug) { $RepoSlug = "$Org/heidi-launch" }
$ErrorActionPreference = "Stop"

gh api -X PUT "repos/$RepoSlug/branches/main/protection" `
  -f enforce_admins=true `
  -f required_linear_history=true `
  -f required_pull_request_reviews.dismiss_stale_reviews=true `
  -f required_pull_request_reviews.require_code_owner_reviews=true `
  -f required_pull_request_reviews.required_approving_review_count=2 `
  -f required_status_checks.strict=true `
  -f required_status_checks.contexts='["CI","CodeQL","Dependency Audit"]' `
  -f allow_force_pushes=false -f allow_deletions=false | Out-Null

gh api -X PATCH "repos/$RepoSlug" `
  -f "security_and_analysis[secret_scanning][status]=enabled" `
  -f "security_and_analysis[secret_scanning_push_protection][status]=enabled" `
  -f "security_and_analysis[dependabot_security_updates][status]=enabled" | Out-Null

Write-Host "Hardening complete for $RepoSlug"
