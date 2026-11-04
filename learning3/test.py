
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key= os.getenv("OPENAI_API_KEY"),
    base_url= os.getenv("OPENAI_BASE_URL"),
)
MODEL = os.getenv("OPENAI_MODEL")

# 1. 模拟订单数据库
ORDER_DB = {
    "A1001": {
        "status": "已发货",
        "carrier": "顺丰速运",
        "tracking_number": "SF1234567890",
    },
    "A1002": {
        "status": "处理中",
        "carrier": None,
        "tracking_number": None,
    },
}

# 2. 告诉模型：我提供了什么工具，以及参数是什么
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "根据订单编号查询订单状态和物流信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单编号，例如 A1001",
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    }
]


# 3. 真正执行工具的 Python 函数
def get_order_status(order_id: str) -> dict:
    order = ORDER_DB.get(order_id)

    if order is None:
        return {
            "found": False,
            "order_id": order_id,
            "message": "没有找到该订单",
        }

    return {
        "found": True,
        "order_id": order_id,
        **order,
    }


# 模型给出工具名称后，我们从这里找到对应函数
AVAILABLE_TOOLS = {
    "get_order_status": get_order_status,
}


def chat_with_agent(user_text: str, max_turns: int = 5):
    messages = [
        {
            "role": "system",
            "content": (
                "你是中文客服。用户询问订单状态或物流时，"
                "调用 get_order_status 工具；"
                "必须根据工具返回结果回答，不要编造订单信息。"
            ),
        },
        {
            "role": "user",
            "content": user_text,
        },
    ]

    # 4. Agent 循环：可能先调用工具，再生成最终回答
    for turn in range(max_turns):
        print(f"\n[模型第 {turn + 1} 轮]")

        text_parts = []

        # 工具调用信息可能分成多个 chunk 返回
        tool_calls = {}

        # 5. 本轮模型请求开启流式输出
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            stream=True,
        )

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # 6. 普通文本：收到一段就输出一段
            if delta.content:
                print(delta.content, end="", flush=True)
                text_parts.append(delta.content)

            # 7. 工具调用：逐步累积名称和参数
            if delta.tool_calls:
                for part in delta.tool_calls:
                    print(type(part),part)
                    index = part.index

                    if index not in tool_calls:
                        tool_calls[index] = {
                            "id": "",
                            "name": "",
                            "arguments": "",
                        }

                    current = tool_calls[index]

                    if part.id:
                        current["id"] = part.id

                    if part.function:
                        if part.function.name:
                            current["name"] += part.function.name

                        if part.function.arguments:
                            current["arguments"] += (
                                part.function.arguments
                            )

        if text_parts:
            print()

        # 8. 本轮没有工具调用，说明可以结束
        if not tool_calls:
            return

        # 9. 把收集完整的工具调用写入对话历史
        full_tool_calls = []

        for index in sorted(tool_calls):#sorted({"b": 2, "a": 1}) # ['a', 'b']   ← 只排键！值没了！
            call = tool_calls[index]

            full_tool_calls.append({
                "id": call["id"],
                "type": "function",
                "function": {
                    "name": call["name"],
                    "arguments": call["arguments"],
                },
            })

        messages.append({
            "role": "assistant",
            "content": "".join(text_parts) or None,
            "tool_calls": full_tool_calls,
        })

        # 10. 由 Python 真正执行工具
        for call in full_tool_calls:
            name = call["function"]["name"]
            raw_args = call["function"]["arguments"]

            print(f"[调用工具] {name}，参数：{raw_args}")

            try:
                args = json.loads(raw_args or "{}")
                function = AVAILABLE_TOOLS[name]
                result = function(**args)

            except (
                KeyError,
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ) as exc:
                result = {"error": f"工具调用失败：{exc}"}

            result_text = json.dumps(
                result,
                ensure_ascii=False,
            )

            print(f"[工具返回] {result_text}")

            # 11. 将工具执行结果传回模型
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": result_text,
            })

        # 12. 进入下一轮请求，模型将基于工具结果继续回答
        # 下一轮同样开启 stream=True

    print(f"已达到最大轮数 {max_turns}，停止执行。")


if __name__ == "__main__":
    print(f"当前模型：{MODEL}")

    question = input(
        "请输入问题（例如：帮我查询订单 A1001 的状态和物流）："
    ).strip()

    if not question:
        question = "帮我查询订单 A1001 的状态和物流"

    chat_with_agent(question)
