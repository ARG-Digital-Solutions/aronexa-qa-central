[CmdletBinding()]
param(
  [ValidateSet('verified','responsive','legacy','models')][string]$Suite='verified',
  [string]$BaseUrl='http://127.0.0.1:5175/',
  [string]$AppReviewPath='',
  [switch]$InstallDependencies
)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$uri=[Uri]$BaseUrl
if($uri.Scheme -ne 'http' -or $uri.Host -notin @('127.0.0.1','localhost')) { throw 'Local synthetic HTTP frontend only.' }
$env:ARONEXA_BASE_URL=$BaseUrl
if($InstallDependencies) {
  npm.cmd ci --no-audit --no-fund
  if($LASTEXITCODE -ne 0){throw 'npm ci failed'}
  npx.cmd playwright install chromium
  if($LASTEXITCODE -ne 0){throw 'Chromium installation failed'}
}
if($Suite -eq 'models') {
  if(-not $AppReviewPath){throw 'Models need -AppReviewPath of the isolated INT-R1 review worktree.'}
  $front=Join-Path $AppReviewPath 'frontend'
  if(-not (Test-Path -LiteralPath (Join-Path $front 'src\appointmentModel.ts'))){throw 'Expected isolated frontend not present.'}
  Push-Location $front
  try {
    node --experimental-strip-types --test test/reception-demo.test.mjs test/appointment-demo.test.mjs
    if($LASTEXITCODE -ne 0){throw 'Frontend model tests failed'}
  } finally {Pop-Location}
} else {
  if($Suite -eq 'legacy'){$argsList=@('playwright','test','-c','legacy/playwright.config.mjs')}
  elseif($Suite -eq 'responsive'){$argsList=@('playwright','test','tests/verified/int-r1-responsive.spec.mjs')}
  else {$argsList=@('playwright','test','tests/verified')}
  & npx.cmd @argsList
  if($LASTEXITCODE -ne 0){throw 'Playwright failed; inspect artifacts/playwright-report'}
}
Write-Host "QA suite $Suite finished. Review recorded test evidence, not just exit status."
