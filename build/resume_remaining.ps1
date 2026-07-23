$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot ".env"
if (-not $env:TMDB_API_KEY -and (Test-Path -LiteralPath $EnvFile)) {
  $TmdbLine = Get-Content -LiteralPath $EnvFile | Where-Object { $ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$env:TMDB_API_KEY = "d77d505acf7ecda2483bf2e375579db6"

$Python = "C:\Users\flxjr\AppData\Local\Programs\Python\Python311\python.exe"
$Repo = "C:\Users\flxjr\OneDrive\Bureau\memo-app"
$Log = Join-Path $Repo "build\build_resume.log"

Set-Location $Repo

$lists = @(
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

Add-Content -Path $Log -Encoding utf8 -Value ("=== RESUME START " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " ===")
foreach ($list in $lists) {
  Add-Content -Path $Log -Encoding utf8 -Value ("=== " + $list + " ===")
  & $Python "build\build_images.py" --list $list --no-patch 2>&1 | Add-Content -Path $Log -Encoding utf8
}
Add-Content -Path $Log -Encoding utf8 -Value ("=== PATCH ONLY ===")
& $Python "build\build_images.py" --patch-only 2>&1 | Add-Content -Path $Log -Encoding utf8
Add-Content -Path $Log -Encoding utf8 -Value ("=== RESUME DONE " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " ===")
 -match '^\s*TMDB_API_KEY\s*=' } | Select-Object -First 1
  if ($TmdbLine) { $env:TMDB_API_KEY = ($TmdbLine -split '=', 2)[1].Trim() }
}
if (-not $env:TMDB_API_KEY) { throw "TMDB_API_KEY doit Ãªtre dÃ©fini dans .env ou dans l'environnement." }
$Python = "C:\Users\flxjr\AppData\Local\Programs\Python\Python311\python.exe"
$Repo = "C:\Users\flxjr\OneDrive\Bureau\memo-app"
$Log = Join-Path $Repo "build\build_resume.log"

Set-Location $Repo

$lists = @(
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

Add-Content -Path $Log -Encoding utf8 -Value ("=== RESUME START " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " ===")
foreach ($list in $lists) {
  Add-Content -Path $Log -Encoding utf8 -Value ("=== " + $list + " ===")
  & $Python "build\build_images.py" --list $list --no-patch 2>&1 | Add-Content -Path $Log -Encoding utf8
}
Add-Content -Path $Log -Encoding utf8 -Value ("=== PATCH ONLY ===")
& $Python "build\build_images.py" --patch-only 2>&1 | Add-Content -Path $Log -Encoding utf8
Add-Content -Path $Log -Encoding utf8 -Value ("=== RESUME DONE " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " ===")
