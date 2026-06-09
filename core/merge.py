"""複数ロガーCSVの後優先マージ。"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .parser import ParsedLog


@dataclass
class MergeSummary:
    rows: int
    start_time: pd.Timestamp | None
    end_time: pd.Timestamp | None
    duplicates_resolved: int
    missing_indices: int
    file_order: list[str]


def merge_logs(logs: list[ParsedLog], order: str = "filename") -> tuple[pd.DataFrame, MergeSummary]:
    """INDEXでソートし、重複は順序上で後のファイルを優先する。"""
    if not logs:
        raise ValueError("結合するCSVがありません。")
    ordered = sorted(logs, key=lambda item: item.name.casefold()) if order == "filename" else list(logs)
    combined = pd.concat([log.data.assign(_file_order=i) for i, log in enumerate(ordered)], ignore_index=True)
    before = len(combined)
    combined = combined.sort_values(["index", "_file_order"], kind="stable").drop_duplicates("index", keep="last")
    combined = combined.sort_values("index", kind="stable").drop(columns="_file_order").reset_index(drop=True)
    indices = combined["index"]
    missing = int(max(0, indices.max() - indices.min() + 1 - len(indices))) if len(indices) else 0
    valid_time = combined["time"].dropna()
    summary = MergeSummary(
        rows=len(combined),
        start_time=valid_time.min() if not valid_time.empty else None,
        end_time=valid_time.max() if not valid_time.empty else None,
        duplicates_resolved=before - len(combined),
        missing_indices=missing,
        file_order=[log.name for log in ordered],
    )
    return combined, summary
