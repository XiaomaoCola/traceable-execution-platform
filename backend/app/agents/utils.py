import json


def sse(payload: dict) -> str:
# SSE = Server-Sent Events  ，  本质是服务器不断往前端“推消息” 。
# 把一个 Python dict 转成 SSE 协议格式字符串。
    """把 Python dict 转成 SSE 协议格式字符串，推送给前端。"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    # json.dumps(...) 的作用是， 把 Python 对象转成 JSON 格式的字符串。
    # ensure_ascii=False 是 控制中文怎么显示。 你好 可能会变成 \u4f60\u597d， 也就是中文被转义。