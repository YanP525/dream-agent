Set-Location $PSScriptRoot
Write-Host "ShadowAgent -> http://localhost:8501"
Write-Host "To stop: .\stop.ps1"
streamlit run app.py
