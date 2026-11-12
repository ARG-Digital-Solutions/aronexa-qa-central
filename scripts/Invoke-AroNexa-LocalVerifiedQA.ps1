#requires -Version 5.1
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$AppRoot,
  [Parameter(Mandatory=$true)][string]$ExpectedAppSha,
  [string]$EvidenceDirectory=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$qaRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$qaSha='';$appSha='';$result='FAIL';$failure='';$tests=0;$failed=0;$skipped=0;$server=$null
$checks=[ordered]@{synthetic_localhost='NOT_RUN';verified_playwright='NOT_RUN'}
$started=[DateTimeOffset]::UtcNow.ToString('o')
$previousCi=$env:CI
$previousUrl=$env:ARONEXA_BASE_URL
function Run([string]$Cmd,[string[]]$Args){& $Cmd @Args;if($LASTEXITCODE -ne 0){throw "$Cmd failed (exit $LASTEXITCODE)"}}
function GitSha([string]$Path){$sha=& git -C $Path rev-parse HEAD;if($LASTEXITCODE -ne 0){throw 'Git rev-parse failed'};return [string]$sha}
function RequireClean([string]$Path){$dirty=@(& git -C $Path status --porcelain --untracked-files=normal);if($LASTEXITCODE -ne 0 -or ($dirty -join '').Trim()){throw "Dirty checkout $Path"}}
try {
  if($ExpectedAppSha -cnotmatch '^[0-9a-f]{40}$'){throw 'Full exact lower-case app SHA required'}
  $app=(Resolve-Path -LiteralPath $AppRoot).Path
  if(-not(Test-Path (Join-Path $app 'frontend\package.json'))){throw 'AppRoot must contain frontend/package.json'}
  $appSha=GitSha $app;$qaSha=GitSha $qaRoot
  if($appSha -cne $ExpectedAppSha){throw 'App source SHA differs from expected SHA'}
  RequireClean $app;RequireClean $qaRoot
  if(-not $EvidenceDirectory){$EvidenceDirectory=Join-Path (Join-Path ([IO.Path]::GetTempPath()) 'aronexa-qa-evidence') ('qa-'+[DateTimeOffset]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+$appSha.Substring(0,8))}
  $evidence=[IO.Path]::GetFullPath($EvidenceDirectory)
  foreach($p in @($app,$qaRoot)){if($evidence.Equals($p,[StringComparison]::OrdinalIgnoreCase) -or $evidence.StartsWith($p.TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Evidence path inside checkout prohibited'}}
  New-Item -ItemType Directory -Force -Path $evidence | Out-Null
  foreach($cmd in @('node','npm.cmd','npx.cmd','git')){if(-not(Get-Command $cmd -ErrorAction SilentlyContinue)){throw "Missing prerequisite $cmd"}}
  $v=[string](& node -p 'process.versions.node');if($LASTEXITCODE -ne 0 -or [int]($v.Split('.')[0]) -lt 22){throw 'Node 22+ required'}
  $listener=New-Object Net.Sockets.TcpClient
  try {
    try {$listener.Connect('127.0.0.1',5175);throw 'Port 5175 already in use: refusing unknown server'}
    catch [System.Net.Sockets.SocketException] {} # Connection refused is expected.
  } finally {$listener.Dispose()}
  $env:CI='true';$env:ARONEXA_BASE_URL='http://127.0.0.1:5175/'
  $checks['synthetic_localhost']='PASS'
  Push-Location (Join-Path $app 'frontend')
  try {Run -Cmd 'npm.cmd' -Args @('ci','--no-audit','--no-fund')} finally {Pop-Location}
  Push-Location $qaRoot
  try {
    Run -Cmd 'npm.cmd' -Args @('ci','--no-audit','--no-fund')
    Run -Cmd 'npx.cmd' -Args @('playwright','install','chromium')
  } finally {Pop-Location}
  $server=Start-Process -FilePath 'cmd.exe' -ArgumentList @('/d','/s','/c','npm.cmd run dev -- --host 127.0.0.1 --port 5175 --strictPort') -WorkingDirectory (Join-Path $app 'frontend') -PassThru -RedirectStandardOutput (Join-Path $evidence 'vite-out.log') -RedirectStandardError (Join-Path $evidence 'vite-err.log')
  $ready=$false
  for($i=0;$i -lt 45;$i++){
    if($server.HasExited){break}
    Start-Sleep -Seconds 1
    try {$response=Invoke-WebRequest -Uri $env:ARONEXA_BASE_URL -TimeoutSec 2 -UseBasicParsing;if($response.StatusCode -eq 200){$ready=$true;break}}catch{}
  }
  if(-not $ready){throw 'Vite failed to start on localhost 5175'}
  Push-Location $qaRoot
  try {
    Run -Cmd 'npx.cmd' -Args @('playwright','test','tests/verified','--project','chromium-desktop','--workers=1')
    $path=Join-Path $qaRoot 'artifacts\results.xml'
    if(-not(Test-Path -LiteralPath $path)){throw 'Missing Playwright JUnit XML'}
    [xml]$xml=Get-Content -LiteralPath $path -Raw
    $suites=@($xml.testsuites.testsuite)
    if($suites.Count -lt 1){throw 'No Playwright JUnit suites found'}
    foreach($suite in $suites){$tests += [int]$suite.tests;$failed += [int]$suite.failures + [int]$suite.errors;$skipped += [int]$suite.skipped}
    if($tests -lt 1 -or $failed -gt 0 -or $skipped -gt 0){throw "Browser gate blocked tests=$tests fail=$failed skipped=$skipped"}
    $checks['verified_playwright']='PASS'
  } finally {Pop-Location}
  $result='PASS'
} catch {$failure=[string]$_.Exception.Message;Write-Warning "Local verified QA failed: $failure"}
finally {
  if($null -ne $server){try{& taskkill.exe /PID $server.Id /T /F 2>$null | Out-Null}catch{}}
  $env:CI=$previousCi;$env:ARONEXA_BASE_URL=$previousUrl
  if(-not (Get-Variable evidence -ErrorAction SilentlyContinue) -or -not $evidence){$evidence=Join-Path ([IO.Path]::GetTempPath()) ('aronexa-qa-failure-'+[DateTimeOffset]::UtcNow.ToString('yyyyMMdd-HHmmss'))}
  New-Item -ItemType Directory -Force -Path $evidence | Out-Null
  $manifest=[ordered]@{schema_version=1;kind='aronexa_central_qa_local';application_sha=$appSha;qa_sha=$qaSha;started_utc=$started;completed_utc=[DateTimeOffset]::UtcNow.ToString('o');result=$result;checks=$checks;browser_tests=$tests;browser_failures=$failed;browser_skipped=$skipped;failure=$failure;synthetic_only=$true;customer_release_approved=$false}
  $out=Join-Path $evidence 'qa-ci-evidence.json';$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $out -Encoding UTF8
  Write-Host "QA_RESULT=$result; APP_SHA=$appSha; QA_SHA=$qaSha; EVIDENCE=$out"
}
if($result -ne 'PASS'){exit 1}
exit 0
