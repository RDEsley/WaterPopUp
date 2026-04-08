# Gera dist\waterpopup.exe. Encerra instâncias em execução para o Windows liberar o arquivo
# (evita PermissionError em update_exe_pe_checksum / os.remove).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$procs = @(Get-Process -Name "waterpopup" -ErrorAction SilentlyContinue)
if ($procs.Count -gt 0) {
    Write-Host "Encerrando $($procs.Count) processo(s) waterpopup..."
    $procs | Stop-Process -Force
}
# Fallback: encerra por nome do .exe (atalho na inicialização, etc.)
$null = cmd /c "taskkill /F /IM waterpopup.exe 2>nul"
Start-Sleep -Seconds $(if ($procs.Count -gt 0) { 4 } else { 1 })

& pyinstaller waterpopup.spec @args
exit $LASTEXITCODE
