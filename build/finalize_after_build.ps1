param(
  [int]$BuildProcessId = 0
)

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
$BuildLog = Join-Path $PSScriptRoot "build_resume.log"
$FinalLog = Join-Path $PSScriptRoot "finalize_after_build.log"
$Report = Join-Path $PSScriptRoot "etat_final.txt"

Set-Location $RepoRoot
function Add-Log($Text) {
  Add-Content -Path $FinalLog -Encoding utf8 -Value ("[" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "] " + $Text)
}

if ($BuildProcessId -gt 0) {
  Add-Log "Finaliseur lancé. Attente du build PID $BuildProcessId."
  while ($true) {
    $Processus = Get-Process -Id $BuildProcessId -ErrorAction SilentlyContinue
    $Marqueur = $false
    if (Test-Path $BuildLog) {
      $Fin = Get-Content -Path $BuildLog -Tail 20 -ErrorAction SilentlyContinue
      $Marqueur = ($Fin -match "RESUME DONE").Count -gt 0
    }
    if (-not $Processus -or $Marqueur) { break }
    Start-Sleep -Seconds 30
  }
}

Add-Log "Régénération de memo.html."
& $Python "build\build_images.py" --patch-only *>> $FinalLog
if ($LASTEXITCODE -ne 0) { throw "Échec de la régénération." }

Add-Log "Vérification finale."
$Verification = & $Python "build\build_images.py" --verify-only 2>&1
$Verification | Add-Content -Path $FinalLog -Encoding utf8
if ($LASTEXITCODE -ne 0) { throw "Échec de la vérification." }

$Compteurs = Get-ChildItem ".\thumbs" -Directory -ErrorAction SilentlyContinue |
  Sort-Object Name |
  ForEach-Object {
    $Nombre = (Get-ChildItem $_.FullName -File -ErrorAction SilentlyContinue).Count
    "{0,-24} {1,4}" -f $_.Name, $Nombre
  }

$Resume = @(
  "État final du build Memo",
  ("Date: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss")),
  "",
  "Compteurs fichiers thumbs:",
  $Compteurs,
  "",
  "Vérification:",
  $Verification,
  "",
  ("Fichier app: " + (Join-Path $RepoRoot "memo.html")),
  ("Log build: " + $BuildLog),
  ("Log finaliseur: " + $FinalLog)
)
$Resume | Set-Content -Path $Report -Encoding utf8
Add-Log "Rapport écrit : $Report"
