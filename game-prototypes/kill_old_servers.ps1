# Kill stale game/test server processes, free port 8080
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
  $_.CommandLine -match 'server\.py' -or $_.CommandLine -match 'http\.server'
} | ForEach-Object {
  Write-Host ("   - kill python PID " + $_.ProcessId + " : " + $_.CommandLine)
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
# Fallback: any process still holding port 8080
Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
  Write-Host ("   - release 8080, PID " + $_.OwningProcess)
  Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Milliseconds 500
Write-Host "   - done."
