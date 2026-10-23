param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{64}$')][string]$PreparedSha256,
    [switch]$VerifyOnly
)
$ErrorActionPreference = 'Stop'
$gate1Root = 'C:\Users\sakth\Documents\Codex\gate1-923de16-20261021'
$gate1Scripts = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\.github\scripts'
$gate1Controller = 'C:\Python314\python.exe'
$gate1Hashes = @{
    'gate1_validation.py' = 'f9b7ef54039756b3d8a95051b05a93e920518c970e6deb1c987bc5bb0aeed22e'
    'gate1_runner.py' = '13bf5ebccbd5f707f2f66c8dcd48ff73c18fb484bfc7f17b6698a66c574d51ae'
    'gate1_worker_checks.py' = 'e2e1a697faa40af82dd99e15d2deb4f590064cc93a05434c0c284f9f40b358b6'
}
function Assert-Gate1Ordinary([string]$Path) {
    $gate1Item = Get-Item -LiteralPath $Path -Force
    while ($null -ne $gate1Item) {
        if (($gate1Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Redirected Gate1 input. Stop: $Path"
        }
        if ($gate1Item -is [IO.FileInfo]) { $gate1Item = $gate1Item.Directory }
        else { $gate1Item = $gate1Item.Parent }
    }
}
$gate1Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($gate1Identity.User.Value -cne 'S-1-5-21-2571509308-2482563067-4170768140-1001') {
    throw 'Use the normal sakth account, not the agent account. No attempt started.'
}
$gate1Principal = [Security.Principal.WindowsPrincipal]::new($gate1Identity)
if ($gate1Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use non-administrator PowerShell. Do not change security settings.'
}
foreach ($gate1Pair in $gate1Hashes.GetEnumerator()) {
    $gate1File = Join-Path $gate1Scripts $gate1Pair.Key
    Assert-Gate1Ordinary $gate1File
    if ((Get-FileHash -LiteralPath $gate1File -Algorithm SHA256).Hash.ToLowerInvariant() -cne $gate1Pair.Value) {
        throw "Gate1 helper changed; no Python or test started: $($gate1Pair.Key)"
    }
}
Assert-Gate1Ordinary $gate1Controller
if ((Get-FileHash -LiteralPath $gate1Controller -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b') {
    throw 'Existing controller changed; stop. No interpreter substitution.'
}
$gate1Prepared = Join-Path $gate1Root 'Prepared.json'
Assert-Gate1Ordinary $gate1Prepared
if ((Get-FileHash -LiteralPath $gate1Prepared -Algorithm SHA256).Hash.ToLowerInvariant() -cne $PreparedSha256) {
    throw 'Prepared input seal changed. Stop.'
}
if (Test-Path -LiteralPath (Join-Path $gate1Root 'normal-attempt')) {
    throw 'Existing Gate1 attempt preserved. Do not repeat, remove or rename it.'
}
if ($VerifyOnly) {
    Write-Output 'GATE1_EXTERNAL_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT'
    return
}
Write-Output 'ONE NEW clean-source Gate1 check; not an old N3, cache or host command.'
Write-Output 'Existing selected Python 3.12 only. All previous caches, receipts and packages stay intact.'
Write-Output 'No install, download, ACL/trust/global config change, API/model/native backend, original-project Git write/push or skill install.'
Write-Output 'Selected tests do create/commit only NEW test-owned disposable Git fixture repositories.'
Write-Output 'Only fresh test-owned temporary cleanup. Fixed case list, real two workers, 24 retrieval arms and preservation.'
& $gate1Controller -B (Join-Path $gate1Scripts 'gate1_validation.py') run --prepared $gate1Prepared --sha256 $PreparedSha256
$gate1Exit = $LASTEXITCODE
if ($gate1Exit -ne 0) {
    throw "Gate1 stopped with exit $gate1Exit. Preserve/share output and receipt; do not rerun or change guards."
}
Write-Output 'Runtime observation only. Parent result review is still required; no release/install qualification.'
