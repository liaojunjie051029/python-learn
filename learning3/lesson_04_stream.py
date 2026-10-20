import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL")

    if not api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY")

    if not model:
        raise RuntimeError("缺少 OPENAI_MODEL")

    client_options = {"api_key": api_key}

    if base_url:
        client_options["base_url"] = base_url

    client = OpenAI(**client_options)

    stream = client.chat.completions.create(
        model = model,
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的 AI 客服助手。",
            },
            {
                "role": "user",
                "content": "请详细解释设备无法启动时的排查步骤。",
            },
        ],
        stream = True,
    )

    full_answer = ""

    for chunk in stream:
        if not chunk.choices:
            continue

        text = chunk.choices[0].delta.content

        if text:
            full_answer += text
            print(text, end="", flush=True)
            # end=""
            # 表示打印后不换行。
            # flush=True
            # 表示立即把 Python 输出缓冲区的内容写到终端。
            #如果没有 flush=True，Python 可能先把内容暂存在缓冲区，过一会儿才显示。这样即使模型已经返回 chunk，你也可能看不到实时效果。

    print("\n\n------模型输出完成------")
    print(f"完整回答长度：{len(full_answer)}")

main()