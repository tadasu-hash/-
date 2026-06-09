"""ロガーCSVを位置ベースで安全に解析する。"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from .constants import COLMAP, JARS, METRICS


@dataclass
class ParsedLog:
    """解析済みロガーファイル。"""

    name: str
    data: pd.DataFrame
    type_definitions: list[str]
    original_headers: list[str]


def _read_bytes(source: bytes | bytearray | BinaryIO | str | Path) -> bytes:
    if isinstance(source, (bytes, bytearray)):
        return bytes(source)
    if isinstance(source, (str, Path)):
        return Path(source).read_bytes()
    source.seek(0)
    return source.read()


def _decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp932", "shift_jis", "utf-8"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def parse_logger_csv(source: bytes | bytearray | BinaryIO | str | Path, name: str | None = None) -> ParsedLog:
    """先頭3行を解析し、26列を位置ベースの正規化列名へ変換する。"""
    raw = _read_bytes(source)
    rows = list(csv.reader(io.StringIO(_decode(raw))))
    if len(rows) < 3:
        raise ValueError("CSVには先頭3行のヘッダーが必要です。")
    if len(rows[2]) < 26:
        raise ValueError(f"CSVの列数が不足しています（{len(rows[2])}列、必要数26列）。")

    type_defs = (rows[1] + [""] * 26)[:26]
    headers = (rows[2] + [""] * 26)[:26]
    body = [((row + [""] * 26)[:26]) for row in rows[3:] if any(cell.strip() for cell in row)]
    frame = pd.DataFrame(body)
    frame.columns = ["time", "index"] + [f"{jar}_{metric}" for jar in JARS for metric in METRICS]
    frame["time"] = pd.to_datetime(frame["time"], errors="coerce")
    frame["index"] = pd.to_numeric(frame["index"], errors="coerce")
    for jar in JARS:
        for metric in METRICS:
            frame[f"{jar}_{metric}"] = pd.to_numeric(frame[f"{jar}_{metric}"], errors="coerce")
    frame = frame.dropna(subset=["index"]).copy()
    frame["index"] = frame["index"].astype("int64")
    return ParsedLog(name=name or getattr(source, "name", "uploaded.csv"), data=frame, type_definitions=type_defs, original_headers=headers)


def to_jar_frame(data: pd.DataFrame, jar: str) -> pd.DataFrame:
    """結合済みワイド形式から指定ジャーの8列を作る。"""
    if jar not in COLMAP:
        raise ValueError(f"未知のジャーです: {jar}")
    result = data[["time", "index"] + [f"{jar}_{m}" for m in METRICS]].copy()
    return result.rename(columns={f"{jar}_{m}": m for m in METRICS})
