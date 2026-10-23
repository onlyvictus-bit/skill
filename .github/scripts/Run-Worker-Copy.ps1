param(
    [ValidateSet('Before','VerifyBefore','Run','After','Finalize')]
    [string]$Mode = 'Before',
    [string]$InputSha256,
    [string]$BeforeSha256,
    [switch]$VerifyOnly
)
$ErrorActionPreference = 'Stop'
$wcRoot = 'C:\Users\sakth\Documents\Codex\w-copy-20261022-7b7f219a'
$wcConfig = Join-Path $wcRoot 'Input-Seal.json'
$wcConfigSha = '6cb2c070072e98dc5000ed7e3b4805da74b44b4fdd6cb293f637d2a5a5bb6288'
$wcHelper = Join-Path $PSScriptRoot 'worker_copy_successor.py'
if ((Get-FileHash -LiteralPath $wcConfig -Algorithm SHA256).Hash.ToLowerInvariant() -cne $wcConfigSha) {
    throw 'Copy successor configuration changed. Stop.'
}
$wcDoc = Get-Content -LiteralPath $wcConfig -Raw | ConvertFrom-Json
foreach ($wcRole in $wcDoc.files.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath $wcRole.Name -Algorithm SHA256).Hash.ToLowerInvariant() -cne $wcRole.Value.sha256) {
        throw ('Copy successor input changed. Stop: ' + $wcRole.Name)
    }
}
if ($VerifyOnly) {
    Write-Output 'W_COPY_EXTERNAL_SEALS_MATCH_NO_PYTHON_COPY_OR_ATTEMPT'
    return
}
$wcIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$wcPrincipal = [Security.Principal.WindowsPrincipal]::new($wcIdentity)
if ($wcIdentity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001' -or
    $wcPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use only your normal, non-administrator PowerShell. No permission or security changes.'
}
Write-Output 'NEW W-COPY cooperating-account successor; not an old W/N3/Gate1 command.'
Write-Output 'No install/download, ACL/trust change, old-data deletion, API/model/native backend, Git write or skill install.'
if ($Mode -eq 'Before') {
    Write-Output 'BEFORE inventory/request only. No selected Python 3.12 or diagnostic workload starts.'
}
$wcArgs = @('-B',$wcHelper,'--mode',$Mode,'--config-sha256',$wcConfigSha)
if ($InputSha256) { $wcArgs += @('--input-sha256',$InputSha256) }
if ($BeforeSha256) { $wcArgs += @('--before-sha256',$BeforeSha256) }
$wcPriorBytecode = $env:PYTHONDONTWRITEBYTECODE
$wcPriorSite = $env:PYTHONNOUSERSITE
try {
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:PYTHONNOUSERSITE = '1'
    & 'C:\Python314\python.exe' @wcArgs
    $wcExit = $LASTEXITCODE
} finally {
    $env:PYTHONDONTWRITEBYTECODE = $wcPriorBytecode
    $env:PYTHONNOUSERSITE = $wcPriorSite
}
if ($wcExit -ne 0) { throw 'Copy successor stopped. Keep all output; do not repeat or remove files/guards.' }
Write-Output 'Share printed status and hashes. No implicit next phase, retry or whole-skill qualification.'
