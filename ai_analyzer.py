import json
import os
from openai import OpenAI

SYSTEM = """你是一个加密永续合约市场研究分析器。

你的任务不是保证盈利，而是在给定 Gate USDT 永续市场数据后，
判断是否存在“值得等待触发”的交易计划。

严格规则：
1. 只能使用输入数据，不得编造新闻、价格、OI或资金费率。
2. 最多选择 3 个候选。
3. 如果数据不足、结构混乱、盈亏比不足或风险太高，输出 WAIT。
4. 不追涨杀跌。入场区必须有逻辑；若只能追价，输出 WAIT。
5. 止损必须位于交易逻辑失效的位置，而不是随意给百分比。
6. TP1/TP2 必须基于近期结构和风险收益比。
7. direction 只能是 LONG、SHORT、WAIT。
8. confidence 为 0-100。
9. 输出简洁中文。
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "market_state": {
            "type": "string"
        },
        "summary": {
            "type": "string"
        },
        "opportunities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "direction": {
                        "type": "string",
                        "enum": ["LONG", "SHORT", "WAIT"]
                    },
                    "entry_low": {"type": "number"},
                    "entry_high": {"type": "number"},
                    "stop": {"type": "number"},
                    "tp1": {"type": "number"},
                    "tp2": {"type": "number"},
                    "rr_tp1": {"type": "number"},
                    "rr_tp2": {"type": "number"},
                    "confidence": {"type": "number"},
                    "reason": {"type": "string"},
                    "trigger": {"type": "string"},
                    "invalid_if": {"type": "string"}
                },
                "required": [
                    "symbol",
                    "direction",
                    "entry_low",
                    "entry_high",
                    "stop",
                    "tp1",
                    "tp2",
                    "rr_tp1",
                    "rr_tp2",
                    "confidence",
                    "reason",
                    "trigger",
                    "invalid_if"
                ],
                "additionalProperties": False
            }
        }
    },
    "required": [
        "market_state",
        "summary",
        "opportunities"
    ],
    "additionalProperties": False
}


def analyze(payload, model=None):
    api_key = os.environ["OPENROUTER_API_KEY"]

    # OpenRouter 模型名使用 provider/model 格式。
    # 默认使用 GPT-5.6 Luna。
    model = model or os.getenv(
        "OPENROUTER_MODEL",
        "openai/gpt-5.6-luna"
    )

    # 兼容原来的 workflow。
    if model == "gpt-5.6":
        model = os.getenv(
            "OPENROUTER_MODEL",
            "openai/gpt-5.6-luna"
        )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    prompt = """下面是 Gate USDT 永续合约扫描器的结构化数据。

请进行二次分析，找出最多3个值得等待触发的机会。

如果没有足够好的机会：
opportunities 返回空数组。

不要为了凑数量而强行给交易机会。

市场数据：
""" + json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":")
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "gate_scan",
                "strict": True,
                "schema": SCHEMA
            }
        },
        temperature=0.2
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("OpenRouter 返回为空")

    return json.loads(content)
