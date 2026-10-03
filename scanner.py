import time
from datetime import datetime, timezone
from gate_api import GateAPI, as_float
from indicators import features

class Scanner:
    def __init__(self, top_n=12, ai_n=8, min_volume=5_000_000):
        self.g = GateAPI()
        self.top_n = top_n
        self.ai_n = ai_n
        self.min_volume = min_volume

    def market_snapshot(self):
        contracts = self.g.contracts()
        allowed = {
            x["name"]: x for x in contracts
            if x.get("name","").endswith("_USDT")
            and not x.get("in_delisting", False)
            and x.get("type") == "direct"
        }
        tickers = self.g.tickers()
        rows = []
        for t in tickers:
            sym = t.get("contract")
            if sym not in allowed:
                continue
            qv = as_float(t.get("volume_24h_quote"))
            last = as_float(t.get("last"))
            change = as_float(t.get("change_percentage"))
            if qv < self.min_volume or last <= 0:
                continue
            rows.append({
                "symbol": sym,
                "last": last,
                "change_24h_pct": change,
                "volume_24h_quote": qv,
                "funding_rate": as_float(allowed[sym].get("funding_rate")),
                "mark_price": as_float(allowed[sym].get("mark_price")),
            })
        rows.sort(key=lambda x: x["volume_24h_quote"], reverse=True)
        return rows[:self.top_n]

    def enrich(self, row):
        sym = row["symbol"]
        c15 = self.g.candles(sym, "15m", 200)
        c1h = self.g.candles(sym, "1h", 200)
        f15, f1h = features(c15), features(c1h)
        stats = self.g.stats(sym, "1h", 2)
        oi = as_float(stats[-1].get("open_interest_usd")) if stats else 0
        prev_oi = as_float(stats[-2].get("open_interest_usd")) if len(stats) > 1 else oi
        oi_change = ((oi / prev_oi) - 1) * 100 if prev_oi else 0
        return {
            **row,
            "tf15": f15,
            "tf1h": f1h,
            "open_interest_usd": oi,
            "oi_change_pct": oi_change,
        }

    def scan(self):
        base = self.market_snapshot()
        enriched = []
        for row in base:
            try:
                e = self.enrich(row)
                # Simple prefilter: trend/volume/volatility/structure
                score = 0
                f15, f1h = e["tf15"], e["tf1h"]
                if f1h["ema20"] > f1h["ema50"]: score += 2
                if f1h["ema20"] < f1h["ema50"]: score += 2
                if f15["vol_ratio"] >= 1.5: score += 2
                if abs(f15["return_20"]) >= 2: score += 1
                if e["oi_change_pct"] >= 2: score += 1
                e["prefilter_score"] = score
                enriched.append(e)
            except Exception as ex:
                row["error"] = str(ex)
        enriched.sort(key=lambda x: x["prefilter_score"], reverse=True)
        return enriched[:self.ai_n]

def compact_for_ai(items):
    out = []
    for x in items:
        out.append({
            "symbol": x["symbol"],
            "last": x["last"],
            "change_24h_pct": x["change_24h_pct"],
            "volume_24h_quote": x["volume_24h_quote"],
            "funding_rate": x["funding_rate"],
            "mark_price": x["mark_price"],
            "open_interest_usd": x["open_interest_usd"],
            "oi_change_pct": x["oi_change_pct"],
            "tf15": x["tf15"],
            "tf1h": x["tf1h"],
        })
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "universe": "Gate USDT perpetuals only",
        "candidates": out
    }
