"""PyInstaller配布用のStreamlit起動ランチャー。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from streamlit.web import cli as stcli


def main() -> None:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    app = base / "app.py"
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    sys.argv = ["streamlit", "run", str(app), "--server.address=localhost", "--browser.gatherUsageStats=false"]
    raise SystemExit(stcli.main())


if __name__ == "__main__":
    main()
