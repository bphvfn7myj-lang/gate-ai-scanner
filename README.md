# Gate AI Scanner

Gate USDT 永续合约 + AI 市场扫描器（只读版）。

功能：
- 读取 Gate USDT 永续合约公开行情
- 自动过滤无流动性/退市合约
- 计算 EMA、RSI、ATR、成交量异常、近期高低点
- 读取资金费率、持仓量（OI）等可用数据
- 先用量化规则筛选，再交给 OpenAI 做二次分析
- 最多输出 3 个候选机会；没有符合条件时输出 WAIT
- 给出方向、入场区、止损、TP1、TP2、R:R、触发条件和失效条件
- 可选 Telegram 通知
- 默认绝不下单，不需要 Gate API Secret

## 安全原则

第一版只读取公开 Gate 市场数据，不连接你的 Gate 私有账户，也不会下单。
以后如果增加账户数据，只使用只读权限；不要把提现/交易权限交给程序。

## 环境变量

复制 `.env.example` 为 `.env`：

- `OPENAI_API_KEY`：OpenAI API Key（必须）
- `OPENAI_MODEL`：默认 `gpt-5.6`
- `SCAN_INTERVAL_SEC`：扫描间隔，默认 300 秒
- `TOP_CANDIDATES`：量化预筛选数量，默认 12
- `AI_CANDIDATES`：交给 AI 深度分析的数量，默认 8
- `TELEGRAM_BOT_TOKEN`：可选
- `TELEGRAM_CHAT_ID`：可选

## 本地运行

```bash
pip install -r requirements.txt
python main.py
```

打开：
`http://127.0.0.1:8080`

## 部署

适合部署到任何支持 Python 长时间运行进程的云服务器。
程序会持续扫描；iPad 只需要打开网页看结果，Telegram 可作为主动提醒。

Gate API 使用官方公开 REST 接口，例如 USDT 永续合约、K 线、资金费率和合约统计。详见：
https://www.gate.com/docs/developers/apiv4/en/futures/

OpenAI 使用 Responses API。API Key 只放在云服务器的环境变量里，不要放进 GitHub 代码。
