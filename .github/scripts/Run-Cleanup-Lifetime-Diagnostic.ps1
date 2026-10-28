param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
$ldRepo = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git'
$ldHelper = Join-Path $ldRepo '.github\scripts\cleanup_lifetime_diagnostic.py'
$ldContract = Join-Path $ldRepo '.github\run-artifacts\cleanup-lifetime-stack-20261024\Inputs.json'
$ldController = 'C:\Python314\python.exe'
$ldHelperSha = 'b03c008a5e590888aa70ea43a38dffc4efaa90b2563336ec2403ff86c2f22031'
$ldContractSha = 'ead95373d25ee2750a10c52e4e2bbf7cf3cabb087166b00df2533458bec27075'
$ldControllerSha = 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
foreach ($ldPair in @(@($ldHelper,$ldHelperSha),@($ldContract,$ldContractSha),@($ldController,$ldControllerSha))) {
    if ($ldPair[1] -cnotmatch '^[0-9a-f]{64}$') { throw 'Diagnostic is not frozen. Do not run.' }
    $ldItem = Get-Item -LiteralPath $ldPair[0] -Force
    while ($null -ne $ldItem) {
        if (($ldItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Redirected diagnostic input. Stop.' }
        if ($ldItem -is [IO.FileInfo]) { $ldItem = $ldItem.Directory } else { $ldItem = $ldItem.Parent }
    }
    if ((Get-FileHash -LiteralPath $ldPair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -cne $ldPair[1]) {
        throw "Diagnostic input changed. Stop: $($ldPair[0])"
    }
}
if ($VerifyOnly) { Write-Output 'LIFETIME_DIAGNOSTIC_EXTERNAL_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT'; return }
$ldIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$ldPrincipal = New-Object Security.Principal.WindowsPrincipal($ldIdentity)
if ($ldIdentity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001' -or
    $ldPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Normal non-administrator account required; no attempt started.'
}
if (Test-Path -LiteralPath (Join-Path ([IO.Path]::GetDirectoryName($ldContract)) 'normal-stack')) {
    throw 'Existing diagnostic retained. Do not retry, remove or rename it.'
}
Write-Output 'ONE NEW lifecycle stack diagnostic; not old CR3, C2, N3 or a qualification rerun.'
Write-Output 'Same frozen source and all12 cases. Existing stack-after10; same60 watchdog and120 worker default.'
Write-Output 'No retrieval, source overlay, install, security change, Git action, deletion or automatic retry.'
Write-Output 'A captured timeout is NOT a fix or completed stage. Share retained Receipt.json and Slow-Stack.log.'
& $ldController -B $ldHelper --sha256 $ldContractSha
if ($LASTEXITCODE -ne 0) { throw 'Diagnostic stopped/failed. Preserve output and share receipt/stacks. Do not retry or bypass guards.' }
Write-Output 'Lifecycle run finished; root cause/fix/CR3 still require result review. Do not run old commands.'
