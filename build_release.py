"""Windows向けの完成版フォルダを安全に作成するビルドスクリプト。"""

from __future__ import annotations

import importlib
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist" / "cultivation-trimmer"
REQUIRED_MODULES = ("streamlit", "pandas", "numpy", "plotly", "openpyxl", "PyInstaller")
DISTRIBUTION_FILES = ("run.bat", "README_ja.md", "START_HERE.txt")


def check_dependencies() -> None:
    """ビルドに使うPythonから全依存パッケージが見えることを確認する。"""
    missing: list[str] = []
    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(f"必要なパッケージが見つかりません: {names}")


def streamlit_static_dir() -> Path:
    """インストール済みStreamlitのフロントエンド静的ファイル位置を返す。"""
    streamlit = importlib.import_module("streamlit")
    source = Path(streamlit.__file__).resolve().parent / "static"
    if not (source / "index.html").is_file():
        raise RuntimeError(f"Streamlitの画面ファイルが見つかりません: {source}")
    return source


def ensure_streamlit_static(source: Path, dist_dir: Path = DIST_DIR) -> Path:
    """PyInstaller配布物へStreamlitの画面ファイルを明示的にコピーして検証する。"""
    destination = dist_dir / "_internal" / "streamlit" / "static"
    shutil.copytree(source, destination, dirs_exist_ok=True)
    if not (destination / "index.html").is_file():
        raise RuntimeError(f"完成版へStreamlitの画面ファイルをコピーできませんでした: {destination}")
    return destination


def copy_distribution_files(dist_dir: Path = DIST_DIR) -> None:
    """一般利用者向けの起動ファイルと説明書だけを完成版へコピーする。"""
    for name in DISTRIBUTION_FILES:
        shutil.copy2(ROOT / name, dist_dir / name)


def build() -> None:
    """現在実行中のPython環境を使い、完成版を作成して検証する。"""
    check_dependencies()
    static_source = streamlit_static_dir()

    from PyInstaller.__main__ import run

    run(
        [
            "--noconfirm",
            "--clean",
            "--onedir",
            "--name=cultivation-trimmer",
            "--collect-all=streamlit",
            "--collect-all=plotly",
            "--hidden-import=pandas",
            "--hidden-import=numpy",
            "--hidden-import=openpyxl",
            "--hidden-import=core.constants",
            "--hidden-import=core.detect",
            "--hidden-import=core.export",
            "--hidden-import=core.merge",
            "--hidden-import=core.parser",
            f"--add-data={ROOT / 'app.py'}{os.pathsep}.",
            f"--add-data={ROOT / 'core'}{os.pathsep}core",
            str(ROOT / "launcher.py"),
        ]
    )

    ensure_streamlit_static(static_source)
    copy_distribution_files()
    print("\n完成版を作成しました:", DIST_DIR)
    print("Streamlit画面ファイルを確認しました:", DIST_DIR / "_internal" / "streamlit" / "static" / "index.html")


if __name__ == "__main__":
    try:
        build()
    except Exception as exc:
        print(f"\nビルドに失敗しました: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
