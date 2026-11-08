param(
    [ValidateSet('smoke','registration','appointments','responsive','extended','core','all')]
    [string]$Suite = 'smoke',
    [ValidateSet('chromium-desktop','chromium-tablet','chromium-mobile','all')]
    [string]$Project = 'chromium-desktop',
    [string]$BaseUrl = 'http://127.0.0.1:5173/',
    [switch]$Headed
)
$ErrorActionPreference = 'Stop'
$u = [Uri]$BaseUrl
if ($u.Scheme -notin @('http','https') -or $u.Host -notin @('127.0.0.1','localhost')) {
    throw 'Only a localhost synthetic demo target is permitted.'
}
$runner = Join-Path $PSScriptRoot 'node_modules\.bin\playwright.cmd'
if (-not (Test-Path -LiteralPath $runner)) {
    throw 'Playwright not installed. Run Setup-Playwright-QA.ps1 separately first.'
}
$env:ARONEXA_BASE_URL = $BaseUrl
Set-Location -LiteralPath $PSScriptRoot
$argsList = @('test')
switch ($Suite) {
    'smoke'        { $argsList += @('--grep','@smoke') }
    'registration' { $argsList += @('--grep','@registration') }
    'appointments' { $argsList += @('--grep','@appointments') }
    'responsive'   { $argsList += @('--grep','@responsive') }
    'extended'     { $argsList += @('--grep','@extended') }
    'core'         { $argsList += @('--grep-invert','@extended') }
}
if ($Project -ne 'all') { $argsList += @('--project',$Project) }
if ($Headed) { $argsList += '--headed' }
Write-Host "Running $Suite suite on $Project against $BaseUrl"
& $runner @argsList
if ($LASTEXITCODE -ne 0) {
    throw 'Playwright reported failures. Inspect artifacts\playwright-report.'
}
Write-Host "Completed. HTML report: $PSScriptRoot\artifacts\playwright-report\index.html" -ForegroundColor Green
