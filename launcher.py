"""PyInstaller配布用のStreamlit起動ランチャー。"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def streamlit_args(app: Path) -> list[str]:
    """PC側のStreamlit設定に左右されないローカル起動引数を返す。"""
    return [
        "streamlit",
        "run",
        str(app),
        "--global.developmentMode=false",
        "--server.address=localhost",
        "--server.port=8501",
        "--browser.serverAddress=localhost",
        "--browser.serverPort=8501",
        "--browser.gatherUsageStats=false",
    ]


def main() -> None:
    from streamlit.web import cli as stcli

    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    app = base / "app.py"
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    sys.argv = streamlit_args(app)
    raise SystemExit(stcli.main())


if __name__ == "__main__":
    main()
