# Read-only observer: exact source-owned pilot markers on a fresh VM engine only.
param([string]$EvidencePath,[string]$StopFile,[string]$DockerPath,
 [ValidatePattern('^[1-9][0-9]*-[1-9][0-9]*$')][string]$RequestId,
 [ValidatePattern('^[0-9a-f]{40}$')][string]$SourceSha)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(-not $RequestId -or -not $SourceSha){throw 'WIN11P observer requires exact request and source identity'}
$seen=@{}
$end=[DateTime]::UtcNow.AddMinutes(175)
while([DateTime]::UtcNow -lt $end -and -not(Test-Path -LiteralPath $StopFile)){
 $ids=@(& $DockerPath ps -q --filter ('label=com.argdigital.aronexa.win11p.request='+$RequestId) --filter ('label=com.argdigital.aronexa.win11p.source='+$SourceSha) 2>$null)
 foreach($id in $ids){
  if($id -notmatch '^[0-9a-f]{12,64}$'){continue}
  try{
   $raw=@(& $DockerPath inspect $id 2>$null)
   if($LASTEXITCODE -ne 0){continue}
   $items=@(ConvertFrom-Json ($raw -join ''))
   if($items.Count -ne 1){continue}
   $item=$items[0]
   $request=$item.Config.Labels.PSObject.Properties['com.argdigital.aronexa.win11p.request']
   $source=$item.Config.Labels.PSObject.Properties['com.argdigital.aronexa.win11p.source']
   $purpose=$item.Config.Labels.PSObject.Properties['com.argdigital.aronexa.win11p.purpose']
   if($null -eq $request -or $request.Value -ne $RequestId -or $null -eq $source -or $source.Value -ne $SourceSha -or
      $null -eq $purpose -or $purpose.Value -notin @('legacy','rc03','operator')){continue}
   $label=$item.Config.Labels.PSObject.Properties['com.argdigital.aronexa.pilot05.run']
   if($null -eq $label -or $label.Value -notmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'){continue}
   $run=$label.Value
   if($seen.ContainsKey($run)){continue}
   if($item.Name -ne ('/aronexa-win11p-'+$purpose.Value+'-'+$run.Replace('-','')) -or $item.Id -notmatch '^[0-9a-f]{64}$' -or
      $item.Image -notmatch '^sha256:[0-9a-f]{64}$' -or
      $item.Config.Image -ne 'postgres:17-alpine'){continue}
   $binding=@($item.NetworkSettings.Ports.PSObject.Properties['5432/tcp'].Value)
   if($binding.Count -ne 1 -or $binding[0].HostIp -ne '127.0.0.1' -or
      $binding[0].HostPort -notmatch '^[0-9]{4,5}$' -or [int]$binding[0].HostPort -lt 1024 -or
      [int]$binding[0].HostPort -gt 65535 -or $binding[0].HostPort -eq '5433'){continue}
   $sql="SELECT current_setting('server_version_num') FROM qa_guard.pilot05_run_marker WHERE run_id='$run' AND database_name='aronexa_pilot05_disposable_only'"
   $version=@(& $DockerPath exec $item.Id psql -X -U aronexa_pilot05_temporary -d aronexa_pilot05_disposable_only -t -A -c $sql 2>$null)
   if($LASTEXITCODE -ne 0 -or $version.Count -ne 1 -or $version[0].Trim() -notmatch '^17[0-9]{4}$'){continue}
   $record=@{run_id=$run;version_num=[int]$version[0].Trim();container_id=$item.Id;image_id=$item.Image;database_name='aronexa_pilot05_disposable_only';loopback=$true}
   [IO.File]::AppendAllText($EvidencePath,(($record|ConvertTo-Json -Compress)+[Environment]::NewLine),[Text.UTF8Encoding]::new($false))
   $seen[$run]=$true
  }catch{
   # No raw errors or credentials emitted. Missing observation blocks collection.
  }
 }
 Start-Sleep -Seconds 1
}
