@echo off
cd /d "%~dp0"
echo Starting setup in a persistent command prompt...
"%ComSpec%" /d /k call "%~dp0setup_and_run.bat" --keep-open
