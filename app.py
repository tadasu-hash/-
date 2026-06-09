"""培養データ トリミング＆エクスポートアプリ。"""

from __future__ import annotations

import hashlib
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from core.constants import JARS
from core.detect import detect_interval
from core.export import build_excel
from core.merge import merge_logs
from core.parser import parse_logger_csv, to_jar_frame

st.set_page_config(page_title="培養データ トリミング＆エクスポート", layout="wide")
st.title("培養データ トリミング＆エクスポート")
st.caption("ロガーCSVを結合し、ジャーごとの有効培養区間を確認してExcelへ出力します。")

with st.sidebar:
    st.header("① CSVアップロード")
    uploaded = st.file_uploader("ロガーCSV（複数可）", type=["csv"], accept_multiple_files=True)
    order_label = st.radio("② 重複時の後優先順", ["ファイル名昇順", "ファイル選択順"])
    st.header("③ 自動検出パラメータ")
    start_threshold = st.number_input("開始しきい値（ポンプ）", value=5.0, step=0.1)
    pre_zero = st.number_input("直前のゼロ継続点数", min_value=1, value=2, step=1)
    rise_persist = st.number_input("立ち上がり継続点数", min_value=1, value=3, step=1)
    end_temp_threshold = st.number_input("終了しきい値（温度℃）", value=10.0, step=0.5)
    cool_persist = st.number_input("温度低下継続点数", min_value=1, value=3, step=1)
    noise_resistant = st.checkbox("ノイズ耐性を有効化", value=True)
    detect_all = st.button("④ 全ジャーを自動検出", use_container_width=True)
    st.header("⑤ 出力ジャー")
    selected_jars = [jar for jar in JARS if st.checkbox(f"ジャー{jar}", value=True, key=f"output_{jar}")]

if not uploaded:
    st.info("サイドバーからCSVファイルをアップロードしてください。先頭3行をヘッダーとして解析します。")
    st.stop()

try:
    parsed = [parse_logger_csv(file.getvalue(), file.name) for file in uploaded]
    merged, summary = merge_logs(parsed, "filename" if order_label == "ファイル名昇順" else "selection")
except Exception as exc:
    st.error(f"CSVの解析または結合に失敗しました: {exc}")
    st.stop()

signature = hashlib.sha1(order_label.encode() + b"|".join(f.name.encode() + b":" + f.getvalue() for f in uploaded)).hexdigest()
if st.session_state.get("data_signature") != signature:
    st.session_state.data_signature = signature
    st.session_state.selections = {jar: {"start_index": int(merged["index"].iloc[0]), "end_index": int(merged["index"].iloc[-1]), "mode": "manual", "warning": None} for jar in JARS}

parameters = {
    "START_THRESHOLD": start_threshold,
    "PRE_ZERO": int(pre_zero),
    "RISE_PERSIST": int(rise_persist),
    "END_TEMP_THRESHOLD": end_temp_threshold,
    "COOL_PERSIST": int(cool_persist),
    "NOISE_RESISTANT": noise_resistant,
}


def run_detection(jar: str) -> None:
    frame = to_jar_frame(merged, jar)
    result = detect_interval(frame, start_threshold, int(pre_zero), int(rise_persist), end_temp_threshold, int(cool_persist), noise_resistant)
    start_index = int(frame.iloc[result.start_pos]["index"])
    end_index = int(frame.iloc[result.end_pos]["index"])
    st.session_state.selections[jar] = {
        "start_index": start_index,
        "end_index": end_index,
        "mode": "auto",
        "warning": result.warning,
    }
    # 自動検出時は既存ウィジェットの表示値も同期する。
    for key, value in ((f"range_{jar}", (start_index, end_index)), (f"start_{jar}", start_index), (f"end_{jar}", end_index)):
        if key in st.session_state:
            st.session_state[key] = value


if detect_all:
    for jar in JARS:
        run_detection(jar)

c1, c2, c3, c4 = st.columns(4)
c1.metric("結合後行数", f"{summary.rows:,}")
c2.metric("期間", f"{summary.start_time:%Y/%m/%d %H:%M} ～ {summary.end_time:%Y/%m/%d %H:%M}" if summary.start_time is not None else "時刻なし")
c3.metric("重複解消件数", f"{summary.duplicates_resolved:,}")
c4.metric("欠落INDEX数", f"{summary.missing_indices:,}")
with st.expander("結合順と型情報を確認"):
    st.write(" → ".join(summary.file_order))
    st.dataframe(pd.DataFrame({"列名": parsed[-1].original_headers, "型定義": parsed[-1].type_definitions}), use_container_width=True)


def chart_for(frame: pd.DataFrame, start_index: int, end_index: int) -> go.Figure:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, subplot_titles=("ポンプ出力", "温度"))
    fig.add_trace(go.Scatter(x=frame["time"], y=frame["pump"], name="ポンプ出力", line={"color": "#1f77b4"}), row=1, col=1)
    fig.add_trace(go.Scatter(x=frame["time"], y=frame["temp"], name="温度", line={"color": "#ff7f0e"}), row=2, col=1)
    selected = frame[frame["index"].isin([start_index, end_index])].set_index("index")
    if start_index in selected.index and end_index in selected.index:
        start_time, end_time = selected.loc[start_index, "time"], selected.loc[end_index, "time"]
        fig.add_vrect(x0=start_time, x1=end_time, fillcolor="green", opacity=0.08, line_width=0, row="all", col=1)
        fig.add_vline(x=start_time, line_color="green", line_width=2, row="all", col=1)
        fig.add_vline(x=end_time, line_color="red", line_width=2, row="all", col=1)
    fig.update_layout(height=340, hovermode="x unified", margin={"t": 45, "b": 10, "l": 35, "r": 15}, legend={"orientation": "h"})
    return fig


tabs = st.tabs(["ジャー調整（A～D）", "エクスポート"])
indices = merged["index"].astype(int).tolist()
min_index, max_index = indices[0], indices[-1]


def sync_range(jar: str) -> None:
    requested_start, requested_end = st.session_state[f"range_{jar}"]
    start = max((i for i in indices if i <= requested_start), default=min_index)
    end = min((i for i in indices if i >= requested_end), default=max_index)
    st.session_state.selections[jar] = {"start_index": start, "end_index": end, "mode": "manual", "warning": None}
    st.session_state[f"range_{jar}"] = (start, end)
    st.session_state[f"start_{jar}"] = start
    st.session_state[f"end_{jar}"] = end


def apply_direct(jar: str) -> None:
    requested_start = min(st.session_state[f"start_{jar}"], st.session_state[f"end_{jar}"])
    requested_end = max(st.session_state[f"start_{jar}"], st.session_state[f"end_{jar}"])
    valid_start = max((i for i in indices if i <= requested_start), default=min_index)
    valid_end = min((i for i in indices if i >= requested_end), default=max_index)
    st.session_state.selections[jar] = {"start_index": valid_start, "end_index": valid_end, "mode": "manual", "warning": None}
    st.session_state[f"range_{jar}"] = (valid_start, valid_end)


def render_jar_panel(jar: str) -> None:
    """2列×2段レイアウト内にジャーの調整UIを描画する。"""
    frame = to_jar_frame(merged, jar)
    st.subheader(f"ジャー{jar}")
    if st.button(f"ジャー{jar}を自動検出", key=f"detect_{jar}", use_container_width=True):
        run_detection(jar)
    selection = st.session_state.selections[jar]
    st.slider("選択区間（INDEX）", min_value=min_index, max_value=max_index, value=(selection["start_index"], selection["end_index"]), key=f"range_{jar}", on_change=sync_range, args=(jar,))
    direct1, direct2 = st.columns(2)
    direct1.number_input("開始INDEX", min_value=min_index, max_value=max_index, value=selection["start_index"], key=f"start_{jar}")
    direct2.number_input("終了INDEX", min_value=min_index, max_value=max_index, value=selection["end_index"], key=f"end_{jar}")
    st.button("直接入力を適用", key=f"apply_{jar}", on_click=apply_direct, args=(jar,), use_container_width=True)
    selection = st.session_state.selections[jar]
    if selection.get("warning"):
        st.warning(selection["warning"])
    start_row = frame.loc[frame["index"].eq(selection["start_index"])].iloc[0]
    end_row = frame.loc[frame["index"].eq(selection["end_index"])].iloc[0]
    st.caption(f"開始: {selection['start_index']} / {start_row['time']}　終了: {selection['end_index']} / {end_row['time']}　設定: {selection['mode']}")
    st.plotly_chart(chart_for(frame, selection["start_index"], selection["end_index"]), use_container_width=True, config={"displaylogo": False})


with tabs[0]:
    for row_jars in (JARS[:2], JARS[2:]):
        columns = st.columns(2)
        for column, jar in zip(columns, row_jars):
            with column:
                with st.container(border=True):
                    render_jar_panel(jar)

with tabs[1]:
    st.subheader("Excelエクスポート")
    include_merged = st.checkbox("結合元データシートを含める", value=False)
    st.write("出力対象: " + (", ".join(f"Jar{jar}" for jar in selected_jars) if selected_jars else "未選択"))
    st.caption("選択した全ジャーを1枚の「トリミングデータ」シートへまとめ、開始点を0:00とする5分刻みの経過時間と、項目別の散布図を出力します。")
    try:
        excel = build_excel(merged, st.session_state.selections, selected_jars, parameters, include_merged)
        st.download_button("⑥ Excelをダウンロード", excel, file_name=f"培養トリミング_{datetime.now():%Y%m%d_%H%M}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    except ValueError as exc:
        st.warning(str(exc))
