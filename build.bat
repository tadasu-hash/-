@echo off
setlocal
cd /d "%~dp0"
python -m pip install -r requirements.txt
pyinstaller --noconfirm --clean --onedir --name cultivation-trimmer --collect-all streamlit --collect-all plotly --add-data "app.py;." --add-data "core;core" launcher.py
copy run.bat dist\cultivation-trimmer\run.bat
copy README_ja.md dist\cultivation-trimmer\README_ja.md
copy START_HERE.txt dist\cultivation-trimmer\START_HERE.txt
endlocal
