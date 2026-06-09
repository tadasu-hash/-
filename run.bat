@echo off
setlocal
cd /d "%~dp0"
if exist cultivation-trimmer.exe (
  cultivation-trimmer.exe
) else (
  python -m streamlit run app.py --server.address localhost --browser.gatherUsageStats false
)
endlocal
