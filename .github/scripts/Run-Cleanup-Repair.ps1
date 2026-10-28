param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
$crRepo = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git'
$crHelper = Join-Path $crRepo '.github\scripts\cleanup_repair_runtime.py'
$crContract = Join-Path $crRepo '.github\run-artifacts\cleanup-repair-20261023\Runtime-Inputs.json'
$crController = 'C:\Python314\python.exe'
$crHelperSha = '8bc851bfbc59848b1730bbd141987c4fff80156a5f5adc23467e7f706fbafc2f'
$crContractSha = '18b1d93425f0f52965b94ed7349acf11042065348aafc26b8152ce7c6b595838'
$crControllerSha = 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
foreach ($crPair in @(@($crHelper,$crHelperSha),@($crContract,$crContractSha),@($crController,$crControllerSha))) {
    if ($crPair[1] -cnotmatch '^[0-9a-f]{64}$') { throw 'CR3 handoff is not frozen. Do not run.' }
    $crItem = Get-Item -LiteralPath $crPair[0] -Force
    while ($null -ne $crItem) {
        if (($crItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Redirected CR3 input. Stop.' }
        if ($crItem -is [IO.FileInfo]) { $crItem = $crItem.Directory } else { $crItem = $crItem.Parent }
    }
    if ((Get-FileHash -LiteralPath $crPair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -cne $crPair[1]) {
        throw "CR3 input changed. Stop: $($crPair[0])"
    }
}
if ($VerifyOnly) { Write-Output 'CR3_EXTERNAL_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT'; return }
$crIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$crPrincipal = New-Object Security.Principal.WindowsPrincipal($crIdentity)
if ($crIdentity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001' -or
    $crPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Normal non-administrator account required; no attempt started.'
}
if (Test-Path -LiteralPath (Join-Path ([IO.Path]::GetDirectoryName($crContract)) 'normal-comparison')) {
    throw 'Existing CR3 comparison retained. Do not retry or remove it.'
}
Write-Output 'ONE NEW focused original/repaired ordered comparison, not old C2, N3 or full Gate1.'
Write-Output 'Identity/dependencies before workload claim. Existing Python3.12 and default120; original public timeout90 unchanged.'
Write-Output 'Twelve lifecycle/error controls plus community/global/DRIFT/vector initial retrieval and replay, with lease refusals.'
Write-Output 'No install/download, ACL/trust/global change, Git write/push, API/model/native database or skill installation.'
Write-Output 'All old source/caches/evidence retained. Only NEW test-owned temporary housekeeping; no automatic retry.'
& $crController -B $crHelper --sha256 $crContractSha
if ($LASTEXITCODE -ne 0) { throw 'CR3 stopped. Preserve/share output and receipt. Do not retry or change guards.' }
Write-Output 'Share Receipt.json for result review. Focused observation is NOT Gate1 completion, release or installation.'
