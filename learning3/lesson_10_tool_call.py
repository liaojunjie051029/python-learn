import json
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_order_status(order_id: str) -> dict[str, str]:
    """
    模拟查询订单状态。
    这是一个只读工具，没有真实副作用。
    """
    orders = {
        "A1001": {
            "order_id": "A1001",
            "status": "已发货",
            "estimated_delivery": "明天",
        },
        "A1002": {
            "order_id": "A1002",
            "status": "待发货",
            "estimated_delivery": "后天",
        },
    }

    return orders.get(
        order_id,
        {
            "order_id": order_id,
            "status": "未找到订单",
            "estimated_delivery": "",
        },
    )#返回结果如果order_id不存在，则返回一个错误消息{
                # "order_id": order_id,
                # "status": "未找到订单",
                # "estimated_delivery": "",
            # },。


def execute_tool(tool_call) -> dict[str, str]:
    """
    根据模型返回的工具调用，执行对应的 Python 函数。
    """
    function_name = tool_call.function.name

    if function_name != "get_order_status":
        return {
            "error": f"未知工具：{function_name}",
        }

    try:
        arguments = json.loads(tool_call.function.arguments)#把 JSON 字符串解析成 Python 对象
    except json.JSONDecodeError:
        return {
            "error": "模型生成的工具参数不是合法 JSON",
        }

    order_id = arguments.get("order_id")

    if not isinstance(order_id, str) or not order_id:
        return {
            "error": "order_id 必须是非空字符串",
        }

    return get_order_status(order_id)


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL")

    if not api_key or not base_url or not model:
        raise RuntimeError(
            "请先设置 OPENAI_API_KEY、LLM_BASE_URL 和 LLM_MODEL"
        )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=20.0,
        max_retries=0,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "你是订单客服。"
                "当用户询问订单状态时，必须调用订单查询工具，"
                "不能凭空猜测订单状态。"
            ),
        },
        {
            "role": "user",
            "content": "你好，今天有什么可以帮我？",
        },
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_order_status",
                "description": "根据订单号查询订单当前状态。",
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

    # 第一次调用：让模型生成工具调用请求。
    # 为了让本次实验稳定触发工具，这里强制指定工具。
    first_response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto"
        # tool_choice={
        #     "type": "function",
        #     "function": {
        #         "name": "get_order_status",
        #     },
        # },#强制指定工具。还有require
        # tool_choice 值	模型被允许的输出形态
# "auto"	文字 或 任意工具调用
# "none"	只能文字，不准调工具
# "required"	只能工具调用，至少一个，名字不限
# {"type":"function","function":{"name":"X"}}	只能调用名为 X 的工具，且必须调
    )

    assistant_message = first_response.choices[0].message

    if not assistant_message.tool_calls:
        print("模型没有生成工具调用。")
        print("模型回答：", assistant_message.content)
        return

    # 把模型生成的 assistant 工具调用消息加入历史。
    messages.append(
        {
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in assistant_message.tool_calls
            ],
        }
    )

    # Python 执行模型请求的工具。
    for tool_call in assistant_message.tool_calls:
        print(
            "Python 正在执行工具：",
            tool_call.function.name,
            tool_call.function.arguments,
        )

        tool_result = execute_tool(tool_call)

        # 把工具执行结果作为 tool 消息加入历史。
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id, #它不是为了保证“每个方法唯一”，而是为了标识：某一次具体的工具调用。例如同一个工具可以被调用两次：
                "content": json.dumps(
                    tool_result,
                    ensure_ascii=False,
                ),
            }
        )

    # 第二次调用：模型读取 tool 结果，生成给用户的最终回答。
    final_response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
    )

    print("\n最终回答：")
    print(final_response.choices[0].message.content)


if __name__ == "__main__":
    main()