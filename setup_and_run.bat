@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 goto :no_python
  set "PYTHON=python"
)

echo 必要なPythonパッケージをインストールします。初回のみインターネット接続が必要です。
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 goto :install_failed
call run.bat
exit /b %errorlevel%

:no_python
echo.
echo Python 3.11以上が見つかりません。
echo Pythonをインストールしてから、もう一度 setup_and_run.bat を実行してください。
pause
exit /b 1

:install_failed
echo.
echo パッケージのインストールに失敗しました。ネットワーク接続を確認してください。
pause
exit /b 1
