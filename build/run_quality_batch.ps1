$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot ".env"
if (-not $env:TMDB_API_KEY -and (Test-Path -LiteralPath $EnvFile)) {
  $TmdbLine = Get-Content -LiteralPath $EnvFile | Where-Object { $ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$env:TMDB_API_KEY = "d77d505acf7ecda2483bf2e375579db6"

$repo = Split-Path -Parent $PSScriptRoot
$python = "C:\Users\flxjr\AppData\Local\Programs\Python\Python311\python.exe"
$status = Join-Path $PSScriptRoot "quality_batch_status.txt"
$lists = @(
  "lunes",
  "mouvements_peinture",
  "mythologie",
  "os",
  "periodes_geologiques",
  "philosophes",
  "xixe",
  "xxe"
)

Set-Location $repo
"started $(Get-Date -Format s)" | Set-Content -Encoding UTF8 $status

foreach ($list in $lists) {
  $log = Join-Path $PSScriptRoot ("quality_" + $list + ".log")
  "running $list $(Get-Date -Format s)" | Set-Content -Encoding UTF8 $status
  "=== $list $(Get-Date -Format s) ===" | Set-Content -Encoding UTF8 $log
  & $python "build\build_images.py" --list $list --force --no-patch >> $log 2>&1
  $code = $LASTEXITCODE
  "done $list exit=$code $(Get-Date -Format s)" | Add-Content -Encoding UTF8 $status
}

"patch-only $(Get-Date -Format s)" | Set-Content -Encoding UTF8 $status
& $python "build\build_images.py" --patch-only >> (Join-Path $PSScriptRoot "quality_patch.log") 2>&1
"verify-only $(Get-Date -Format s)" | Set-Content -Encoding UTF8 $status
& $python "build\build_images.py" --verify-only >> (Join-Path $PSScriptRoot "quality_verify.log") 2>&1
"finished $(Get-Date -Format s)" | Set-Content -Encoding UTF8 $status
 -match '^\s*TMDB_API_KEY\s*=' } | Select-Object -First 1
  if ($TmdbLine) { $env:TMDB_API_KEY = ($TmdbLine -split '=', 2)[1].Trim() }
}
if (-not $env:TMDB_API_KEY) { throw "TMDB_API_KEY doit Ãªtre dÃ©fini dans .env ou dans l'environnement." }
$repo = Split-Path -Parent $PSScriptRoot
$python = "C:\Users\flxjr\AppData\Local\Programs\Python\Python311\python.exe"
$status = Join-Path $PSScriptRoot "quality_batch_status.txt"
$lists = @(
  "lunes",
  "mouvements_peinture",
  "mythologie",
  "os",
  "periodes_geologiques",
  "philosophes",
  "xixe",
  "xxe"
)

Set-Location $repo
"started $(Get-Date -Format s)" | Set-Content -Encoding UTF8 $status

foreach ($list in $lists) {
  $log = Join-Path $PSScriptRoot ("quality_" + $list + ".log")
  "running $list $(Get-Date -Format s)" | Set-Content -Encoding UTF8 $status
  "=== $list $(Get-Date -Format s) ===" | Set-Content -Encoding UTF8 $log
  & $python "build\build_images.py" --list $list --force --no-patch >> $log 2>&1
  $code = $LASTEXITCODE
  "done $list exit=$code $(Get-Date -Format s)" | Add-Content -Encoding UTF8 $status
}

"patch-only $(Get-Date -Format s)" | Set-Content -Encoding UTF8 $status
& $python "build\build_images.py" --patch-only >> (Join-Path $PSScriptRoot "quality_patch.log") 2>&1
"verify-only $(Get-Date -Format s)" | Set-Content -Encoding UTF8 $status
& $python "build\build_images.py" --verify-only >> (Join-Path $PSScriptRoot "quality_verify.log") 2>&1
"finished $(Get-Date -Format s)" | Set-Content -Encoding UTF8 $status
