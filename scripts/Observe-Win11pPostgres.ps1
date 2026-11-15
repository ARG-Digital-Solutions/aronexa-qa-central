# Read-only observer: exact source-owned pilot markers on a fresh VM engine only.
param([string]$EvidencePath,[string]$StopFile,[string]$DockerPath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$seen=@{}
$end=[DateTime]::UtcNow.AddMinutes(175)
while([DateTime]::UtcNow -lt $end -and -not(Test-Path -LiteralPath $StopFile)){
 $ids=@(& $DockerPath ps -q --filter 'label=com.argdigital.aronexa.pilot05.run' 2>$null)
 foreach($id in $ids){
  if($id -notmatch '^[0-9a-f]{12,64}$'){continue}
  try{
   $raw=@(& $DockerPath inspect $id 2>$null)
   if($LASTEXITCODE -ne 0){continue}
   $items=@(ConvertFrom-Json ($raw -join ''))
   if($items.Count -ne 1){continue}
   $item=$items[0]
   $label=$item.Config.Labels.PSObject.Properties['com.argdigital.aronexa.pilot05.run']
   if($null -eq $label -or $label.Value -notmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'){continue}
   $run=$label.Value
   if($seen.ContainsKey($run)){continue}
   if($item.Name -ne ('/aronexa-pilot05-'+$run.Substring(0,12)) -or $item.Id -notmatch '^[0-9a-f]{64}$'){continue}
   $binding=@($item.NetworkSettings.Ports.PSObject.Properties['5432/tcp'].Value)
   if($binding.Count -ne 1 -or $binding[0].HostIp -ne '127.0.0.1' -or
      $binding[0].HostPort -notmatch '^[0-9]{4,5}$' -or $binding[0].HostPort -eq '5433'){continue}
   $sql="SELECT current_setting('server_version_num') FROM qa_guard.pilot05_run_marker WHERE run_id='$run' AND database_name='aronexa_pilot05_disposable_only'"
   $version=@(& $DockerPath exec $item.Id psql -X -U aronexa_pilot05_temporary -d aronexa_pilot05_disposable_only -t -A -c $sql 2>$null)
   if($LASTEXITCODE -ne 0 -or $version.Count -ne 1 -or $version[0].Trim() -notmatch '^[0-9]{6}$'){continue}
   $record=@{run_id=$run;version_num=[int]$version[0].Trim();container_id=$item.Id;database_name='aronexa_pilot05_disposable_only';loopback=$true}
   [IO.File]::AppendAllText($EvidencePath,(($record|ConvertTo-Json -Compress)+[Environment]::NewLine),[Text.UTF8Encoding]::new($false))
   $seen[$run]=$true
  }catch{
   # No raw errors or credentials emitted. Missing observation blocks collection.
  }
 }
 Start-Sleep -Seconds 1
}
