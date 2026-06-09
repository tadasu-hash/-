@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

if exist cultivation-trimmer.exe (
  cultivation-trimmer.exe
  exit /b
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m streamlit run app.py --server.address localhost --browser.gatherUsageStats false
  exit /b
)

where python >nul 2>nul
if %errorlevel%==0 (
  python -m streamlit run app.py --server.address localhost --browser.gatherUsageStats false
  exit /b
)

echo Pythonまたは完成版exeが見つかりません。
echo ソース版を使用する場合は、Python 3.11以上をインストールして setup_and_run.bat を実行してください。
pause
exit /b 1
