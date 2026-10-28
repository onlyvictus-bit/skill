param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'

# One new C2 run, bound to the successful and now read-only C1 clean source.
$c2Root = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git'
$c2Helper = Join-Path $c2Root '.github\scripts\gate1_current_runtime.py'
$c2Contract = Join-Path $c2Root '.github\run-artifacts\gate1-current-20261023\C2\C2-Inputs.json'
$c2Controller = 'C:\Python314\python.exe'
$c2Output = 'C:\Users\sakth\Documents\Codex\gate1-current-a38297d-20261023-c2'
$c2HelperSha = '42ee6ee502ac9b4dc742fa6c9a0a70d56fc04600f1d24800f65ace32db56989f'
$c2ContractSha = '6cb6cb39d6b3e2a702b0e2b63cba6a97b44f250fb4c396463bc62f5cd2113c15'
$c2ControllerSha = 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'

function Assert-C2OrdinaryChain([string]$c2Path) {
    $c2Item = Get-Item -LiteralPath $c2Path -Force
    while ($null -ne $c2Item) {
        if (($c2Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Redirected C2 handoff path; stop: $($c2Item.FullName)"
        }
        if ($c2Item -is [IO.FileInfo]) { $c2Item = $c2Item.Directory }
        else { $c2Item = $c2Item.Parent }
    }
}

foreach ($c2Pair in @(@($c2Helper, $c2HelperSha), @($c2Contract, $c2ContractSha), @($c2Controller, $c2ControllerSha))) {
    if ($c2Pair[1] -cnotmatch '^[0-9a-f]{64}$') { throw 'C2 handoff is not frozen. Stop.' }
    Assert-C2OrdinaryChain $c2Pair[0]
    if ((Get-FileHash -LiteralPath $c2Pair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -cne $c2Pair[1]) {
        throw "C2 input changed; stop: $($c2Pair[0])"
    }
}
if ($VerifyOnly) {
    Write-Output 'C2_EXTERNAL_SEALS_MATCH_NO_PYTHON_WORKER_OR_ATTEMPT'
    return
}

$c2Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$c2Principal = New-Object Security.Principal.WindowsPrincipal($c2Identity)
if ($c2Identity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001' -or
    $c2Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'C2 requires the existing normal non-administrator account; no attempt started.'
}
if (Test-Path -LiteralPath $c2Output) { throw 'Existing C2 attempt preserved. Do not retry or remove it.' }
if (Test-Path -LiteralPath (Join-Path ([IO.Path]::GetDirectoryName($c2Contract)) 'Preflight-Failure.json')) {
    throw 'Existing C2 preflight failure preserved. Do not retry or remove it.'
}

Write-Output 'STEP2 ONLY: existing verified a38297d source preservation-pinned, no overlay; five exact test groups and24 comparisons with fresh replays.'
Write-Output 'Existing selected Python3.12 and default120. No install/download, ACL/trust change, external API/learned model/native database or skill install.'
Write-Output 'No original-project Git write/push; tests may create/commit only NEW disposable Git fixtures.'
Write-Output 'All old source/caches/evidence retained. Only NEW test-owned temporary cleanup. Every failure stops; no automatic retry.'
Write-Output 'This is not C3 worker-handle/cleanup review, whole Gate1, release or installed qualification.'
& $c2Controller -B $c2Helper --sha256 $c2ContractSha
if ($LASTEXITCODE -ne 0) { throw 'C2 stopped. Preserve/share output and receipt; do not retry, remove markers or change guards.' }
Write-Output 'Share the C2 Receipt path/hash. Actual results still require review before the separate C3 step.'
