param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'

# External launcher hash is supplied separately. These two inputs are also sealed.
$c1Root = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git'
$c1Helper = Join-Path $c1Root '.github\scripts\gate1_current_preflight.py'
$c1Contract = Join-Path $c1Root '.github\run-artifacts\gate1-current-20261023\C1-Contract.json'
$c1Controller = 'C:\Python314\python.exe'
$c1Output = 'C:\Users\sakth\Documents\Codex\gate1-current-a38297d-20261023-c1'
$c1HelperSha = '5e1b06812949b72a8723844c4c1b7a8bde1b4fee645c43147e3352acb7696861'
$c1ContractSha = '116835e0a0f79dc907512c0275404bac210c7128484580ceebf865e0ec6d5dbb'
$c1ControllerSha = 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'

function Assert-C1OrdinaryChain([string]$c1Path) {
    $c1Item = Get-Item -LiteralPath $c1Path -Force
    while ($null -ne $c1Item) {
        if (($c1Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Redirected handoff path; stop: $($c1Item.FullName)"
        }
        if ($c1Item -is [IO.FileInfo]) { $c1Item = $c1Item.Directory }
        else { $c1Item = $c1Item.Parent }
    }
}

foreach ($c1Pair in @(@($c1Helper, $c1HelperSha), @($c1Contract, $c1ContractSha), @($c1Controller, $c1ControllerSha))) {
    Assert-C1OrdinaryChain $c1Pair[0]
    if ((Get-FileHash -LiteralPath $c1Pair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -cne $c1Pair[1]) {
        throw "C1 input changed or is not frozen; stop: $($c1Pair[0])"
    }
}
if ($VerifyOnly) {
    Write-Output 'C1_EXTERNAL_SEALS_MATCH_NO_PYTHON_SOURCE_COPY_OR_ATTEMPT'
    return
}

$c1Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$c1Principal = New-Object Security.Principal.WindowsPrincipal($c1Identity)
if ($c1Identity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001' -or
    $c1Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'C1 requires the existing normal non-administrator account; no attempt started.'
}
if (Test-Path -LiteralPath $c1Output) { throw 'Existing C1 output is preserved. Do not retry or remove it.' }
if (Test-Path -LiteralPath (Join-Path ([IO.Path]::GetDirectoryName($c1Contract)) 'C1-Preflight-Failure.json')) {
    throw 'Existing C1 preflight failure is preserved. Do not retry or remove it.'
}

Write-Output 'STEP1 ONLY: exact a38297d clean source and existing Python3.12 identity/dependency/default checks.'
Write-Output 'No retrieval, numerical work, install/download, ACL/trust change, deletion, Git write, model/API/native backend or skill installation.'
Write-Output 'All old attempts stay unchanged. A failure stops; no retry. Gate1 groups and24arms remain later.'

& $c1Controller -B $c1Helper --contract $c1Contract --sha256 $c1ContractSha
if ($LASTEXITCODE -ne 0) { throw 'C1 stopped. Preserve/share output and receipt; do not retry or change guards.' }
Write-Output 'Share Receipt.json and Prepared.json hashes for review. This is not a Gate1 completion or permission to run an old command.'
