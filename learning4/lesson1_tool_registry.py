import logging
import time
import os
from openai import OpenAI
from pathlib import Path
import asyncio
from dotenv import load_dotenv
from datetime import datetime
import json
from dataclasses import dataclass
from typing import Any


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("agent")

def local_get_current_time():
    now = datetime.now().astimezone()

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
    }

MOCK_PRODUCTS = {
    "P1001": {
        "name": "智能空气净化器 X1",
        "content": {
            "introduction": "智能空气净化器 X1 适合家庭客厅和卧室使用。",
            "tutorial": "长按电源键 3 秒开机，首次使用建议运行自动模式。",
            "notes": "滤芯需要定期更换，不要在潮湿环境中使用。",
            "troubleshooting": "如果设备无法启动，请检查电源连接和滤芯安装状态。",
        },
    }
}

def local_get_product_info(
    product_id: str,
    file_type: str,
    category: str,
):
    product = MOCK_PRODUCTS.get(product_id)

    if product is None:
        return {
            "error": "产品不存在",
            "product_id": product_id,
        }

    content = product["content"].get(category)

    if content is None:
        return {
            "error": "暂不支持该信息类型",
            "category": category,
        }

    return {
        "product_id": product_id,
        "product_name": product["name"],
        "file_type": file_type,
        "category": category,
        "content": content,
    }


# 工具注册表：工具名称 -> Python 函数
TOOL_REGISTRY = {
    "local_get_current_time": local_get_current_time,
    "local_get_product_info": local_get_product_info,
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "local_get_current_time",
            "description": "获取当前时间。用户询问现在几点或当前日期时使用。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
        {
        "type": "function",
        "function": {
            "name": "local_get_product_info",
            "description": "查询模拟产品资料。用户询问产品介绍、使用教程、注意事项或故障排查时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "产品编号，例如 P1001",
                    },
                    "file_type": {
                        "type": "string",
                        "enum": ["image", "video", "document"],
                        "description": "资料类型",
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "introduction",
                            "tutorial",
                            "notes",
                            "troubleshooting",
                        ],
                        "description": "产品资料类别",
                    },
                },
                "required": [
                    "product_id",
                    "file_type",
                    "category",
                ],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
]

MAX_TOOL_ROUNDS = 3


def build_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            f"没有在 {ENV_FILE} 中找到 OPENAI_API_KEY"
        )

    client_options = {
        "api_key": api_key,
    }

    base_url = os.getenv("OPENAI_BASE_URL")

    if base_url:
        client_options["base_url"] = base_url

    return OpenAI(**client_options)

ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(str(ENV_FILE))

def validate_tool_arguments(name: str, arguments: dict):
    tool_definition = next(
        (
            item["function"]
            for item in TOOL_DEFINITIONS
            if item["function"]["name"] == name
        ),
        None,
    )#在 TOOL_DEFINITIONS 列表里，按名字找到对应的工具定义；找到了返回那个函数的定义字典，找不到返回 None。
    # (
    # item["function"]
    # for item in TOOL_DEFINITIONS
    # if item["function"]["name"] == name
    # )
    # 这是一个惰性的生成器：遍历 TOOL_DEFINITIONS，只保留 function.name == name 的那些 item，然后把它们的 item["function"] 吐出来。它不会一次性算出所有结果，而是你取一个它才算一个。
    # next(生成器, None)
    # next() 从迭代器里取第一个元素；如果迭代器空了，就返回第二个参数 None（不传这个默认值的话会抛 StopIteration）。
    # 
    # 两者配合：取第一个匹配项；没有匹配就返回 None。
    if tool_definition is None:
        raise ValueError(f"未知工具定义：{name}")

    if not isinstance(arguments, dict):
        raise TypeError("工具参数必须是 JSON 对象")

    schema = tool_definition["parameters"]
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))#set() 是内置类型/构造函数，接受任何可迭代对象（list、tuple、字符串、生成器等）。并且自动去重

    actual_keys = set(arguments.keys())#arguments.keys() 就是获取字典的所有键
# 但要特别注意：它返回的不是列表，而是一个“视图对象”（view object），类型是 dict_keys。
# arguments.keys()=dict_keys(['product_id', 'file_type', 'category'])
    
    missing_keys = required - actual_keys

    if missing_keys:
        raise ValueError(
            f"缺少必填参数：{sorted(missing_keys)}"
        )

    if schema.get("additionalProperties") is False:
        unknown_keys = actual_keys - set(properties.keys())

        if unknown_keys:
            raise ValueError(
                f"存在未声明参数：{sorted(unknown_keys)}"
            )

    for key, rule in properties.items():
        #properties.items() —— 把字典变成键值对的序列
        # dict_items([
        #   ('product_id', {'type': 'string', 'description': '产品编号'}),
        #   ('file_type',  {'type': 'string', 'enum': [...]}),
        #   ('category',   {'type': 'string', 'enum': [...]}),
        # ])
        # Python 允许你在 for 的循环变量位置直接写多个变量，只要每次迭代出的元素长度匹配，就会自动拆开。

        # python
        # for key, rule in properties.items():
            # print(key, rule)
        # 等价于不写解包的版本：

        # python
        # for item in properties.items():
            # key = item[0]      # 手动取第 0 个
            # rule = item[1]     # 手动取第 1 个
            # print(key, rule)
            # 取出来的值
            # key  = "product_id" / "file_type" / "category"
            # rule = {"type": "string", "description": ..., "enum": [...]}
        if key not in arguments:
            continue

        value = arguments[key]

        if rule.get("type") == "string" and not isinstance(value, str):
            raise TypeError(
                f"参数 {key} 必须是字符串"
            )

        allowed_values = rule.get("enum")

        if allowed_values and value not in allowed_values:
            raise ValueError(
                f"参数 {key} 的值必须是：{allowed_values}"
            )


@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: str | None = None

    def to_message_content(self) -> str:
        if self.ok:
            payload = {
                "ok": True,
                "data": self.data,
            }
        else:
            payload = {
                "ok": False,
                "error": self.error,
            }

        return json.dumps(payload, ensure_ascii=False)

# def execute_tool(name: str, arguments: dict):
#     tool_function = TOOL_REGISTRY.get(name)

#     if tool_function is None:
#         raise ValueError(f"未知工具：{name}")

#     validate_tool_arguments(name, arguments)
#     return tool_function(**arguments)

def execute_tool(name: str, arguments: dict) -> ToolResult:
    tool_function = TOOL_REGISTRY.get(name)

    if tool_function is None:
        return ToolResult(
            ok=False,
            error=f"未知工具：{name}",
        )

    try:
        validate_tool_arguments(name, arguments)

        result = tool_function(**arguments)

        return ToolResult(
            ok=True,
            data=result,
        )

    except Exception as exc:
        return ToolResult(
            ok=False,
            error=f"{type(exc).__name__}: {exc}",
        )

def build_assistant_tool_message(message):
    return {
        "role": "assistant",
        "content": message.content or None,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in message.tool_calls
        ],
    }


# def ask_model(user_message):
#     client = build_client()
#     model=os.getenv("OPENAI_MODEL")

#     if not model:
#         raise RuntimeError(
#             f"没有在 {ENV_FILE} 中找到 OPENAI_MODEL"
#         )

#     messages=[
#                 {
#                     "role": "system",
#                     "content": "你是 AI 客服。涉及当前时间时，必须调用工具，不要自己猜测。",
#                 },
#                 {
#                     "role": "user",
#                     "content": user_message,
#                 },
#             ]


#     response = client.chat.completions.create(
#         model=model,
#         # messages=[
#         #     {
#         #         "role": "system",
#         #         "content": "你是 AI 客服。涉及当前时间时，必须调用工具，不要自己猜测。",
#         #     },
#         #     {
#         #         "role": "user",
#         #         "content": user_message,
#         #     },
#         # ],
#         messages=messages,
#         tools=TOOL_DEFINITIONS,
#         tool_choice="auto",
#         parallel_tool_calls=False,
#     )

#     # message = response.choices[0].message
#     assistant_message = response.choices[0].message

#     print("\n模型返回的原始消息：")
#     # print(message.model_dump_json(indent=2))
#     print(assistant_message.model_dump_json(indent=2))

#     # if not message.tool_calls:
#     if not assistant_message.tool_calls:
#         # print("模型没有调用工具")
#         print("模型回答：", assistant_message.content)
#         return

#     # tool_call = message.tool_calls[0]
#     tool_call = assistant_message.tool_calls[0]

#     tool_name = tool_call.function.name
#     tool_arguments = json.loads(tool_call.function.arguments)

#     print("\n解析后的工具调用：")
#     print("工具名称：", tool_name)
#     print("工具参数：", tool_arguments)

#     tool_result = execute_tool(tool_name, tool_arguments)

#     print("\n模型触发的工具执行结果：")
#     print(tool_result)

#     # 把模型刚才的 tool_call 放回对话历史
#     messages.append(
#         {
#             "role": "assistant",
#             "content": assistant_message.content or None,
#             "tool_calls": [
#                 {
#                     "id": call.id,
#                     "type": "function",
#                     "function": {
#                         "name": call.function.name,
#                         "arguments": call.function.arguments,
#                     },
#                 }
#                 for call in assistant_message.tool_calls
#             ],
#         }
#     )

#      # 把 Python 执行结果作为 tool 消息返回模型
#     messages.append(
#         {
#             "role": "tool",
#             "tool_call_id": tool_call.id,
#             "content": tool_result.to_message_content(),
#             # "content": json.dumps(tool_result, ensure_ascii=False),
#         }
#     )

#     # 第二次请求：让模型根据工具结果生成最终答案
#     final_response = client.chat.completions.create(
#         model=model,
#         messages=messages,
#         tools=TOOL_DEFINITIONS,
#         tool_choice="auto",
#         parallel_tool_calls=False,
#     )

#     final_message = final_response.choices[0].message

#     print("\n最终回答：")
#     print(final_message.content)


async def execute_tool_calls_parallel(tool_calls):
    async def execute_one(tool_call):
        tool_name = tool_call.function.name

        tool_arguments = json.loads(
            tool_call.function.arguments
        )

        # 每个工具调用单独记录开始时间
        start_time = time.perf_counter()

        # 当前工具函数是同步函数，所以放到线程中执行
        tool_result = await asyncio.to_thread(
            execute_tool,
            tool_name,
            tool_arguments,
        )

        duration_ms = (
        time.perf_counter() - start_time
        ) * 1000

        logger.info(
        "tool.done id=%s name=%s ok=%s duration_ms=%.2f",
        tool_call.id,
        tool_name,
        tool_result.ok,
        duration_ms,
    )


        return (
            tool_call,
            tool_name,
            tool_arguments,
            tool_result,
        )

    return await asyncio.gather(
        *(
            execute_one(tool_call)
            for tool_call in tool_calls
    )
    )

def ask_model(user_message):
    logger.info(
    "agent.start question=%s",
    user_message,
    )
    client = build_client()

    model = os.getenv("OPENAI_MODEL", "").strip()

    if not model:
        raise RuntimeError(
            f"没有在 {ENV_FILE} 中找到 OPENAI_MODEL"
        )

    messages = [
        {
            "role": "system",
            "content": "你是 AI 客服。需要实时信息或产品资料时，必须调用工具。",
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    for round_number in range(1, MAX_TOOL_ROUNDS + 1):
        print(f"\n--- 模型轮次 {round_number} ---")

        logger.info(
        "model.request round=%d",
        round_number,
        )

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            parallel_tool_calls=True
            # parallel_tool_calls=False,#控制模型能否在一次响应中同时发起多个工具调用的布尔值参数。这里是让每次回复最多只能调用一个工具
        )

        assistant_message = response.choices[0].message

        logger.info(
        "model.response round=%d tool_calls=%d",
        round_number,
        len(assistant_message.tool_calls or []),
        )

        # 没有工具调用，说明模型已经生成最终答案
        if not assistant_message.tool_calls:
            logger.info("agent.finish")
            print("\n最终回答：")
            print(assistant_message.content)
            return

        print("\n模型返回工具调用：")
        print(assistant_message.tool_calls)

        # 先保存 assistant 的 tool_call
        messages.append(
            build_assistant_tool_message(assistant_message)
        )

        # 当前关闭了 parallel_tool_calls，但代码仍按列表处理
        # for tool_call in assistant_message.tool_calls:
            # tool_name = tool_call.function.name
            # tool_arguments = json.loads(
            #     tool_call.function.arguments
            # )

            # print("工具名称：", tool_name)
            # print("工具参数：", tool_arguments)

            # tool_result = execute_tool(
            #     tool_name,
            #     tool_arguments,
            # )

            # print("工具结果：", tool_result)

            # messages.append(
            #     {
            #         "role": "tool",
            #         "tool_call_id": tool_call.id,
            #         "content": tool_result.to_message_content(),
            #     }
            # )
        tool_results = asyncio.run(
            execute_tool_calls_parallel(
                assistant_message.tool_calls
            )
        )

        for (
            tool_call,
            tool_name,
            tool_arguments,
            tool_result,
        ) in tool_results:
            print("工具名称：", tool_name)
            print("工具参数：", tool_arguments)
            print("工具结果：", tool_result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result.to_message_content(),
                }
            )

    raise RuntimeError(
        f"达到最大工具轮数：{MAX_TOOL_ROUNDS}"
    )

def main():
    # 假设这个名字来自模型的 tool_call
    # tool_name = "local_get_current_time"
    # tool_name = "local_get_product_info"

    # tool_function = TOOL_REGISTRY.get(tool_name)

    # if tool_function is None:
    #     print(f"未知工具：{tool_name}")
    #     return

    # result = tool_function()

    # print("工具执行结果：")
    # print(result)
    print("\n给模型看的工具定义：")
    print(json.dumps(TOOL_DEFINITIONS, ensure_ascii=False, indent=2))
    # ask_model("现在几点？")
    # ask_model("你好，请介绍一下你自己")
    # ask_model("请查询产品 P1001 的故障排查文档")
    ask_model(
    "请同时告诉我当前时间，并查询产品 P1001 的故障排查文档"
)


if __name__ == "__main__":
    main()
    
