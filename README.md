# Heidi Launch

Hardened GitHub repository scaffold with CI, CodeQL, and dependency auditing.

## Contents
- `scripts/gh-setup.ps1`: Creates a private repo and configures strong protections and security.
- `scripts/gh-org-hardening.ps1`: Applies hardening to a repo within an org.
- `scripts/harden.ps1`: Applies protections via GitHub REST API using `ADMIN_TOKEN`.
- `scripts/ci-check.ps1`: Runs `black`, `flake8`, and `pytest`.
- `windows-setup.md`: Quick Windows setup steps.

## Local use
```powershell
# From Windows PowerShell
.\scripts\gh-setup.ps1 -RepoSlug <owner>/<repo>
# Optionally
.\scripts\gh-org-hardening.ps1 -Org <org> -RepoSlug <owner>/<repo>
```

## CI Workflows
- CI: runs formatting, linting, and tests; publishes a commit status context `CI`.
- CodeQL: runs code scanning; publishes a commit status context `CodeQL`.
- Dependency Audit: runs Python dependency audit; publishes a commit status context `Dependency Audit`.

These contexts align with branch protection settings configured by the scripts.