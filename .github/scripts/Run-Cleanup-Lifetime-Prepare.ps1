param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
$lpRepo = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git'
$lpHelper = Join-Path $lpRepo '.github\scripts\cleanup_lifetime_diagnostic.py'
$lpController = 'C:\Python314\python.exe'
$lpHelperSha = 'b03c008a5e590888aa70ea43a38dffc4efaa90b2563336ec2403ff86c2f22031'
$lpControllerSha = 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
foreach ($lpPair in @(@($lpHelper,$lpHelperSha),@($lpController,$lpControllerSha))) {
    if ($lpPair[1] -cnotmatch '^[0-9a-f]{64}$') { throw 'Input preparation is not frozen. Do not run.' }
    $lpItem = Get-Item -LiteralPath $lpPair[0] -Force
    while ($null -ne $lpItem) {
        if (($lpItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Redirected preparation input. Stop.' }
        if ($lpItem -is [IO.FileInfo]) { $lpItem = $lpItem.Directory } else { $lpItem = $lpItem.Parent }
    }
    if ((Get-FileHash -LiteralPath $lpPair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -cne $lpPair[1]) {
        throw "Preparation input changed. Stop: $($lpPair[0])"
    }
}
if ($VerifyOnly) { Write-Output 'LIFETIME_PREPARE_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT'; return }
$lpIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$lpPrincipal = New-Object Security.Principal.WindowsPrincipal($lpIdentity)
if ($lpIdentity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001' -or
    $lpPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Normal non-administrator account required; no preparation started.'
}
if (Test-Path -LiteralPath (Join-Path $lpRepo '.github\run-artifacts\cleanup-lifetime-stack-20261024')) {
    throw 'Existing preparation retained. Do not retry, remove, rename or precreate the directory.'
}
Write-Output 'INPUT PREPARATION ONLY: read/hash existing source, runtime metadata and failed CR3 attempt.'
Write-Output 'No Python3.12, test, retrieval, diagnostic workload claim, source overlay or old command runs.'
Write-Output 'Only NEW Inputs.json will be created after validation. No install, ACL/trust, Git action or deletion.'
& $lpController -B $lpHelper --prepare
if ($LASTEXITCODE -ne 0) { throw 'Preparation stopped. Preserve/share error; no automatic retry or permission workaround.' }
Write-Output 'Share the printed contract path/size/SHA. Diagnostic runtime command is NOT frozen or authorized to run by this preparation.'
