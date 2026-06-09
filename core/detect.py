"""ポンプ立ち上がりと温度低下による培養区間検出。"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DetectionResult:
    start_pos: int
    end_pos: int
    start_detected: bool
    end_detected: bool
    warning: str | None = None


def detect_start(pump: pd.Series, threshold: float = 5.0, pre_zero: int = 2, rise_persist: int = 3, noise_resistant: bool = True) -> int | None:
    """持続する立ち上がり直前の0の位置を返す。"""
    values = pd.to_numeric(pump, errors="coerce").to_numpy(dtype=float)
    required_pre = pre_zero if noise_resistant else 1
    required_rise = rise_persist if noise_resistant else 1
    for i in range(required_pre, len(values)):
        pre = values[i - required_pre : i]
        rise = values[i : i + required_rise]
        if len(rise) == required_rise and np.all(np.isfinite(pre)) and np.all(pre == 0) and np.all(np.isfinite(rise)) and np.all(rise >= threshold):
            return i - 1
    return None


def detect_end(temp: pd.Series, start_pos: int, threshold: float = 10.0, cool_persist: int = 3, noise_resistant: bool = True) -> int | None:
    """開始以降で持続する温度低下の最初の位置を返す。"""
    values = pd.to_numeric(temp, errors="coerce").to_numpy(dtype=float)
    required = cool_persist if noise_resistant else 1
    for i in range(max(0, start_pos), len(values)):
        window = values[i : i + required]
        if len(window) == required and np.all(np.isfinite(window)) and np.all(window < threshold):
            return i
    return None


def detect_interval(frame: pd.DataFrame, start_threshold: float = 5.0, pre_zero: int = 2, rise_persist: int = 3, end_temp_threshold: float = 10.0, cool_persist: int = 3, noise_resistant: bool = True) -> DetectionResult:
    """ジャーデータの開始・終了を検出し、不成立時は安全に全区間へ戻す。"""
    if frame.empty:
        raise ValueError("自動検出するデータがありません。")
    start = detect_start(frame["pump"], start_threshold, pre_zero, rise_persist, noise_resistant)
    if start is None:
        return DetectionResult(0, len(frame) - 1, False, False, "ポンプ立ち上がりを検出できないため、全区間を選択しました。")
    end = detect_end(frame["temp"], start, end_temp_threshold, cool_persist, noise_resistant)
    if end is None:
        return DetectionResult(start, len(frame) - 1, True, False, "温度低下を検出できないため、終了点をデータ末尾にしました。")
    return DetectionResult(start, end, True, True)
