param(
  [string]$Port = '8501'
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m streamlit run "$PSScriptRoot\streamlit_app.py" --server.headless true --browser.gatherUsageStats false --server.port $Port