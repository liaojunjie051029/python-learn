from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()


@tool
def search_faq(question: str) -> str:
    """查询客服知识库中的常见问题。"""
    return "退款规则：未发货订单可以申请退款。"

model_name=os.getenv("OPENAI_MODEL")
api_key=os.getenv("OPENAI_API_KEY")
base_url=os.getenv("OPENAI_BASE_URL")

if not api_key:
    raise RuntimeError("没有找到 DASHSCOPE_API_KEY")

if not model_name:
    raise RuntimeError("没有找到 DASHSCOPE_MODEL")

if not base_url:
    raise RuntimeError("没有找到 DASHSCOPE_BASE_URL")

model = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
)

agent = create_agent(
    model=model,
    tools=[search_faq],
    system_prompt="你是一个专业的 AI 客服，只能基于客服知识库回答问题。",
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "请查询客服知识库：我的订单还没有发货，可以退款吗？",
            }
        ]
    }
)

print("消息数量:", len(result["messages"]))
#enumerate 是 Python 内置函数，把可迭代对象包装成 (索引, 元素) 的配对，索引默认从 0 开始。
# 也可以转成 list 看结构
# list(enumerate(["a", "b", "c"]))
# [(0, 'a'), (1, 'b'), (2, 'c')]

# list(enumerate(["a", "b"], start=10))
# [(10, 'a'), (11, 'b')]
for index, message in enumerate(result["messages"]):
    print(f"\n[{index}] {type(message).__name__}")
    print("内容:", message.content)

    if getattr(message, "tool_calls", None):
        # getattr(object, name, default)
# 参数	含义
# object	要取属性的对象，这里是 message
# name	属性名（字符串），这里是 "tool_calls"
# default	可选。属性不存在时返回的默认值，这里是 None
# 关键点：只有传了第三个参数 default，getattr 才不会抛异常。

# python
# 不传 default：属性不存在 → 抛 AttributeError
# getattr(msg, "tool_calls")          # ❌ AttributeError: ...

# 传 default：属性不存在 → 返回 None，不报错
# getattr(msg, "tool_calls", None)    # ✅ 返回 None
        print("工具调用:", message.tool_calls)

print("\n最终回答:", result["messages"][-1].content)

print("模型类型:", type(model).__name__)
print("Agent 类型:", type(agent).__name__)