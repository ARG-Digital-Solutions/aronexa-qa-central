# QA38 proposal. Requires separately enrolled, disposable one-job interactive Windows VM.
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$InputDirectory,
 [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedContextSha,
 [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedSourceBundleSha,
 [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedQaArchiveSha
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT){throw 'WIN11P requires Windows'}
if($env:WIN11P_EPHEMERAL_EXECUTION -ne 'AUTHORIZED_ONE_JOB_VM'){throw 'WIN11P runner not enrolled'}
foreach($entry in @(Get-ChildItem Env:)){
 if($entry.Name -match '^(GH_TOKEN|GITHUB_TOKEN|ARONEXA_.*|SPRING_.*|PGHOST|PGPORT|PGDATABASE|PGUSER|PGPASSWORD|JAVA_TOOL_OPTIONS|JDK_JAVA_OPTIONS|_JAVA_OPTIONS|MAVEN_OPTS|MAVEN_ARGS|NODE_OPTIONS|NODE_PATH)$' -and $entry.Value){
  throw 'WIN11P refuses inherited credentials, database or JVM overrides'
 }
}
foreach($p in @(5176,5186)){
 $probe=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,$p)
 try{$probe.Start()}finally{$probe.Stop()}
}
$inputRoot=(Resolve-Path -LiteralPath $InputDirectory).Path
function Assert-Hash([string]$Path,[string]$Expected){
 if((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Expected){throw 'WIN11P input digest mismatch'}
}
Assert-Hash (Join-Path $inputRoot 'context.json') $ExpectedContextSha
Assert-Hash (Join-Path $inputRoot 'source.bundle') $ExpectedSourceBundleSha
Assert-Hash (Join-Path $inputRoot 'qa.zip') $ExpectedQaArchiveSha
$c=Get-Content -LiteralPath (Join-Path $inputRoot 'context.json') -Raw | ConvertFrom-Json
if($c.source_bundle_sha256 -ne $ExpectedSourceBundleSha -or $c.qa_archive_sha256 -ne $ExpectedQaArchiveSha -or
 $c.source_sha -notmatch '^[0-9a-f]{40}$' -or $c.qa_sha -ne $env:GITHUB_SHA -or
 $c.run_id -ne $env:GITHUB_RUN_ID -or $c.run_attempt -ne $env:GITHUB_RUN_ATTEMPT -or
 $c.request_id -ne ($env:GITHUB_RUN_ID+'-'+$env:GITHUB_RUN_ATTEMPT)){
 throw 'WIN11P context does not identify this execution'
}
$work=Join-Path $env:RUNNER_TEMP ('win11p-private-'+$c.request_id)
if(Test-Path -LiteralPath $work){throw 'WIN11P private work directory already exists'}
[void][IO.Directory]::CreateDirectory($work)
$public=Join-Path $env:RUNNER_TEMP 'win11p-public'
if(Test-Path -LiteralPath $public){throw 'WIN11P public evidence directory already exists'}
[void][IO.Directory]::CreateDirectory($public)
$qa=Join-Path $work 'qa'
Expand-Archive -LiteralPath (Join-Path $inputRoot 'qa.zip') -DestinationPath $qa
$app=Join-Path $work 'app'
& git init --quiet $app
if($LASTEXITCODE -ne 0){throw 'WIN11P git init failed'}
& git -C $app fetch --quiet --no-tags (Join-Path $inputRoot 'source.bundle') HEAD
if($LASTEXITCODE -ne 0){throw 'WIN11P source bundle fetch failed'}
& git -C $app checkout --quiet --detach FETCH_HEAD
if($LASTEXITCODE -ne 0 -or (& git -C $app rev-parse HEAD).Trim() -ne $c.source_sha){throw 'WIN11P source pin mismatch'}
foreach($tool in @('java.exe','jlink.exe','mvn.cmd','node.exe','npm.cmd','docker.exe','python.exe','powershell.exe')){
 if(-not(Get-Command $tool -ErrorAction SilentlyContinue)){throw 'WIN11P required tool unavailable'}
}
$javaVersion=(& java.exe --version | Select-Object -First 1)
$nodeVersion=(& node.exe --version)
if($javaVersion -notmatch '\b21\.' -or $nodeVersion -notmatch '^v24\.'){throw 'WIN11P Java21/Node24 required'}
$dockerType=(& docker.exe info --format '{{.OSType}}')
if($LASTEXITCODE -ne 0 -or $dockerType -ne 'linux'){throw 'WIN11P isolated Linux-container Docker required'}
$containers=@(& docker.exe ps -aq)
if($LASTEXITCODE -ne 0 -or $containers.Count -ne 0){throw 'WIN11P Docker is not a fresh isolated engine'}
$operatorRoot=Join-Path $env:LOCALAPPDATA 'ARG-Digital\AroNexa-Pilot09-Disposable'
if(Test-Path -LiteralPath $operatorRoot){throw 'WIN11P refuses existing operator labs'}
$descriptor=@{context=$c;versions=@{java=21;node=24;postgres=17};source_clean=$false;
 frontend_exit=1;build_exit=1;full_maven_exit=1;rc03_exit=1;operator_exit=1;
 frontend_log=(Join-Path $work 'frontend.log');search_xml='';roles_xml='';rls_xml='';
 full_maven_reports=@();phase_a_xml='';phase_b_xml='';rc03_summary='';
 rc03_log=(Join-Path $work 'rc03.log');runtime_home='';runtime_sha256='';
 operator_xml='';operator_observation='';operator_summary='';postgres_observations=(Join-Path $work 'postgres-observations.jsonl')}
function Run-Private([string]$Log,[scriptblock]$Command){
 & $Command *> $Log
 return [int]$LASTEXITCODE
}
$reportDir=Join-Path $app 'backend\target\surefire-reports'
$observerStop=Join-Path $work 'observer.stop'
$observer=Start-Job -FilePath (Join-Path $qa 'scripts\Observe-Win11pPostgres.ps1') -ArgumentList $descriptor.postgres_observations,$observerStop,(Get-Command docker.exe).Source
try {
 $install=Run-Private (Join-Path $work 'qa-install.log') { & npm.cmd --prefix $qa ci --no-audit --no-fund }
 if($install -ne 0){throw 'WIN11P QA dependency installation failed'}
 Push-Location $qa
 try{$install=Run-Private (Join-Path $work 'playwright-install.log') { & node.exe node_modules/playwright/cli.js install chromium }}finally{Pop-Location}
 if($install -ne 0){throw 'WIN11P Playwright installation failed'}
 $install=Run-Private (Join-Path $work 'app-install.log') { & npm.cmd --prefix (Join-Path $app 'frontend') ci --no-audit --no-fund }
 if($install -ne 0){throw 'WIN11P application dependency installation failed'}
 $descriptor.frontend_exit=Run-Private $descriptor.frontend_log { & npm.cmd --prefix (Join-Path $app 'frontend') test }
 $descriptor.build_exit=Run-Private (Join-Path $work 'build.log') { & npm.cmd --prefix (Join-Path $app 'frontend') run build:connected:test }
 # Never set indiscriminate acknowledgement flags for the inherited full suite.
 $descriptor.full_maven_exit=Run-Private (Join-Path $work 'full-maven.log') { & mvn.cmd -B -f (Join-Path $app 'backend\pom.xml') verify }
 $full=Join-Path $work 'full-junit'
 [void][IO.Directory]::CreateDirectory($full)
 if(Test-Path -LiteralPath $reportDir){
  foreach($file in @(Get-ChildItem -LiteralPath $reportDir -Filter 'TEST-*.xml' -File)){
   Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $full $file.Name)
  }
 }
 $descriptor.full_maven_reports=@(Get-ChildItem -LiteralPath $full -Filter '*.xml' -File | ForEach-Object {$_.FullName})
 $security=Run-Private (Join-Path $work 'search-security.log') {
  & mvn.cmd -B -f (Join-Path $app 'backend\pom.xml') '-Dtest=PatientCandidateSearchHttpAcceptanceTests,PostgresTenantRlsTests,AuthRoleBoundaryTests' '-Dsurefire.failIfNoSpecifiedTests=true' test
 }
 if($security -eq 0){
  $descriptor.search_xml=Join-Path $reportDir 'TEST-com.argdigital.aronexa.patient.PatientCandidateSearchHttpAcceptanceTests.xml'
  $descriptor.roles_xml=Join-Path $reportDir 'TEST-com.argdigital.aronexa.auth.AuthRoleBoundaryTests.xml'
  $descriptor.rls_xml=Join-Path $reportDir 'TEST-com.argdigital.aronexa.auth.PostgresTenantRlsTests.xml'
 }
 $runtime=Join-Path $work 'portable-java21'
 $link=Run-Private (Join-Path $work 'jlink.log') {
  & (Join-Path $env:JAVA_HOME 'bin\jlink.exe') --module-path (Join-Path $env:JAVA_HOME 'jmods') --add-modules ALL-MODULE-PATH --strip-debug --no-header-files --no-man-pages --output $runtime
 }
 if($link -ne 0){throw 'WIN11P portable runtime build failed'}
 $descriptor.runtime_home=$runtime
 $descriptor.runtime_sha256=(& python.exe -c 'import sys;sys.path.insert(0,sys.argv[1]);from win11p_collect import runtime_hash;print(runtime_hash(sys.argv[2]))' (Join-Path $qa 'scripts') $runtime).Trim()
 if($LASTEXITCODE -ne 0){throw 'WIN11P runtime inventory failed'}
 $env:ARONEXA_WIN11P_JAVA_HOME=$runtime
 $env:MAVEN_OPTS='-Djvm="'+(Join-Path $runtime 'bin\java.exe')+'"'
 try{
  $descriptor.rc03_exit=Run-Private $descriptor.rc03_log {
   & powershell.exe -NoProfile -File (Join-Path $app 'scripts\pilot\Test-AroNexa-Pilot05-DistinctJvm-Restart.ps1') -ExpectedCommit $c.source_sha -Rc03 -PreviewPort 5186 -QaCentralPath $qa
  }
 }finally{
  [Environment]::SetEnvironmentVariable('MAVEN_OPTS',$null,'Process')
  [Environment]::SetEnvironmentVariable('ARONEXA_WIN11P_JAVA_HOME',$null,'Process')
 }
 if($descriptor.rc03_exit -eq 0){
  $match=@(Select-String -LiteralPath $descriptor.rc03_log -Pattern '^EvidenceFolder=')
  if($match.Count -ne 1){throw 'WIN11P ambiguous RC03 evidence'}
  $folder=$match[0].Line.Substring('EvidenceFolder='.Length)
  if((Split-Path $folder -Parent) -ne (Join-Path $env:USERPROFILE 'AroNexa-Local-QA') -or
      (Split-Path $folder -Leaf) -notmatch '^PILOT05-[0-9a-f-]{36}$'){throw 'WIN11P unexpected RC03 evidence path'}
  $descriptor.phase_a_xml=Join-Path $folder 'phaseA-surefire.xml'
  $descriptor.phase_b_xml=Join-Path $folder 'phaseB-surefire.xml'
  $descriptor.rc03_summary=Join-Path $folder 'SUMMARY.txt'
 }
 Write-Output 'WIN11P operator: use the approved VM console and private fictional staff sheet; complete Reception, then STOP. No patient data.'
 $descriptor.operator_exit=Run-Private (Join-Path $work 'operator-private.log') {
  & powershell.exe -NoProfile -File (Join-Path $app 'scripts\pilot\Start-AroNexa-WindowsAssistedPilot.ps1') -ExpectedCommit $c.source_sha -ConfirmFictionalDisposableLab
 }
 if($descriptor.operator_exit -eq 0){
  $labs=@(Get-ChildItem -LiteralPath $operatorRoot -Directory -ErrorAction Stop)
  if($labs.Count -ne 1 -or $labs[0].Name -notmatch '^pilot09-[0-9a-f]{32}$'){throw 'WIN11P ambiguous operator lab'}
  $descriptor.operator_observation=Join-Path $labs[0].FullName 'SESSION-OBSERVATION.txt'
  $descriptor.operator_xml=Join-Path $reportDir 'TEST-com.argdigital.aronexa.appointment.Pilot05SeparateJvmHttpTests.xml'
  $opMatches=@(Select-String -LiteralPath (Join-Path $work 'operator-private.log') -Pattern '^EvidenceFolder=')
  if($opMatches.Count -ne 1){throw 'WIN11P ambiguous operator evidence'}
  $opFolder=$opMatches[0].Line.Substring('EvidenceFolder='.Length)
  if((Split-Path $opFolder -Parent) -ne (Join-Path $env:USERPROFILE 'AroNexa-Local-QA') -or
      (Split-Path $opFolder -Leaf) -notmatch '^PILOT05-[0-9a-f-]{36}$'){throw 'WIN11P operator evidence path mismatch'}
  $descriptor.operator_summary=Join-Path $opFolder 'SUMMARY.txt' 
 }
 $descriptor.source_clean=((& git -C $app rev-parse HEAD).Trim() -eq $c.source_sha -and
  @(& git -C $app status --porcelain --untracked-files=no).Count -eq 0)
} catch {
 Write-Warning 'WIN11P incomplete required stage; private diagnostics retained only until VM destruction'
} finally {
 [IO.File]::WriteAllText($observerStop,'STOP')
 if($null -ne $observer){Stop-Job -Job $observer; Remove-Job -Job $observer}
 $privateDescriptor=Join-Path $work 'collector-private.json'
 [IO.File]::WriteAllText($privateDescriptor,($descriptor | ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
 & python.exe (Join-Path $qa 'scripts\win11p_collect.py') --descriptor $privateDescriptor --output (Join-Path $public 'evidence.json')
 $collectorExit=$LASTEXITCODE
}
if($collectorExit -ne 0){throw 'WIN11P required execution evidence failed; no Central PASS'}
Write-Output 'WIN11P sanitized execution complete; independent receipts and reporter approval required'
