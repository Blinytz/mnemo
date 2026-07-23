param(
  [int]$BuildProcessId = 22276
)

$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot ".env"
if (-not $env:TMDB_API_KEY -and (Test-Path -LiteralPath $EnvFile)) {
  $TmdbLine = Get-Content -LiteralPath $EnvFile | Where-Object { param(
  [int]$BuildProcessId = 22276
)

$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$env:TMDB_API_KEY = "d77d505acf7ecda2483bf2e375579db6"

$Python = "C:\Users\flxjr\AppData\Local\Programs\Python\Python311\python.exe"
$Repo = "C:\Users\flxjr\OneDrive\Bureau\memo-app"
$BuildLog = Join-Path $Repo "build\build_resume.log"
$FinalLog = Join-Path $Repo "build\finalize_after_build.log"
$Report = Join-Path $Repo "build\etat_final.txt"

Set-Location $Repo

function Add-Log($Text) {
  Add-Content -Path $FinalLog -Encoding utf8 -Value ("[" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "] " + $Text)
}

Add-Log "Finaliseur lance. Attente du build PID $BuildProcessId."

while ($true) {
  $proc = Get-Process -Id $BuildProcessId -ErrorAction SilentlyContinue
  $doneMarker = $false
  if (Test-Path $BuildLog) {
    $tail = Get-Content -Path $BuildLog -Tail 20 -ErrorAction SilentlyContinue
    $doneMarker = ($tail -match "RESUME DONE").Count -gt 0
  }
  if (-not $proc -or $doneMarker) { break }
  Start-Sleep -Seconds 60
}

Add-Log "Build principal termine ou absent. Regeneration memo.html."
& $Python "build\build_images.py" --patch-only 2>&1 | Add-Content -Path $FinalLog -Encoding utf8

Add-Log "Verification finale."
$verifyOutput = & $Python "build\build_images.py" --verify-only 2>&1
$verifyOutput | Add-Content -Path $FinalLog -Encoding utf8

$counts = Get-ChildItem ".\thumbs" -Directory -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
  $count = (Get-ChildItem $_.FullName -File -ErrorAction SilentlyContinue).Count
  "{0,-24} {1,4}" -f $_.Name, $count
}

$summary = @()
$summary += "Etat final du build Memo"
$summary += "Date: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
$summary += ""
$summary += "Compteurs fichiers thumbs:"
$summary += $counts
$summary += ""
$summary += "Verification:"
$summary += $verifyOutput
$summary += ""
$summary += "Fichier app: C:\Users\flxjr\OneDrive\Bureau\memo-app\memo.html"
$summary += "Log build: C:\Users\flxjr\OneDrive\Bureau\memo-app\build\build_resume.log"
$summary += "Log finaliseur: C:\Users\flxjr\OneDrive\Bureau\memo-app\build\finalize_after_build.log"

$summary | Set-Content -Path $Report -Encoding utf8
Add-Log "Rapport ecrit: $Report"
 -match '^\s*TMDB_API_KEY\s*=' } | Select-Object -First 1
  if ($TmdbLine) { $env:TMDB_API_KEY = ($TmdbLine -split '=', 2)[1].Trim() }
}
if (-not $env:TMDB_API_KEY) { throw "TMDB_API_KEY doit Ãªtre dÃ©fini dans .env ou dans l'environnement." }
$Python = "C:\Users\flxjr\AppData\Local\Programs\Python\Python311\python.exe"
$Repo = "C:\Users\flxjr\OneDrive\Bureau\memo-app"
$BuildLog = Join-Path $Repo "build\build_resume.log"
$FinalLog = Join-Path $Repo "build\finalize_after_build.log"
$Report = Join-Path $Repo "build\etat_final.txt"

Set-Location $Repo

function Add-Log($Text) {
  Add-Content -Path $FinalLog -Encoding utf8 -Value ("[" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "] " + $Text)
}

Add-Log "Finaliseur lance. Attente du build PID $BuildProcessId."

while ($true) {
  $proc = Get-Process -Id $BuildProcessId -ErrorAction SilentlyContinue
  $doneMarker = $false
  if (Test-Path $BuildLog) {
    $tail = Get-Content -Path $BuildLog -Tail 20 -ErrorAction SilentlyContinue
    $doneMarker = ($tail -match "RESUME DONE").Count -gt 0
  }
  if (-not $proc -or $doneMarker) { break }
  Start-Sleep -Seconds 60
}

Add-Log "Build principal termine ou absent. Regeneration memo.html."
& $Python "build\build_images.py" --patch-only 2>&1 | Add-Content -Path $FinalLog -Encoding utf8

Add-Log "Verification finale."
$verifyOutput = & $Python "build\build_images.py" --verify-only 2>&1
$verifyOutput | Add-Content -Path $FinalLog -Encoding utf8

$counts = Get-ChildItem ".\thumbs" -Directory -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
  $count = (Get-ChildItem $_.FullName -File -ErrorAction SilentlyContinue).Count
  "{0,-24} {1,4}" -f $_.Name, $count
}

$summary = @()
$summary += "Etat final du build Memo"
$summary += "Date: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
$summary += ""
$summary += "Compteurs fichiers thumbs:"
$summary += $counts
$summary += ""
$summary += "Verification:"
$summary += $verifyOutput
$summary += ""
$summary += "Fichier app: C:\Users\flxjr\OneDrive\Bureau\memo-app\memo.html"
$summary += "Log build: C:\Users\flxjr\OneDrive\Bureau\memo-app\build\build_resume.log"
$summary += "Log finaliseur: C:\Users\flxjr\OneDrive\Bureau\memo-app\build\finalize_after_build.log"

$summary | Set-Content -Path $Report -Encoding utf8
Add-Log "Rapport ecrit: $Report"
