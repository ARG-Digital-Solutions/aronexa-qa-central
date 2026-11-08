# One-time setup, writes ONLY to the separate QA directory and normal browser cache.
# Explicit user permission required for downloads; never run automatically.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js is required.' }
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'npm.cmd is required.' }
Write-Host 'Installing pinned @playwright/test in the central QA directory...'
npm.cmd install --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw 'npm install failed.' }
$runner = Join-Path $PSScriptRoot 'node_modules\.bin\playwright.cmd'
if (-not (Test-Path -LiteralPath $runner)) { throw 'Playwright CLI not found.' }
Write-Host 'Installing Playwright Chromium browser...'
& $runner install chromium
if ($LASTEXITCODE -ne 0) { throw 'Playwright Chromium install failed.' }
Write-Host 'QA setup complete. No AroNexa application worktree modified.' -ForegroundColor Green
