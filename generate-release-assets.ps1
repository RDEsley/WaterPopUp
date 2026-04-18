param(
    [string]$Version = "v1.0.0",
    [switch]$IncludeZip = $true
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$distExe = Join-Path $PSScriptRoot "dist\waterpopup.exe"
if (-not (Test-Path $distExe)) {
    throw "Arquivo nao encontrado: $distExe`nGere o executavel antes (ex.: build-exe.bat)."
}

$releaseDir = Join-Path $PSScriptRoot "release"
if (Test-Path $releaseDir) {
    Remove-Item $releaseDir -Recurse -Force
}
New-Item -ItemType Directory -Path $releaseDir | Out-Null

$releaseExe = Join-Path $releaseDir "waterpopup.exe"
Copy-Item $distExe $releaseExe -Force

$audiosSrc = Join-Path $PSScriptRoot "audios"
if (Test-Path $audiosSrc) {
    Copy-Item $audiosSrc (Join-Path $releaseDir "audios") -Recurse -Force
}

$shaFile = Join-Path $releaseDir "SHA256.txt"
"# SHA-256 checksums ($Version)" | Out-File -FilePath $shaFile -Encoding UTF8

$exeHash = (Get-FileHash $releaseExe -Algorithm SHA256).Hash
"$exeHash  waterpopup.exe" | Out-File -FilePath $shaFile -Append -Encoding UTF8

if ($IncludeZip) {
    $zipName = "waterpopup-win64-$Version.zip"
    $zipPath = Join-Path $PSScriptRoot $zipName
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    Compress-Archive -Path (Join-Path $releaseDir "*") -DestinationPath $zipPath -Force

    $zipHash = (Get-FileHash $zipPath -Algorithm SHA256).Hash
    "$zipHash  $zipName" | Out-File -FilePath $shaFile -Append -Encoding UTF8
}

Write-Host ""
Write-Host "Assets de release gerados com sucesso:" -ForegroundColor Green
Write-Host "- Pasta: $releaseDir"
if ($IncludeZip) {
    Write-Host "- ZIP:   $zipPath"
}
Write-Host "- Hash:  $shaFile"
Write-Host ""
Write-Host "Proximo passo: anexar ZIP + SHA256.txt no GitHub Releases."

