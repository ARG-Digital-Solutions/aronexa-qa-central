# QA Central operator launcher — P01-T07-INT-REG01
# Runs remote QA Central GitHub Actions only. No local build, Docker or DB access.
# Requires QA Central workflow qa-int-reg01.yml on default branch after approved merge.
[CmdletBinding()]
param(
    [string]$ProductSha = '8788b89ddceb70c085818939a82c3476887006bd',
    [string]$FrontendSha = '52809efbc077cd6abb6860d870cc487cc8eddc42'
)
$ErrorActionPreference = 'Stop'

$qaRepo = 'ARG-Digital-Solutions/aronexa-qa-central'
$appRepo = 'ARG-Digital-Solutions/aronexa-healthcare-platform'
$workflow = 'qa-int-reg01.yml'
$sourceBranch = 'codex/p01-t07-int-reg01-contract-20261109'
$approvedProductSha = '8788b89ddceb70c085818939a82c3476887006bd'
$approvedFrontendSha = '52809efbc077cd6abb6860d870cc487cc8eddc42'

function Invoke-Gh([string[]]$Arguments) {
    $value = & gh @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub CLI failed: $($Arguments -join ' '): $($value | Out-String)"
    }
    return ($value | Out-String).Trim()
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'Install GitHub CLI and authenticate with gh auth login before running QA.'
}
& gh auth status --hostname github.com *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'GitHub authentication missing. Run gh auth login.'
}
if ($ProductSha -cne $approvedProductSha -or $FrontendSha -cne $approvedFrontendSha) {
    throw 'Blocked: SHA differs from P01-T07-INT-REG01 owner-reviewed pins. Separate review required.'
}

$actualSha = Invoke-Gh @('api', "repos/$appRepo/git/ref/heads/$sourceBranch", '--jq', '.object.sha')
if ($actualSha -cne $ProductSha) {
    throw "Stopped: product branch moved. Expected $ProductSha; actual $actualSha. Re-review before dispatch."
}

# GitHub only registers workflow_dispatch workflows present on the QA default branch.
$workflowApiPath = "repos/$qaRepo/contents/.github/workflows/" + $workflow + '?ref=main'
try {
    $null = Invoke-Gh @('api', $workflowApiPath, '--jq', '.path')
} catch {
    throw "QA Central workflow is not on main yet. Review and separately authorize QA Central PR #5 before running. $($_.Exception.Message)"
}

$priorText = Invoke-Gh @('run','list','--repo',$qaRepo,'--workflow',$workflow,
    '--event','workflow_dispatch','--limit','50','--json','databaseId')
$prior = @($priorText | ConvertFrom-Json | ForEach-Object { $_.databaseId })

Invoke-Gh @('workflow','run',$workflow,'--repo',$qaRepo,'--ref','main',
    '-f',"backend_sha=$ProductSha",'-f',"frontend_sha=$FrontendSha",
    '-f','acknowledge_disposable_only=true') | Write-Host

$run = $null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 3
    $raw = Invoke-Gh @('run','list','--repo',$qaRepo,'--workflow',$workflow,
        '--event','workflow_dispatch','--limit','50',
        '--json','databaseId,headSha,createdAt,status,conclusion,url')
    $items = @($raw | ConvertFrom-Json)
    $run = $items | Where-Object { $_.databaseId -notin $prior } |
        Sort-Object -Property databaseId -Descending | Select-Object -First 1
    if ($null -ne $run) { break }
}
if ($null -eq $run) {
    throw 'Run dispatched but not located: inspect GitHub Actions; do not blindly retry.'
}
Write-Host "QA Central run: $($run.url)"

& gh run watch "$($run.databaseId)" --repo $qaRepo --exit-status
$watchExit = $LASTEXITCODE

$details = Invoke-Gh @('run','view',"$($run.databaseId)",'--repo',$qaRepo,
    '--json','databaseId,status,conclusion,headSha,createdAt,updatedAt,url,jobs')
$data = $details | ConvertFrom-Json

$jobs = @($data.jobs | ForEach-Object {
    [ordered]@{name=$_.name;status=$_.status;conclusion=$_.conclusion;url=$_.url}
})
$success = $watchExit -eq 0 -and $data.conclusion -eq 'success' -and
    @($jobs | Where-Object { $_.conclusion -ne 'success' }).Count -eq 0 -and
    @($jobs | Where-Object { $_.name -match 'Backend full regression' }).Count -eq 1 -and
    @($jobs | Where-Object { $_.name -match 'Independent frozen' }).Count -eq 1

$report = [ordered]@{
    task = 'P01-T07-INT-REG01'
    repository = $qaRepo
    applicationRepository = $appRepo
    applicationSha = $ProductSha
    frozenFrontendSha = $FrontendSha
    qaWorkflowSha = $data.headSha
    githubRunUrl = $data.url
    status = $data.status
    conclusion = $data.conclusion
    jobs = $jobs
    pipelinePass = [bool]$success
    independentSecurityReview = 'PENDING'
    releaseReady = $false
    collectedAtUtc = [DateTime]::UtcNow.ToString('o')
}
$path = Join-Path (Split-Path -Parent $PSScriptRoot) 'artifacts/int-reg01/P01_T07_INT_REG01_QA_EVIDENCE.json'
New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force | Out-Null
$report | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $path -Encoding utf8
Write-Host "QA evidence written to: $path"
if (-not $success) {
    throw "QA is NOT PASS. Inspect $($data.url) and its per-job logs."
}
Write-Host "Isolated QA jobs succeeded. Independent security review, merged product changes and release remain separate owner gates."
