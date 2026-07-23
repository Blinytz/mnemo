$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot ".env"

if (-not $env:TMDB_API_KEY -and (Test-Path -LiteralPath $EnvFile)) {
  $TmdbLine = Get-Content -LiteralPath $EnvFile |
    Where-Object { $_ -match '^\s*TMDB_API_KEY\s*=' } |
    Select-Object -First 1
  if ($TmdbLine) {
    $env:TMDB_API_KEY = ($TmdbLine -split '=', 2)[1].Trim()
  }
}
if (-not $env:TMDB_API_KEY) {
  throw "TMDB_API_KEY doit être défini dans .env ou dans l'environnement."
}

$Python = (Get-Command python -ErrorAction Stop).Source
$Status = Join-Path $PSScriptRoot "quality_batch_status.txt"
$Lists = @(
  "lunes",
  "mouvements_peinture",
  "mythologie",
  "os",
  "periodes_geologiques",
  "philosophes",
  "xixe",
  "xxe"
)

Set-Location $RepoRoot
"started $(Get-Date -Format s)" | Set-Content -Encoding utf8 $Status

foreach ($List in $Lists) {
  $Log = Join-Path $PSScriptRoot ("quality_" + $List + ".log")
  "running $List $(Get-Date -Format s)" | Set-Content -Encoding utf8 $Status
  "=== $List $(Get-Date -Format s) ===" | Set-Content -Encoding utf8 $Log
  & $Python "build\build_images.py" --list $List --force --no-patch *>> $Log
  "done $List exit=$LASTEXITCODE $(Get-Date -Format s)" |
    Add-Content -Encoding utf8 $Status
  if ($LASTEXITCODE -ne 0) { throw "Échec du lot $List." }
}

"patch-only $(Get-Date -Format s)" | Set-Content -Encoding utf8 $Status
& $Python "build\build_images.py" --patch-only *>> (Join-Path $PSScriptRoot "quality_patch.log")
if ($LASTEXITCODE -ne 0) { throw "Échec de la génération finale." }

"verify-only $(Get-Date -Format s)" | Set-Content -Encoding utf8 $Status
& $Python "build\build_images.py" --verify-only *>> (Join-Path $PSScriptRoot "quality_verify.log")
if ($LASTEXITCODE -ne 0) { throw "Échec de la vérification finale." }

"finished $(Get-Date -Format s)" | Set-Content -Encoding utf8 $Status
