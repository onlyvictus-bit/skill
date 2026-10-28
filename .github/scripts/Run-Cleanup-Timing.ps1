param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
$trRepo = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git'
$trHelper = Join-Path $trRepo '.github\scripts\cleanup_timing_diagnostic.py'
$trContract = Join-Path $trRepo '.github\run-artifacts\cleanup-process-timing-20261024\Inputs.json'
$trController = 'C:\Python314\python.exe'
$trContractSha = 'cf45dfde1fae5d2bb5f601a8d54c4fa68e62d5db35e3248ffe9bdfecf9476d62'
$trPairs = @(
    @($trHelper,'883ec3cda3ab7b6120f417cc79b0bee6d14b2fd6407cb9683491189c23ab3554'),
    @((Join-Path $trRepo '.github\scripts\cleanup_timing_observer.py'),'00ee0acf6dc4205fd2a853fb80fdc481772a19b71b8afc7c5e44fab2875f6473'),
    @((Join-Path $trRepo '.github\scripts\extended_timing_log.py'),'0b234e4988127d711e9183100bf47e13adefe772e5671bd5637535d2bdc4c87e'),
    @((Join-Path $trRepo '.github\scripts\worker_diagnostic_events.py'),'5e7d30538b296acb763972e6553e927309c7c8319a2670a651920f7c793a6a88'),
    @($trContract,$trContractSha),
    @($trController,'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b')
)
foreach ($trPair in $trPairs) {
    if ($trPair[1] -cnotmatch '^[0-9a-f]{64}$') { throw 'Timing diagnostic is not frozen. Stop.' }
    $trItem = Get-Item -LiteralPath $trPair[0] -Force
    while ($null -ne $trItem) {
        if (($trItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Redirected timing input. Stop.' }
        if ($trItem -is [IO.FileInfo]) { $trItem = $trItem.Directory } else { $trItem = $trItem.Parent }
    }
    if ((Get-FileHash -LiteralPath $trPair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -cne $trPair[1]) {
        throw "Timing input changed. Stop: $($trPair[0])"
    }
}
if ($VerifyOnly) { Write-Output 'TC1_RUNTIME_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT'; return }
$trIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$trPrincipal = New-Object Security.Principal.WindowsPrincipal($trIdentity)
if ($trIdentity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001' -or
    $trPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Normal non-administrator account required; no timing attempt started.'
}
if (Test-Path -LiteralPath (Join-Path ([IO.Path]::GetDirectoryName($trContract)) 'normal-timing')) {
    throw 'Existing timing attempt retained. Do not retry, remove or rename it.'
}
Write-Output 'ONE NEW process/stage timing diagnostic; not old stack, CR3, C2, N3 or stage qualification.'
Write-Output 'Same12 lifecycle cases; new diagnostic copy only. Request0.1/shutdown5/lifecycle-watchdog60/default120 unchanged.'
Write-Output 'Imports and installed metadata, data/serialization, process lineage, pipe write/flush, job/writer/cleanup timed separately.'
Write-Output 'Inclusive/parallel times are not totals. Missing END means unfinished/unknown. No package reinstall or timeout increase.'
Write-Output 'Full old/private input checks remain mandatory before and after; preserve all outputs. No automatic retry.'
Write-Output 'No retrieval, install/download, security change, Git action, deletion or model/native backend operation.'
& $trController -B $trHelper --sha256 $trContractSha
if ($LASTEXITCODE -ne 0) { throw 'TC1 stopped/failed. Preserve Receipt.json, Timings.json/Timings.md and stacks; do not retry or change guards.' }
Write-Output 'Timing capture finished, NOT a fix or completed stage. Share Receipt.json and Timings.md for result review.'
