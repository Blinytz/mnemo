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
$Log = Join-Path $PSScriptRoot "build_resume.log"
$Lists = @(
  "os",
  "peintres",
  "rois_france",
  "coupes_monde",
  "xixe",
  "xxe",
  "litterature",
  "guerres",
  "philosophes",
  "mouvements_peinture",
  "jo_ete",
  "jo_hiver",
  "f1_champions",
  "consoles",
  "lunes",
  "periodes_geologiques",
  "films"
)

Set-Location $RepoRoot
Add-Content -Path $Log -Encoding utf8 -Value ("=== RESUME START " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " ===")

foreach ($List in $Lists) {
  Add-Content -Path $Log -Encoding utf8 -Value ("=== " + $List + " ===")
  & $Python "build\build_images.py" --list $List --no-patch *>> $Log
  if ($LASTEXITCODE -ne 0) { throw "Échec du lot $List." }
}

Add-Content -Path $Log -Encoding utf8 -Value "=== PATCH ONLY ==="
& $Python "build\build_images.py" --patch-only *>> $Log
if ($LASTEXITCODE -ne 0) { throw "Échec de la génération finale." }

Add-Content -Path $Log -Encoding utf8 -Value ("=== RESUME DONE " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " ===")
