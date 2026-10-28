param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
$tcRepo = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git'
$tcController = 'C:\Python314\python.exe'
$tcHelper = Join-Path $tcRepo '.github\scripts\cleanup_timing_diagnostic.py'
$tcPairs = @(
    @($tcHelper,'883ec3cda3ab7b6120f417cc79b0bee6d14b2fd6407cb9683491189c23ab3554'),
    @((Join-Path $tcRepo '.github\scripts\cleanup_timing_observer.py'),'00ee0acf6dc4205fd2a853fb80fdc481772a19b71b8afc7c5e44fab2875f6473'),
    @((Join-Path $tcRepo '.github\scripts\extended_timing_log.py'),'0b234e4988127d711e9183100bf47e13adefe772e5671bd5637535d2bdc4c87e'),
    @((Join-Path $tcRepo '.github\scripts\worker_diagnostic_events.py'),'5e7d30538b296acb763972e6553e927309c7c8319a2670a651920f7c793a6a88'),
    @($tcController,'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b')
)
foreach ($tcPair in $tcPairs) {
    if ($tcPair[1] -cnotmatch '^[0-9a-f]{64}$') { throw 'Timing preparation is not frozen. Stop.' }
    $tcItem = Get-Item -LiteralPath $tcPair[0] -Force
    while ($null -ne $tcItem) {
        if (($tcItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Redirected timing input. Stop.' }
        if ($tcItem -is [IO.FileInfo]) { $tcItem = $tcItem.Directory } else { $tcItem = $tcItem.Parent }
    }
    if ((Get-FileHash -LiteralPath $tcPair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -cne $tcPair[1]) {
        throw "Timing input changed. Stop: $($tcPair[0])"
    }
}
if ($VerifyOnly) { Write-Output 'TC1_PREPARATION_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT'; return }
$tcIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$tcPrincipal = New-Object Security.Principal.WindowsPrincipal($tcIdentity)
if ($tcIdentity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001' -or
    $tcPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Normal non-administrator account required. Nothing started.'
}
if (Test-Path -LiteralPath (Join-Path $tcRepo '.github\run-artifacts\cleanup-process-timing-20261024')) {
    throw 'Existing preparation retained. No retry, remove, rename or precreation.'
}
Write-Output 'TC1 INPUT PREPARATION ONLY: read/hash old source, failed CR3 and consumed stack attempt.'
Write-Output 'Only NEW Inputs.json is created. No selected Python3.12, test, timing workload or source copy runs.'
Write-Output 'No reinstall/download, security change, Git action or deletion. Stop on any inaccessible required input.'
& $tcController -B $tcHelper --prepare
if ($LASTEXITCODE -ne 0) { throw 'TC1 preparation failed. Preserve/share output; no retry or guard change.' }
Write-Output 'Share contract path, size and SHA. Timing runtime launcher is NOT frozen by this preparation.'
