@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title 培養データ トリミング - 初回セットアップ

set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"
set "SETUP_LOG=%~dp0setup.log"
>"%SETUP_LOG%" echo [%date% %time%] セットアップ開始

echo ================================================
echo  培養データ トリミング - 初回セットアップ
echo ================================================
echo.
echo この画面はセットアップ完了まで閉じないでください。
echo 問題が起きた場合は、このフォルダの setup.log を管理者へ渡してください。
echo.

if exist "%VENV_PYTHON%" goto :install

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if not errorlevel 1 (
  set "BASE_PYTHON=py -3"
  goto :create_venv
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if not errorlevel 1 (
  set "BASE_PYTHON=python"
  goto :create_venv
)
goto :no_python

:create_venv
echo [1/3] 専用Python環境を作成しています...
echo [%date% %time%] venv作成: %BASE_PYTHON%>>"%SETUP_LOG%"
%BASE_PYTHON% -m venv "%~dp0.venv" >>"%SETUP_LOG%" 2>&1
if errorlevel 1 goto :venv_failed

:install
echo [2/3] 必要なパッケージをインストールしています...
echo       初回のみインターネット接続が必要です。数分かかる場合があります。
echo [%date% %time%] pip install開始>>"%SETUP_LOG%"
"%VENV_PYTHON%" -m pip install -r "%~dp0requirements.txt" >>"%SETUP_LOG%" 2>&1
if errorlevel 1 goto :install_failed

echo [3/3] セットアップ完了。アプリを起動します...
echo [%date% %time%] セットアップ完了>>"%SETUP_LOG%"
call "%~dp0run.bat"
set "RUN_RESULT=%errorlevel%"
if not "%RUN_RESULT%"=="0" goto :run_failed
exit /b 0

:no_python
echo.
echo エラー: Python 3.11以上が見つかりません。
echo Python 3.11以上をインストールしてから、もう一度実行してください。
echo [%date% %time%] Python 3.11以上が見つかりません>>"%SETUP_LOG%"
goto :stop

:venv_failed
echo.
echo エラー: 専用Python環境の作成に失敗しました。
echo 詳細は setup.log を確認してください。
echo [%date% %time%] venv作成失敗>>"%SETUP_LOG%"
goto :stop

:install_failed
echo.
echo エラー: パッケージのインストールに失敗しました。
echo ネットワーク接続を確認してください。詳細は setup.log に記録されています。
echo [%date% %time%] pip install失敗>>"%SETUP_LOG%"
goto :stop

:run_failed
echo.
echo エラー: セットアップ後のアプリ起動に失敗しました。
echo 詳細は上のメッセージと setup.log を確認してください。
echo [%date% %time%] アプリ起動失敗: %RUN_RESULT%>>"%SETUP_LOG%"

:stop
echo.
echo この画面を閉じるには、何かキーを押してください。
pause >nul
exit /b 1
