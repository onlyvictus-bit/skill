param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
$mrRepo = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git'
$mrController = 'C:\Python314\python.exe'
$mrHelper = Join-Path $mrRepo '.github\scripts\cleanup_membership_diagnostic.py'
$mrContract = Join-Path $mrRepo '.github\run-artifacts\cleanup-membership-20261025\Inputs.json'
$mrContractSha = '457fc256b81f52572695b787344cd5778f3bd06bdc14939b5416508ceeacf5a4'
$mrPairs = @(
    @($mrHelper,'2c87f117bf38c13e50aa939a5f6b2b3ad163c0dae0de9ab8da9524390def1656'),
    @((Join-Path $mrRepo '.github\scripts\cleanup_membership_probe.py'),'7598e119a279214b1b49fcbc7db1c355fbb311821b7a4dffcd23fd1b0cffe43d'),
    @((Join-Path $mrRepo '.github\scripts\cleanup_timing_diagnostic.py'),'883ec3cda3ab7b6120f417cc79b0bee6d14b2fd6407cb9683491189c23ab3554'),
    @($mrContract,$mrContractSha),
    @($mrController,'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b')
)
foreach ($mrPair in $mrPairs) {
    if ($mrPair[1] -cnotmatch '^[0-9a-f]{64}$') { throw 'Membership runtime is not frozen. Stop.' }
    $mrItem = Get-Item -LiteralPath $mrPair[0] -Force
    while ($null -ne $mrItem) {
        if (($mrItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Redirected membership input. Stop.' }
        if ($mrItem -is [IO.FileInfo]) { $mrItem = $mrItem.Directory } else { $mrItem = $mrItem.Parent }
    }
    if ((Get-FileHash -LiteralPath $mrPair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -cne $mrPair[1]) {
        throw "Membership input changed. Stop: $($mrPair[0])"
    }
}
if ($VerifyOnly) { Write-Output 'MP1_RUNTIME_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT'; return }
$mrIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$mrPrincipal = New-Object Security.Principal.WindowsPrincipal($mrIdentity)
if ($mrIdentity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001' -or
    $mrPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Normal non-administrator account required; no membership attempt started.'
}
if (Test-Path -LiteralPath (Join-Path ([IO.Path]::GetDirectoryName($mrContract)) 'normal-membership')) {
    throw 'Existing membership attempt retained. Do not retry, remove or rename it.'
}
Write-Output 'ONE NEW MP1 process-membership diagnostic; not old TC1, stack, CR3, C2 or stage qualification.'
Write-Output 'Identity/dependency checks and full old/private guards precede ONE focused fixture claim.'
Write-Output 'Same frozen source, selected Python3.12, request0.1/shutdown5/watchdog60/default120; no budget changes.'
Write-Output 'Records launcher/relay/child membership and native exits before bounded fixture-only emergency cleanup.'
Write-Output 'No retrieval, package install/download, security change, Git action, deletion or automatic retry.'
& $mrController -B $mrHelper --sha256 $mrContractSha
if ($LASTEXITCODE -ne 0) { throw 'MP1 stopped/failed. Preserve Receipt.json and probe output; no retry, fallback or guard change.' }
Write-Output 'Membership observation captured, NOT a fix or completed stage. Share Receipt.json and probe/Probe.json.'
