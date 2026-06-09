"""アプリ全体で使用する列定義。"""

JARS = ["A", "B", "C", "D"]
METRICS = ["scale", "alcohol", "pump", "ph", "do", "temp"]
COLMAP = {
    jar: {metric: 2 + jar_pos * 6 + metric_pos for metric_pos, metric in enumerate(METRICS)}
    for jar_pos, jar in enumerate(JARS)
}
DECIMALS = {"scale": 3, "alcohol": 0, "pump": 1, "ph": 1, "do": 2, "temp": 1}
METRIC_LABELS = {
    "scale": "はかり重量",
    "alcohol": "アルコール",
    "pump": "ポンプ出力",
    "ph": "pH",
    "do": "DO",
    "temp": "温度",
}
