param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
$mpRepo = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git'
$mpController = 'C:\Python314\python.exe'
$mpHelper = Join-Path $mpRepo '.github\scripts\cleanup_membership_diagnostic.py'
$mpPairs = @(
    @($mpHelper,'2c87f117bf38c13e50aa939a5f6b2b3ad163c0dae0de9ab8da9524390def1656'),
    @((Join-Path $mpRepo '.github\scripts\cleanup_membership_probe.py'),'7598e119a279214b1b49fcbc7db1c355fbb311821b7a4dffcd23fd1b0cffe43d'),
    @((Join-Path $mpRepo '.github\scripts\cleanup_timing_diagnostic.py'),'883ec3cda3ab7b6120f417cc79b0bee6d14b2fd6407cb9683491189c23ab3554'),
    @($mpController,'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b')
)
foreach ($mpPair in $mpPairs) {
    if ($mpPair[1] -cnotmatch '^[0-9a-f]{64}$') { throw 'Membership preparation is not frozen. Stop.' }
    $mpItem = Get-Item -LiteralPath $mpPair[0] -Force
    while ($null -ne $mpItem) {
        if (($mpItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Redirected membership input. Stop.' }
        if ($mpItem -is [IO.FileInfo]) { $mpItem = $mpItem.Directory } else { $mpItem = $mpItem.Parent }
    }
    if ((Get-FileHash -LiteralPath $mpPair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -cne $mpPair[1]) {
        throw "Membership input changed. Stop: $($mpPair[0])"
    }
}
if ($VerifyOnly) { Write-Output 'MP1_PREPARATION_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT'; return }
$mpIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$mpPrincipal = New-Object Security.Principal.WindowsPrincipal($mpIdentity)
if ($mpIdentity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001' -or
    $mpPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Normal non-administrator account required. Nothing started.'
}
if (Test-Path -LiteralPath (Join-Path $mpRepo '.github\run-artifacts\cleanup-membership-20261025')) {
    throw 'Existing preparation retained. No retry, remove, rename or precreation.'
}
Write-Output 'MP1 INPUT PREPARATION ONLY: read/hash consumed TC1, old histories, source and runtime metadata.'
Write-Output 'Only NEW Inputs.json is created. No Python3.12, membership fixture, test or workload attempt runs.'
Write-Output 'No package install, permission change, Git action or deletion. Inaccessible required input means stop.'
& $mpController -B $mpHelper --prepare
if ($LASTEXITCODE -ne 0) { throw 'MP1 preparation failed. Preserve/share output; no retry or guard change.' }
Write-Output 'Share contract path, size and SHA. Membership runtime launcher is NOT frozen or issued by this preparation.'
