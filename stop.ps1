# Stop Streamlit on port 8501 without interactive prompts
$pids = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique

if (-not $pids) {
    Write-Host "No service on port 8501."
    exit 0
}

foreach ($procId in $pids) {
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped process $procId"
}
