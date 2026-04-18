from __future__ import annotations

from datetime import datetime

import httpx

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_date",
            "description": "获取今天的日期和星期",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市今天的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名，如 '上海'、'Beijing'",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_zodiac",
            "description": "根据出生日期推算星座、生肖和五行",
            "parameters": {
                "type": "object",
                "properties": {
                    "birth_date": {
                        "type": "string",
                        "description": "出生日期，格式 YYYY-MM-DD，如 '1990-05-15'",
                    }
                },
                "required": ["birth_date"],
            },
        },
    },
]


def _get_current_date() -> str:
    now = datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return f"{now.year}年{now.month}月{now.day}日，{weekdays[now.weekday()]}"


async def _get_weather(city: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=8.0, trust_env=False) as client:
            resp = await client.get(
                f"https://wttr.in/{city}?format=3",
                headers={"User-Agent": "curl/7.68.0"},
            )
        return resp.text.strip() if resp.status_code == 200 else f"天气查询失败（{resp.status_code}）"
    except Exception as exc:
        return f"天气查询失败：{exc}"


def _get_zodiac(birth_date: str) -> str:
    try:
        dt = datetime.strptime(birth_date, "%Y-%m-%d")
    except ValueError:
        return "日期格式错误，请用 YYYY-MM-DD"

    month, day = dt.month, dt.day
    signs = [
        (1, 20, "水瓶座"), (2, 19, "双鱼座"), (3, 21, "白羊座"),
        (4, 20, "金牛座"), (5, 21, "双子座"), (6, 21, "巨蟹座"),
        (7, 23, "狮子座"), (8, 23, "处女座"), (9, 23, "天秤座"),
        (10, 23, "天蝎座"), (11, 22, "射手座"), (12, 22, "摩羯座"),
    ]
    zodiac = "摩羯座"
    for m, d, name in signs:
        if month == m and day >= d:
            zodiac = name
            break
        if month == m + 1 and day < d:
            zodiac = name
            break

    animals = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
    shengxiao = animals[(dt.year - 4) % 12]

    wuxing = {0: "金", 1: "金", 2: "水", 3: "水", 4: "木", 5: "木", 6: "火", 7: "火", 8: "土", 9: "土"}[dt.year % 10]

    return f"星座：{zodiac} | 生肖：属{shengxiao} | 五行属{wuxing}"


async def execute_tool(name: str, args: dict) -> str:
    if name == "get_current_date":
        return _get_current_date()
    if name == "get_weather":
        return await _get_weather(args.get("city", "上海"))
    if name == "get_zodiac":
        return _get_zodiac(args.get("birth_date", ""))
    return f"未知工具：{name}"
