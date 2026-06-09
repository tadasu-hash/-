@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title 培養データ トリミング - 完成版ビルド

echo ================================================
echo  培養データ トリミング - 完成版ビルド
echo ================================================
echo.

set "PYTHON_CMD="
py -3.12 --version >nul 2>nul && set "PYTHON_CMD=py -3.12"
if not defined PYTHON_CMD py -3 --version >nul 2>nul && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD python --version >nul 2>nul && set "PYTHON_CMD=python"
if not defined PYTHON_CMD goto :no_python

echo [1/3] ビルド用パッケージを同じPython環境へインストールします...
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 goto :failed

echo [2/3] 完成版を作成し、Streamlit画面ファイルを検証します...
%PYTHON_CMD% build_release.py
if errorlevel 1 goto :failed

echo [3/3] 完成しました: dist\cultivation-trimmer
echo このフォルダ全体をZIPにして配布してください。
echo.
pause
exit /b 0

:no_python
echo エラー: 実行可能なPython 3が見つかりません。
goto :failed

:failed
echo.
echo 完成版の作成に失敗しました。上に表示されたエラーを確認してください。
echo 不完全なdistフォルダは配布しないでください。
echo.
pause
exit /b 1
