# Windows Setup (PowerShell)

```powershell
# 1) Unpack and init
Expand-Archive .\heidi-launch-repo.zip -DestinationPath .
cd .\heidi-launch
git init -b main
git add .
git commit -m "chore: init Heidi launch scaffold"

# 2) Create hardened private repo
.\scripts\gh-setup.ps1 -RepoSlug protoforge/heidi-launch

# 3) Add remote and push
git remote add origin git@github.com:protoforge/heidi-launch.git
git push -u origin main
```

**Optional:** Organization-level hardening
```powershell
.\scripts\gh-org-hardening.ps1 -Org protoforge -RepoSlug protoforge/heidi-launch
```
