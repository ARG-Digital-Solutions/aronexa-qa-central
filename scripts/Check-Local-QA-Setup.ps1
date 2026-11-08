$ErrorActionPreference='Stop'
Write-Host 'QA location:' (Get-Location).Path
Write-Host 'Node:'; node --version
Write-Host 'NPM:'; npm.cmd --version
Write-Host 'Git:'; git --version
$u='http://127.0.0.1:5175/'
try { $r=Invoke-WebRequest -Uri $u -Method Get -TimeoutSec 5; Write-Host "Local frontend: HTTP $($r.StatusCode)" }
catch { Write-Host "Frontend not reachable at $u; start the isolated review Vite server first." }
