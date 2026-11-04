import json
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_order_status(order_id: str) -> dict[str, str]:
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
    if order_id == "FAIL":
        raise RuntimeError("模拟订单服务异常")

    return orders.get(
        order_id,
        {
            "order_id": order_id,
            "status": "未找到订单",
            "estimated_delivery": "",
        },
    )

def execute_tool_safely(tool_call) -> dict:
    try:
        result = execute_tool(tool_call)

        return {
            "ok": True,
            "data": result,
        }

    except Exception as exc:
        print(f"内部工具异常：{type(exc).__name__}")

        return {
            "ok": False,
            "error": "订单服务暂时不可用，请稍后重试。",
        }

def execute_tool(tool_call) -> dict[str, str]:
    function_name = tool_call.function.name

    if function_name != "get_order_status":
        return {
            "error": f"未知工具：{function_name}",
        }

    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        return {
            "error": "工具参数不是合法 JSON",
        }

    order_id = arguments.get("order_id")

    if not isinstance(order_id, str) or not order_id:
        return {
            "error": "order_id 必须是非空字符串",
        }

    return get_order_status(order_id)


def assistant_message_to_dict(message) -> dict:
    return {
        "role": "assistant",
        "content": message.content,
        "tool_calls": [
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
            for tool_call in message.tool_calls
        ],
    }


def run_agent(
    client: OpenAI,
    model: str,
    messages: list[dict],
    tools: list[dict],
    max_steps: int = 5,
) -> str:
    for step in range(1, max_steps + 1):
        print(f"\n--- Agent 第 {step} 轮 ---")

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        # 没有工具调用，说明模型已经准备好最终回答
        if not assistant_message.tool_calls:
            return assistant_message.content or ""

        # 保存模型的工具调用请求
        messages.append(
            assistant_message_to_dict(assistant_message)
        )

        # 执行本轮所有工具调用
        for tool_call in assistant_message.tool_calls:
            print(
                "执行工具：",
                tool_call.function.name,
                tool_call.function.arguments,
            )

            # tool_result = execute_tool(tool_call)
            tool_result = execute_tool_safely(tool_call)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False,
                    ),
                }
            )

    return "工具调用超过最大轮次，系统未生成最终回答。"


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL")

    if not api_key or not base_url or not model:
        raise RuntimeError(
            "请先设置 OPENAI_API_KEY、OPENAI_BASE_URL 和 OPENAI_MODEL"
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
                "如果工具返回 ok=False，必须明确告知用户查询失败，不能猜测订单状态。"
                "如果工具返回 ok=True 且订单状态为未找到订单，才说明订单不存在。"
            ),
        },
        {
            "role": "user",
            "content": "请查询订单 FAIL 的状态。",
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

    final_answer = run_agent(
        client=client,
        model=model,
        messages=messages,
        tools=tools,
        max_steps=5,
    )

    print("\n最终回答：")
    print(final_answer)


if __name__ == "__main__":
    main()