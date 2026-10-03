import os
import json
import threading
import time
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from scanner import Scanner, compact_for_ai
from ai_analyzer import analyze
import requests

load_dotenv()

SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL_SEC", "300"))
TOP = int(os.getenv("TOP_CANDIDATES", "12"))
AI_N = int(os.getenv("AI_CANDIDATES", "8"))
MIN_VOL = float(os.getenv("MIN_24H_VOLUME_USDT", "5000000"))
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/auto")

app = Flask(__name__)

state = {
    "status": "starting",
    "last_scan": None,
    "market": None,
    "opportunities": [],
    "error": None
}

lock = threading.Lock()


def telegram(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat:
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat,
                "text": text
            },
            timeout=10
        )
    except Exception:
        pass


def format_alert(result):
    lines = [
        f"Gate AI 扫描｜{result.get('market_state', '')}",
        result.get("summary", "")
    ]

    for o in result.get("opportunities", [])[:3]:
        lines += [
            "",
            f"{o['symbol']}｜{o['direction']}｜置信度 {o['confidence']:.0f}",
            f"入场 {o['entry_low']} - {o['entry_high']}",
            f"SL {o['stop']}｜TP1 {o['tp1']}｜TP2 {o['tp2']}",
            f"R:R {o['rr_tp1']:.2f} / {o['rr_tp2']:.2f}",
            f"逻辑：{o['reason']}",
            f"触发：{o['trigger']}",
            f"失效：{o['invalid_if']}",
        ]

    return "\n".join(lines)


def run_once():
    scanner = Scanner(TOP, AI_N, MIN_VOL)

    data = scanner.scan()
    payload = compact_for_ai(data)

    result = analyze(payload, MODEL)

    with lock:
        state["status"] = "running"
        state["last_scan"] = payload["generated_at_utc"]
        state["market"] = result.get("market_state")
        state["opportunities"] = result.get("opportunities", [])
        state["error"] = None

    telegram(format_alert(result))

    return result


def worker():
    while True:
        try:
            run_once()

        except Exception as e:
            with lock:
                state["status"] = "error"
                state["error"] = str(e)

        time.sleep(SCAN_INTERVAL)


@app.get("/")
def home():
    return """
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Gate AI Scanner</title>
        <meta name='viewport' content='width=device-width, initial-scale=1'>
    </head>

    <body style='font-family:-apple-system;padding:20px'>
        <h2>Gate AI Scanner</h2>
        <p>只读｜Gate USDT 永续｜AI 二次分析</p>

        <pre id='x'>加载中...</pre>

        <script>
        async function f(){
            const r = await fetch('/api/state');
            const j = await r.json();
            document.getElementById('x').textContent =
                JSON.stringify(j, null, 2);
        }

        f();
        setInterval(f, 15000);
        </script>
    </body>
    </html>
    """


@app.get("/api/state")
def api_state():
    with lock:
        return jsonify(state)


@app.get("/api/scan")
def api_scan():
    token = os.getenv("SCANNER_API_TOKEN")
    auth = request.headers.get("Authorization", "")

    if not token or auth != f"Bearer {token}":
        return jsonify({
            "error": "unauthorized"
        }), 401

    try:
        result = run_once()
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    threading.Thread(
        target=worker,
        daemon=True
    ).start()

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080"))
    )
