param(
    [ValidateSet('Before','VerifyBefore','Run','After','Finalize')]
    [string]$Mode = 'Before',
    [string]$InputSha256,
    [string]$BeforeSha256,
    [switch]$VerifyOnly
)
$ErrorActionPreference = 'Stop'
$h1Root = 'C:\Users\sakth\Documents\Codex\w-h1-20261022-80b78d91'
$h1Config = Join-Path $h1Root 'Input-Seal.json'
$h1ConfigSha = '623a78c6a9226527b24b418cc70bf55377b6607e9de331488d88ced298b02b8a'
$h1Helper = Join-Path $PSScriptRoot 'worker_copy_h1.py'
function Assert-H1PlainFile([string]$Path) {
    $h1Item = Get-Item -LiteralPath $Path -Force
    if ($h1Item.PSIsContainer -or $h1Item.LinkType -or
        ($h1Item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw ('H1 trusted input is not an ordinary single-link file: ' + $Path)
    }
    $h1Parent = $h1Item.Directory
    while ($null -ne $h1Parent) {
        if ($h1Parent.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw ('H1 redirected ancestor rejected: ' + $h1Parent.FullName)
        }
        $h1Parent = $h1Parent.Parent
    }
}
Assert-H1PlainFile $h1Config
if ((Get-FileHash -LiteralPath $h1Config -Algorithm SHA256).Hash.ToLowerInvariant() -cne $h1ConfigSha) {
    throw 'H1 external configuration seal changed. Stop.'
}
$h1Doc = Get-Content -LiteralPath $h1Config -Raw | ConvertFrom-Json
foreach ($h1Role in $h1Doc.files.PSObject.Properties) {
    Assert-H1PlainFile $h1Role.Name
    if ((Get-FileHash -LiteralPath $h1Role.Name -Algorithm SHA256).Hash.ToLowerInvariant() -cne $h1Role.Value.sha256) {
        throw ('H1 sealed input changed: ' + $h1Role.Name)
    }
}
if ($VerifyOnly) {
    Write-Output 'COPY_H1_EXTERNAL_SEALS_MATCH_NO_PYTHON_COPY_OR_ATTEMPT'
    return
}
$h1Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$h1Principal = [Security.Principal.WindowsPrincipal]::new($h1Identity)
if ($h1Identity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001' -or
    $h1Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use your normal non-administrator PowerShell only. No security/permission changes.'
}
Write-Output 'NEW COPY-H1 exact historical-DATA successor; never reuse old W-COPY commands.'
Write-Output 'No install/download, ACL/trust change, deletion, API/model/native database, Git action or skill install.'
if ($Mode -eq 'Before') {
    Write-Output 'Fresh BEFORE request only: original history readback, no data copies or numerical worker yet.'
}
$h1Args = @('-B',$h1Helper,'--mode',$Mode,'--config-sha256',$h1ConfigSha)
if ($InputSha256) { $h1Args += @('--input-sha256',$InputSha256) }
if ($BeforeSha256) { $h1Args += @('--before-sha256',$BeforeSha256) }
$h1PriorBytecode = $env:PYTHONDONTWRITEBYTECODE
$h1PriorSite = $env:PYTHONNOUSERSITE
try {
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:PYTHONNOUSERSITE = '1'
    & 'C:\Python314\python.exe' @h1Args
    $h1Exit = $LASTEXITCODE
} finally {
    $env:PYTHONDONTWRITEBYTECODE = $h1PriorBytecode
    $env:PYTHONNOUSERSITE = $h1PriorSite
}
if ($h1Exit -ne 0) { throw 'COPY-H1 stopped. Preserve all output; no rerun, marker removal or guard changes.' }
Write-Output 'Share the exact status/path/hash. This does not complete W, Gate1, release or installation.'
