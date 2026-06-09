@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title 培養データ トリミング

if exist "%~dp0cultivation-trimmer.exe" goto :run_exe
if exist "%~dp0.venv\Scripts\python.exe" goto :run_venv

py -3 -c "import streamlit, pandas, plotly, openpyxl" >nul 2>nul
if not errorlevel 1 goto :run_py
python -c "import streamlit, pandas, plotly, openpyxl" >nul 2>nul
if not errorlevel 1 goto :run_python

echo.
echo エラー: アプリの実行環境が見つかりません。
echo 初回は setup_and_run.bat をダブルクリックしてください。
goto :failed

:run_exe
"%~dp0cultivation-trimmer.exe"
if errorlevel 1 goto :failed
exit /b 0

:run_venv
"%~dp0.venv\Scripts\python.exe" -m streamlit run "%~dp0app.py" --server.address localhost --browser.gatherUsageStats false
if errorlevel 1 goto :failed
exit /b 0

:run_py
py -3 -m streamlit run "%~dp0app.py" --server.address localhost --browser.gatherUsageStats false
if errorlevel 1 goto :failed
exit /b 0

:run_python
python -m streamlit run "%~dp0app.py" --server.address localhost --browser.gatherUsageStats false
if errorlevel 1 goto :failed
exit /b 0

:failed
echo.
echo アプリを起動できませんでした。上に表示されたエラー内容を確認してください。
echo 解決しない場合は setup_and_run.bat をもう一度実行してください。
echo.
echo この画面を閉じるには、何かキーを押してください。
pause >nul
exit /b 1
