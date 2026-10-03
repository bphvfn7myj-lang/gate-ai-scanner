import math

def closes(candles):
    return [float(x["c"]) for x in candles]

def volumes(candles):
    # Gate's "sum" is quote volume.
    return [float(x.get("sum", 0)) for x in candles]

def ema(values, period):
    if len(values) < period:
        return values[-1] if values else 0.0
    k = 2 / (period + 1)
    e = sum(values[:period]) / period
    for v in values[period:]:
        e = v * k + e * (1-k)
    return e

def rsi(values, period=14):
    if len(values) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(values)):
        d = values[i] - values[i-1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0:
        return 100.0
    rs = ag / al
    return 100 - 100 / (1 + rs)

def atr(candles, period=14):
    if len(candles) < period + 1:
        return 0.0
    trs = []
    prev = float(candles[0]["c"])
    for x in candles[1:]:
        h, l = float(x["h"]), float(x["l"])
        trs.append(max(h-l, abs(h-prev), abs(l-prev)))
        prev = float(x["c"])
    return sum(trs[-period:]) / period

def features(candles):
    c = closes(candles)
    v = volumes(candles)
    last = c[-1]
    a = atr(candles)
    avg_vol = sum(v[-21:-1]) / max(1, len(v[-21:-1]))
    return {
        "last": last,
        "ema20": ema(c, 20),
        "ema50": ema(c, 50),
        "rsi14": rsi(c, 14),
        "atr14": a,
        "atr_pct": (a / last * 100) if last else 0,
        "vol_ratio": (v[-1] / avg_vol) if avg_vol else 0,
        "high_20": max(c[-20:]),
        "low_20": min(c[-20:]),
        "high_50": max(c[-50:]),
        "low_50": min(c[-50:]),
        "return_4": (last / c[-5] - 1) * 100 if len(c) >= 5 else 0,
        "return_20": (last / c[-21] - 1) * 100 if len(c) >= 21 else 0,
    }
