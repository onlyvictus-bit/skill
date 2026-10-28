param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'

# THIS launcher is deliberately BEFORE/INPUT-ONLY. No runtime phase is chained.
$scRepo = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git'
$scRoot = 'C:\Users\sakth\Documents\Codex\sr3-copy-20261027-4a52cd8d'
$scController = 'C:\Python314\python.exe'
$scHelper = Join-Path $scRepo '.github\scripts\shutdown_copy_verification.py'
$scData = Join-Path $scRepo '.github\scripts\shutdown_copy_data.py'
$scHelperSha = '234dd24e90a33feeee9fbacd5e75f03b2099c8393b7be86d3d9f994d99946cd3'
$scDataSha = '4fa0afdaa1219b243421717eca9a8d2939c4f653a8d9b27110e2b63c80e27299'
$scControllerSha = 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'

function Test-ScOrdinary([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    while ($null -ne $item) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Redirected SC input: $Path"
        }
        if ($item -is [IO.FileInfo]) { $item = $item.Directory } else { $item = $item.Parent }
    }
}
function Test-ScSeals {
    foreach ($pair in @(@($scHelper,$scHelperSha),@($scData,$scDataSha),@($scController,$scControllerSha))) {
        if ($pair[1] -cnotmatch '^[0-9a-f]{64}$') { throw 'SC handoff is not frozen. Do not run.' }
        Test-ScOrdinary $pair[0]
        if ((Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -cne $pair[1]) {
            throw "SC sealed input changed: $($pair[0])"
        }
    }
}
Test-ScSeals
if ($VerifyOnly) { Write-Output 'SC_BEFORE_EXTERNAL_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT'; return }
$scIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$scPrincipal = New-Object Security.Principal.WindowsPrincipal($scIdentity)
if ($scIdentity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001' -or
    $scPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Normal non-administrator account required. No SC attempt started.'
}
if (Test-Path -LiteralPath $scRoot) { throw 'SC session already exists. Preserve output; do not retry.' }
Write-Output 'SC BEFORE INPUTS ONLY: original source/runtime/helper checks, then readable/denied evidence request.'
Write-Output 'Existing-access copy/readback is next; NO Python3.12, shutdown test, retrieval or workload runs now.'
Write-Output 'No ACL change, reinstall, security change, Git write, original deletion or automatic retry.'
Test-ScSeals
& $scController -B $scHelper --mode Before
if ($LASTEXITCODE -ne 0) { throw 'SC BEFORE stopped. Preserve/share output and Before-Failure.json. Do not retry.' }
Write-Output 'Share Inputs.json and BEFORE Request.json path/size/SHA. Do not run old SR3 or any runtime command.'
