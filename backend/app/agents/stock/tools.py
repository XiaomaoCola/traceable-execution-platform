from __future__ import annotations

import re

import httpx

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_astock_indices",
            "description": "获取 A 股三大指数（上证指数、深证成指、创业板指）的实时行情",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "predict_trend",
            "description": "自动获取指定 A 股指数的实时价格，再用动量模型计算未来 N 个交易日的价格区间预测",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol_name": {
                        "type": "string",
                        "description": "指数名称，必须是以下之一：「上证指数」「深证成指」「创业板指」",
                    },
                    "days": {
                        "type": "integer",
                        "description": "预测天数，默认 5",
                    },
                },
                "required": ["symbol_name"],
            },
        },
    },
]

NAME_TO_SYMBOL = {
    "上证指数": "sh000001",
    "深证成指": "sz399001",
    "创业板指": "sz399006",
}


async def _get_astock_indices() -> str:
    symbols = "sh000001,sz399001,sz399006"
    try:
        async with httpx.AsyncClient(timeout=8.0, trust_env=False) as client:
            resp = await client.get(
                f"https://hq.sinajs.cn/list={symbols}",
                headers={"Referer": "https://finance.sina.com.cn"},
            )
        if resp.status_code != 200:
            return f"行情获取失败（HTTP {resp.status_code}）"

        text = resp.content.decode("gbk", errors="replace")

        results = []
        names = {"sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指"}
        for sym, display in names.items():
            match = re.search(rf'hq_str_{sym}="([^"]+)"', text)
            if not match:
                continue
            fields = match.group(1).split(",")
            if len(fields) < 10:
                continue
            cur  = float(fields[3])
            prev = float(fields[2])
            high = float(fields[4])
            low  = float(fields[5])
            chg  = cur - prev
            pct  = chg / prev * 100
            sign = "+" if chg >= 0 else ""
            results.append(
                f"{display}：{cur:.2f}  {sign}{chg:.2f}（{sign}{pct:.2f}%）"
                f"  今日区间 {low:.2f}~{high:.2f}"
            )

        return "\n".join(results) if results else "未能解析行情数据"
    except Exception as exc:
        return f"行情获取异常：{exc}"


async def _predict_trend(symbol_name: str, days: int = 5) -> str:
    sym = NAME_TO_SYMBOL.get(symbol_name)
    if not sym:
        return f"不支持的指数名称：{symbol_name}，请用「上证指数」「深证成指」或「创业板指」"

    try:
        async with httpx.AsyncClient(timeout=8.0, trust_env=False) as client:
            resp = await client.get(
                f"https://hq.sinajs.cn/list={sym}",
                headers={"Referer": "https://finance.sina.com.cn"},
            )
        text = resp.content.decode("gbk", errors="replace")
        match = re.search(rf'hq_str_{sym}="([^"]+)"', text)
        if not match:
            return "行情数据解析失败"
        fields = match.group(1).split(",")
        current_price = float(fields[3])
        prev_close    = float(fields[2])
        change_pct    = (current_price - prev_close) / prev_close * 100
    except Exception as exc:
        return f"获取行情失败：{exc}"

    # 动量模型：以今日涨跌幅的 30% 作为每日衰减动量，±1.2% 作为日波动带
    momentum   = change_pct * 0.30
    volatility = current_price * 0.012

    lines = [f"【{symbol_name}】当前 {current_price:.2f}，今日{'+' if change_pct >= 0 else ''}{change_pct:.2f}%"]
    lines.append(f"未来 {days} 个交易日预测区间（动量模型）：")
    price = current_price
    for i in range(1, days + 1):
        price = price * (1 + momentum / 100)
        lines.append(f"  第 {i} 日：{price - volatility:.2f} ~ {price + volatility:.2f}（中枢 {price:.2f}）")

    trend = "震荡偏多" if momentum > 0.1 else ("震荡偏空" if momentum < -0.1 else "窄幅震荡")
    lines.append(f"趋势判断：{trend}  |  模型置信度：低（仅供参考）")
    return "\n".join(lines)


async def execute_tool(name: str, args: dict) -> str:
    if name == "get_astock_indices":
        return await _get_astock_indices()
    if name == "predict_trend":
        return await _predict_trend(
            symbol_name=args.get("symbol_name", "上证指数"),
            days=int(args.get("days", 5)),
        )
    return f"未知工具：{name}"
