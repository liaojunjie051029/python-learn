import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL")

    if not api_key or not base_url or not model:
        raise RuntimeError("缺少环境变量")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=60.0,
        max_retries=0
        )

    messages = [
         {
    "role": "system",
    "content": """
知识库资料：
挖掘机无法启动时，应优先检查电瓶电压、搭铁线、
启动继电器、安全锁杆和启动保险丝。
如果启动电机有咔哒声但不转，应重点检查启动机和主电瓶线。
""",
},
    {
        "role": "user",
        "content": "挖掘机启动电机没有反应，应该先检查什么？",
    },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    print("模型回答：")
    print(response.choices[0].message.content or "")

    print("\nToken 使用情况：")

    if response.usage is None:
        print("服务商没有返回usage信息")

    print("输入 Token：", response.usage.prompt_tokens)
    print("输出 Token：", response.usage.completion_tokens)
    print("总 Token：", response.usage.total_tokens)

if __name__ == "__main__":
    main()


# 4. 保留关键需求，删除重复内容
# 正确，这是实际 Agent 需要做的事情。
# 适合保留：
# - 用户身份和设备信息；
# - 当前故障现象；
# - 已经确认的排查结果；
# - 用户明确的约束；
# - 尚未解决的问题；
# - 重要的工具执行结果。
# 适合删除或压缩：
# - “你好”“好的”之类的寒暄；
# - 重复的 assistant 解释；
# - 已经解决的中间过程；
# - 与当前问题无关的历史内容；
# - 过期的 RAG 检索内容。
# 特别注意：RAG 结果通常是“当前请求的临时上下文”，不应该直接永久保存到聊天历史中。下一轮应该根据新的问题重新检索。