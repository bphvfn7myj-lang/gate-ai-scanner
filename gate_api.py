import requests
import time

BASE = "https://api.gateio.ws/api/v4"

class GateAPI:
    def __init__(self, timeout=15):
        self.timeout = timeout
        self.s = requests.Session()
        self.s.headers.update({"Accept": "application/json", "Content-Type": "application/json"})

    def get(self, path, params=None):
        r = self.s.get(BASE + path, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def contracts(self):
        return self.get("/futures/usdt/contracts")

    def tickers(self):
        return self.get("/futures/usdt/tickers")

    def candles(self, contract, interval="15m", limit=200):
        return self.get("/futures/usdt/candlesticks", {
            "contract": contract, "interval": interval, "limit": limit
        })

    def stats(self, contract, interval="1h", limit=2):
        return self.get("/futures/usdt/contract_stats", {
            "contract": contract, "interval": interval, "limit": limit
        })

    def funding(self, contract, limit=1):
        return self.get("/futures/usdt/funding_rate", {
            "contract": contract, "limit": limit
        })

def as_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default
