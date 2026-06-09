"""トリミング済みデータとネイティブグラフをExcelへ出力する。"""

from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from .constants import DECIMALS, JARS, METRICS, METRIC_LABELS
from .parser import to_jar_frame

HEADERS = ["TIME", "INDEX"] + [METRIC_LABELS[m] for m in METRICS]


def _write_dataframe(ws, frame: pd.DataFrame, headers: list[str], metric_offset: int = 2) -> None:
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="4472C4")
    for row in frame.itertuples(index=False, name=None):
        ws.append(list(row))
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 12
    for row in range(2, ws.max_row + 1):
        ws.cell(row, 1).number_format = "yyyy/mm/dd hh:mm"
        for metric_pos, metric in enumerate(METRICS, start=metric_offset + 1):
            ws.cell(row, metric_pos).number_format = "0" if DECIMALS[metric] == 0 else "0." + "0" * DECIMALS[metric]


def _add_charts(ws) -> None:
    if ws.max_row < 2:
        return
    categories = Reference(ws, min_col=1, min_row=2, max_row=ws.max_row)
    for position, metric in enumerate(METRICS):
        chart = LineChart()
        chart.title = f"{METRIC_LABELS[metric]}の推移"
        chart.y_axis.title = METRIC_LABELS[metric]
        chart.x_axis.title = "時刻"
        chart.height = 7.0
        chart.width = 13.0
        data_col = 3 + position
        chart.add_data(Reference(ws, min_col=data_col, min_row=1, max_row=ws.max_row), titles_from_data=True)
        chart.set_categories(categories)
        chart.legend = None
        chart.style = 13
        ws.add_chart(chart, f"K{2 + position * 15}")


def build_excel(merged: pd.DataFrame, selections: dict[str, dict[str, Any]], selected_jars: list[str], parameters: dict[str, Any], include_merged: bool = False) -> bytes:
    """現在の選択区間からExcelワークブックを生成する。"""
    if not selected_jars:
        raise ValueError("出力対象ジャーを1つ以上選択してください。")
    workbook = Workbook()
    summary = workbook.active
    summary.title = "概要"
    summary.append(["ジャー", "開始INDEX", "開始時刻", "終了INDEX", "終了時刻", "行数", "設定方法"])
    for cell in summary[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="4472C4")

    for jar in selected_jars:
        if jar not in JARS:
            continue
        selection = selections[jar]
        jar_frame = to_jar_frame(merged, jar)
        trimmed = jar_frame[jar_frame["index"].between(selection["start_index"], selection["end_index"], inclusive="both")].copy()
        start = trimmed.iloc[0] if not trimmed.empty else None
        end = trimmed.iloc[-1] if not trimmed.empty else None
        summary.append([jar, None if start is None else int(start["index"]), None if start is None else start["time"], None if end is None else int(end["index"]), None if end is None else end["time"], len(trimmed), selection.get("mode", "manual")])
        ws = workbook.create_sheet(f"Jar{jar}")
        _write_dataframe(ws, trimmed[["time", "index"] + METRICS], HEADERS)
        _add_charts(ws)

    summary.append([])
    summary.append(["自動検出パラメータ", "値"])
    for key, value in parameters.items():
        summary.append([key, value])
    summary.column_dimensions["A"].width = 24
    for column in range(2, 8):
        summary.column_dimensions[get_column_letter(column)].width = 20
    for row in range(2, 2 + len(selected_jars)):
        summary.cell(row, 3).number_format = "yyyy/mm/dd hh:mm"
        summary.cell(row, 5).number_format = "yyyy/mm/dd hh:mm"

    if include_merged:
        ws = workbook.create_sheet("結合元データ")
        raw_headers = ["TIME", "INDEX"] + [f"{jar} {METRIC_LABELS[m]}" for jar in JARS for m in METRICS]
        _write_dataframe(ws, merged, raw_headers)

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
