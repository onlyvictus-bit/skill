param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'

# Source hashes are literal seals inside the reviewed helper. Check the helper
# and existing controller again before each input-preparation/runtime call.
$sr3Repo = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git'
$sr3Helper = Join-Path $sr3Repo '.github\scripts\shutdown_repair_verification.py'
$sr3Controller = 'C:\Python314\python.exe'
$sr3HelperSha = 'f224d215d0eb8ac898ac6a185cb388d1aa45b627765a006ae266455b800aff69'
$sr3ControllerSha = 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
$sr3Sid = 'S-1-5-21-2571509308-2482563067-4170768140-1001'

function Test-Sr3Ordinary([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    while ($null -ne $item) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Redirected SR3 input: $Path" }
        if ($item -is [IO.FileInfo]) { $item = $item.Directory } else { $item = $item.Parent }
    }
}
function Test-Sr3Seals {
    foreach ($pair in @(@($sr3Helper,$sr3HelperSha),@($sr3Controller,$sr3ControllerSha))) {
        if ($pair[1] -cnotmatch '^[0-9a-f]{64}$') { throw 'SR3 handoff is not frozen. Do not run.' }
        Test-Sr3Ordinary $pair[0]
        if ((Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -cne $pair[1]) {
            throw "SR3 sealed input changed: $($pair[0])"
        }
    }
}
Test-Sr3Seals
if ($VerifyOnly) { Write-Output 'SR3_EXTERNAL_SEALS_MATCH_NO_PYTHON_OR_WORKLOAD'; return }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if ($identity.User.Value -cne $sr3Sid -or $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Normal non-administrator account required; no SR3 output or attempt started.'
}
$root = Join-Path $sr3Repo '.github\run-artifacts\cleanup-shutdown-repair-20261026'
$contract = Join-Path $root 'SR3-Inputs.json'
$output = Join-Path $root 'sr3-normal'
$preparation = Join-Path $root 'sr3-prepare'
if ((Test-Path -LiteralPath $contract) -or (Test-Path -LiteralPath $output) -or (Test-Path -LiteralPath $preparation)) {
    throw 'SR3 input or normal-account attempt already exists. Preserve it; do not retry.'
}
Write-Output 'One fresh SR3 normal-account focused cleanup verification; not C2, CR3, TC1, MP1, Gate1, release, or install.'
Write-Output 'The helper inventories old/private history before work, proves identity first, then ownership/lifecycle groups before the retained public ordered method.'
Write-Output 'Existing Python 3.12; 74 ownership/writer/lifecycle controls, then unchanged community/global/DRIFT/vector initial/replay and lease refusals.'
Write-Output 'Worker default120, public90, lifecycle watchdog60 and shared shutdown5 remain unchanged. No reinstall, permission change, Git write, deletion or retry.'
Test-Sr3Seals
& $sr3Controller -B $sr3Helper --prepare
if ($LASTEXITCODE -ne 0) { throw 'SR3 preparation stopped before workload. Preserve/share sr3-prepare\Failure.json; do not retry.' }
$contractSha = (Get-FileHash -LiteralPath $contract -Algorithm SHA256).Hash.ToLowerInvariant()
Test-Sr3Seals
& $sr3Controller -B $sr3Helper --sha256 $contractSha
if ($LASTEXITCODE -ne 0) { throw 'SR3 stopped. Preserve/share sr3-normal\Receipt.json. Do not retry or relax guards.' }
Write-Output 'Focused cleanup stage observation only. Gate1, release, and installation remain false.'
