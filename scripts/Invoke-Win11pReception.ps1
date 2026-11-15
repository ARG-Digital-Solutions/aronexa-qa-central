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
 if($entry.Name -match '^(GH_TOKEN|GITHUB_TOKEN|ARONEXA_.*|SPRING_.*|PGHOST|PGPORT|PGDATABASE|PGUSER|PGPASSWORD|JAVA_TOOL_OPTIONS|JDK_JAVA_OPTIONS|_JAVA_OPTIONS|MAVEN_OPTS|MAVEN_ARGS|NODE_OPTIONS|NODE_PATH|WIN11P_PORTABLE_JAVA_HOME|WIN11P_QA_CENTRAL_PATH|WIN11P_QA_SHA)$' -and $entry.Value){
  throw 'WIN11P refuses inherited credentials, database or JVM overrides'
 }
}
$inputRoot=(Resolve-Path -LiteralPath $InputDirectory).Path
function Assert-Hash([string]$Path,[string]$Expected){
 if((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Expected){throw 'WIN11P input digest mismatch'}
}
Assert-Hash (Join-Path $inputRoot 'context.json') $ExpectedContextSha
Assert-Hash (Join-Path $inputRoot 'source.bundle') $ExpectedSourceBundleSha
Assert-Hash (Join-Path $inputRoot 'qa.zip') $ExpectedQaArchiveSha
$c=Get-Content -LiteralPath (Join-Path $inputRoot 'context.json') -Raw | ConvertFrom-Json
if($c.plan_id -ne 'WIN11P_RECEPTION_E2E' -or $c.event -ne 'workflow_dispatch' -or $c.ref -ne 'refs/heads/main' -or
 $c.source_bundle_sha256 -ne $ExpectedSourceBundleSha -or $c.qa_archive_sha256 -ne $ExpectedQaArchiveSha -or
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
$app=Join-Path $work 'app'
$matrixDirectory=Join-Path $work 'matrix'
$descriptor=@{context=$c;versions=@{java=0;node=0;postgres=0};source_clean=$false;
 frontend_exit=1;build_exit=1;full_maven_exit=1;rc03_exit=1;operator_exit=1;
 frontend_log=(Join-Path $work 'frontend.log');search_xml='';roles_xml='';rls_xml='';
 full_maven_reports=@();phase_a_xml='';phase_b_xml='';rc03_summary='';
 rc03_log='';rc03_logs=@();runtime_home='';runtime_sha256='';
 matrix_results_path=(Join-Path $matrixDirectory 'matrix-results.json');matrix_execution_run_id='';matrix_report_paths=@();
 operator_xml='';operator_observation='';operator_summary='';postgres_observations=(Join-Path $work 'postgres-observations.jsonl')}
function Run-Private([string]$Log,[scriptblock]$Command){
 & $Command *> $Log
 return [int]$LASTEXITCODE
}
# This artifact is authored outside execution code. Protected workflow pins are
# assertions from the reviewed control plane; JSON cannot authenticate itself.
function Read-ExecutionAuthorization {
 if(-not $env:WIN11P_EXECUTION_AUTHORIZATION_JSON -or
    $env:WIN11P_EXECUTION_AUTHORIZATION_SHA256 -notmatch '^[0-9a-f]{64}$' -or
    $env:WIN11P_AUTHORIZATION_VERIFIED_SHA256 -ne $env:WIN11P_EXECUTION_AUTHORIZATION_SHA256 -or
    $env:WIN11P_AUTHORIZATION_REQUEST_ID -ne $c.request_id){throw 'WIN11P protected execution authorization is missing'}
 $authorizationPath=Join-Path $work 'execution-authorization.json'
 [IO.File]::WriteAllText($authorizationPath,$env:WIN11P_EXECUTION_AUTHORIZATION_JSON,[Text.UTF8Encoding]::new($false))
 Assert-Hash $authorizationPath $env:WIN11P_EXECUTION_AUTHORIZATION_SHA256
 $authorization=Get-Content -LiteralPath $authorizationPath -Raw | ConvertFrom-Json
 if($authorization.source_sha -ne $c.source_sha -or $authorization.qa_sha -ne $c.qa_sha -or
    $authorization.request_id -ne $c.request_id -or $authorization.plan_id -ne $c.plan_id -or
    $authorization.disposition -ne 'APPROVED_FOR_EXECUTION' -or $authorization.reviewer -ne $c.reviewer -or
    $authorization.review_url -notmatch '^https://github.com/ARG-Digital-Solutions/aronexa-qa-central/(?:pull|issues)/[1-9][0-9]*(?:#[A-Za-z0-9-]+)?$'){
  throw 'WIN11P reviewed execution authorization identity mismatch'
 }
 $allowed=@('source_sha','qa_sha','request_id','plan_id','reviewer','review_url','disposition','lanes')
 foreach($property in $authorization.PSObject.Properties){if($property.Name -notin $allowed){throw 'WIN11P unauthorized authorization field'}}
 foreach($lane in @($authorization.lanes)){
  foreach($property in $lane.PSObject.Properties){
   if($property.Name -notin @('id','operator','acknowledged_at','authorization_url','environment','java_home','preview_port')){throw 'WIN11P unauthorized lane authorization field'}
  }
  if($lane.PSObject.Properties['operator'] -and $lane.operator -ne $c.operator){throw 'WIN11P lane operator is not independently reviewed'}
 }
 # An operator may prepare this one source-bound fictional lab before the job.
 # Refuse every stale/extra lab; execution never creates its consent marker.
 $operatorRoot=Join-Path $env:LOCALAPPDATA 'ARG-Digital\AroNexa-Pilot09-Disposable'
 $operatorLanes=@($authorization.lanes | Where-Object {$_.id -eq 'pilot09-operator'})
 if($operatorLanes.Count -gt 1){throw 'WIN11P duplicate operator lab authorization'}
 if(Test-Path -LiteralPath $operatorRoot){
  $root=Get-Item -LiteralPath $operatorRoot
  $labs=@(Get-ChildItem -LiteralPath $operatorRoot -Force)
  if(-not $root.PSIsContainer -or ($root.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
     $operatorLanes.Count -ne 1 -or $labs.Count -ne 1 -or -not $labs[0].PSIsContainer -or
     ($labs[0].Attributes -band [IO.FileAttributes]::ReparsePoint) -or $labs[0].Name -notmatch '^pilot09-[0-9a-f]{32}$' -or
     [IO.Path]::GetFullPath([string]$operatorLanes[0].environment.ARONEXA_PILOT09_RUN_DIR) -ne $labs[0].FullName){
   throw 'WIN11P refuses stale or unreviewed operator labs'
  }
  $marker=Get-Item -LiteralPath (Join-Path $labs[0].FullName 'LAB-TEST-ONLY.marker')
  if($marker.PSIsContainer -or $marker.Length -gt 512 -or ($marker.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
     (Get-Content -LiteralPath $marker.FullName -Raw).TrimEnd("`r","`n") -cne ('FICTIONAL_DISPOSABLE_ONLY_SOURCE_SHA='+$c.source_sha) -or
     (Test-Path -LiteralPath (Join-Path $labs[0].FullName 'STOP'))){throw 'WIN11P operator lab source marker is invalid'}
 }elseif($operatorLanes.Count -ne 0){throw 'WIN11P reviewed operator lab is absent'}
 [Environment]::SetEnvironmentVariable('WIN11P_EXECUTION_AUTHORIZATION_JSON',$null,'Process')
 return $authorizationPath
}
function Read-MatrixProjections {
 if(-not(Test-Path -LiteralPath $descriptor.matrix_results_path -PathType Leaf)){return}
 $matrix=Get-Content -LiteralPath $descriptor.matrix_results_path -Raw | ConvertFrom-Json
 if($matrix.run_id -notmatch '^[0-9a-f]{32}$' -or $matrix.source_sha -ne $c.source_sha -or $matrix.request_id -ne $c.request_id){throw 'WIN11P matrix identity mismatch'}
 $descriptor.matrix_execution_run_id=$matrix.run_id
 $reportsRoot=Join-Path $app ('backend\target\win11p-reports\'+$matrix.run_id)
 $lanes=@('discovery','ordinary','pilot05-phase-a','pilot05-phase-b','pilot05-rc03-phase-a','pilot05-rc03-phase-b','pilot06-browser','pilot07-recovery','pilot07-operator','pilot09-operator')
 foreach($lane in $lanes){
  $folder=Join-Path $reportsRoot $lane
  $paths=@()
  if(Test-Path -LiteralPath $folder -PathType Container){
   $paths=@(Get-ChildItem -LiteralPath $folder -Filter 'TEST-*.xml' -File | ForEach-Object {$_.FullName})
  }
  $descriptor.matrix_report_paths+=@(@{lane=$lane;paths=$paths})
  $descriptor.full_maven_reports+=@($paths)
 }
 # Security subsets project ordinary results and do not add to the matrix total.
 $ordinary=Join-Path $reportsRoot 'ordinary'
 $descriptor.search_xml=Join-Path $ordinary 'TEST-com.argdigital.aronexa.patient.PatientCandidateSearchHttpAcceptanceTests.xml'
 $descriptor.roles_xml=Join-Path $ordinary 'TEST-com.argdigital.aronexa.auth.AuthRoleBoundaryTests.xml'
 $descriptor.rls_xml=Join-Path $ordinary 'TEST-com.argdigital.aronexa.auth.PostgresTenantRlsTests.xml'
 $phaseReport='TEST-com.argdigital.aronexa.appointment.Pilot05SeparateJvmHttpTests.xml'
 $descriptor.phase_a_xml=Join-Path (Join-Path $reportsRoot 'pilot05-rc03-phase-a') $phaseReport
 $descriptor.phase_b_xml=Join-Path (Join-Path $reportsRoot 'pilot05-rc03-phase-b') $phaseReport
 $descriptor.rc03_logs=@((Join-Path $matrixDirectory 'pilot05-rc03-phase-a.log'),(Join-Path $matrixDirectory 'pilot05-rc03-phase-b.log'))
 $rc03=@($matrix.lane_results | Where-Object {$_.lane -in @('pilot05-rc03-phase-a','pilot05-rc03-phase-b')})
 if($rc03.Count -eq 2 -and @($rc03 | Where-Object {$null -eq $_.exit_code -or $_.exit_code -ne 0}).Count -eq 0){$descriptor.rc03_exit=0}
 $descriptor.operator_xml=Join-Path (Join-Path $reportsRoot 'pilot09-operator') $phaseReport
 $operator=@($matrix.lane_results | Where-Object {$_.lane -eq 'pilot09-operator'})
 if($operator.Count -eq 1){
  if($null -ne $operator[0].exit_code){$descriptor.operator_exit=[int]$operator[0].exit_code}
  if($operator[0].PSObject.Properties['operator_run_directory'] -and $operator[0].operator_run_directory){
   $root=[IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'ARG-Digital\AroNexa-Pilot09-Disposable'))
   $folder=[IO.Path]::GetFullPath([string]$operator[0].operator_run_directory)
   if((Split-Path $folder -Parent) -ne $root -or (Split-Path $folder -Leaf) -notmatch '^pilot09-[0-9a-f]{32}$'){throw 'WIN11P unexpected operator observation path'}
   $descriptor.operator_observation=Join-Path $folder 'SESSION-OBSERVATION.txt'
  }
 }
}
$observerStop=Join-Path $work 'observer.stop'
$observer=$null
$collectorExit=1
try {
 foreach($p in @(5176,5186)){
  $probe=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,$p)
  try{$probe.Start()}finally{$probe.Stop()}
 }
 $authorizationPath=Read-ExecutionAuthorization
 Expand-Archive -LiteralPath (Join-Path $inputRoot 'qa.zip') -DestinationPath $qa
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
 $descriptor.versions.java=21
 $descriptor.versions.node=24
 $dockerType=(& docker.exe info --format '{{.OSType}}')
 if($LASTEXITCODE -ne 0 -or $dockerType -ne 'linux'){throw 'WIN11P isolated Linux-container Docker required'}
 $containers=@(& docker.exe ps -aq)
 if($LASTEXITCODE -ne 0 -or $containers.Count -ne 0){throw 'WIN11P Docker is not a fresh isolated engine'}
 $observer=Start-Job -FilePath (Join-Path $qa 'scripts\Observe-Win11pPostgres.ps1') -ArgumentList $descriptor.postgres_observations,$observerStop,(Get-Command docker.exe).Source,$c.request_id,$c.source_sha
 $install=Run-Private (Join-Path $work 'qa-install.log') { & npm.cmd --prefix $qa ci --no-audit --no-fund }
 if($install -ne 0){throw 'WIN11P QA dependency installation failed'}
 Push-Location $qa
 try{$install=Run-Private (Join-Path $work 'playwright-install.log') { & node.exe node_modules/playwright/cli.js install chromium }}finally{Pop-Location}
 if($install -ne 0){throw 'WIN11P Playwright installation failed'}
 $install=Run-Private (Join-Path $work 'app-install.log') { & npm.cmd --prefix (Join-Path $app 'frontend') ci --no-audit --no-fund }
 if($install -ne 0){throw 'WIN11P application dependency installation failed'}
 $descriptor.frontend_exit=Run-Private $descriptor.frontend_log { & npm.cmd --prefix (Join-Path $app 'frontend') test }
 $descriptor.build_exit=Run-Private (Join-Path $work 'build.log') { & npm.cmd --prefix (Join-Path $app 'frontend') run build:connected:test }
 $runtime=Join-Path $work 'portable-java21'
 $link=Run-Private (Join-Path $work 'jlink.log') {
  & (Join-Path $env:JAVA_HOME 'bin\jlink.exe') --module-path (Join-Path $env:JAVA_HOME 'jmods') --add-modules ALL-MODULE-PATH --strip-debug --no-header-files --no-man-pages --output $runtime
 }
 if($link -ne 0){throw 'WIN11P portable runtime build failed'}
 $descriptor.runtime_home=$runtime
 $descriptor.runtime_sha256=(& python.exe -c 'import sys;sys.path.insert(0,sys.argv[1]);from win11p_collect import runtime_hash;print(runtime_hash(sys.argv[2]))' $PSScriptRoot $runtime).Trim()
 if($LASTEXITCODE -ne 0){throw 'WIN11P runtime inventory failed'}
 $env:WIN11P_PORTABLE_JAVA_HOME=$runtime
 $env:WIN11P_QA_CENTRAL_PATH=$qa
 $env:WIN11P_QA_SHA=$c.qa_sha
 Write-Output 'WIN11P operator: use the approved VM console and private fictional staff sheet; complete Reception, then STOP. No patient data.'
 # Exactly one coordinator owns every mandatory Maven method and all guarded
 # resources. Operator acknowledgements come only from the reviewed artifact.
 $descriptor.full_maven_exit=Run-Private (Join-Path $work 'matrix-private.log') {
  & powershell.exe -NoProfile -File (Join-Path $app 'scripts\pilot\Invoke-Win11p-MavenMatrix.ps1') -ExpectedCommit $c.source_sha -Mode All -EvidenceDirectory $matrixDirectory -AuthorizationPath $authorizationPath -AuthorizationSha256 $env:WIN11P_EXECUTION_AUTHORIZATION_SHA256 -RequestId $c.request_id
 }
} catch {
 Write-Warning 'WIN11P incomplete required stage; private diagnostics retained only until VM destruction'
} finally {
 [Environment]::SetEnvironmentVariable('WIN11P_EXECUTION_AUTHORIZATION_JSON',$null,'Process')
 [Environment]::SetEnvironmentVariable('WIN11P_PORTABLE_JAVA_HOME',$null,'Process')
 [Environment]::SetEnvironmentVariable('WIN11P_QA_CENTRAL_PATH',$null,'Process')
 [Environment]::SetEnvironmentVariable('WIN11P_QA_SHA',$null,'Process')
 try{
  [IO.File]::WriteAllText($observerStop,'STOP')
  if($null -ne $observer){Stop-Job -Job $observer; Remove-Job -Job $observer}
 }catch{Write-Warning 'WIN11P observer finalization incomplete'}
 try{Read-MatrixProjections}catch{Write-Warning 'WIN11P matrix projections incomplete'}
 try{
  if(Test-Path -LiteralPath (Join-Path $app '.git')){
   $head=@(& git -C $app rev-parse HEAD)
   $headExit=$LASTEXITCODE
   $dirty=@(& git -C $app status --porcelain --untracked-files=no)
   $descriptor.source_clean=($headExit -eq 0 -and $LASTEXITCODE -eq 0 -and $head.Count -eq 1 -and
    $head[0].Trim() -eq $c.source_sha -and $dirty.Count -eq 0)
  }
 }catch{$descriptor.source_clean=$false}
 $privateDescriptor=Join-Path $work 'collector-private.json'
 [IO.File]::WriteAllText($privateDescriptor,($descriptor | ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
 try{
  & python.exe (Join-Path $PSScriptRoot 'win11p_collect.py') --descriptor $privateDescriptor --output (Join-Path $public 'evidence.json')
  $collectorExit=$LASTEXITCODE
 }catch{Write-Warning 'WIN11P collector unavailable; required evidence did not pass'}
 if(-not(Test-Path -LiteralPath (Join-Path $public 'evidence.json') -PathType Leaf)){
  # This incomplete sanitized failure record is deliberately rejected by the
  # strict reporter. Never substitute absent test, JVM or operator observations.
  $failure=@{schema_version=2;plan_id=$c.plan_id;source_sha=$c.source_sha;qa_sha=$c.qa_sha;request_id=$c.request_id;run_id=$c.run_id;run_attempt=$c.run_attempt;classification='NOT_READY';release_authorized=$false}
  [IO.File]::WriteAllText((Join-Path $public 'evidence.json'),($failure|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
 }
}
if($collectorExit -ne 0){throw 'WIN11P required execution evidence failed; no Central PASS'}
Write-Output 'WIN11P sanitized execution complete; independent receipts and reporter approval required'
