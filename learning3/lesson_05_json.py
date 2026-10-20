import json
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

    response = client.chat.completions.create(
        model = model,
        messages=[
            {
                "role": "system",
                "content": """
你是一个客服信息提取助手。

请根据用户描述提取设备故障信息。
必须只返回合法 JSON，不要返回 Markdown，不要返回解释文字。

JSON 必须包含以下字段：
{
  "device_type": "设备类型，没有则为 null",
  "symptoms": ["故障现象列表"],
  "possible_causes": ["可能原因列表"],
  "needs_more_info": ["还需要用户补充的信息"]
}
""",
            },
            {
                "role": "user",
                "content": "我的手机在充电的时候会掉电，请帮我找出原因",
            },
        ],
        response_format={
            "type": "json_object",
        },#模型返回可解析的 JSON
    )

    raw_content = response.choices[0].message.content or ""

    print("模型原始返回：")
    print(raw_content)

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("模型返回的 JSON 解析失败") from exc

    if not isinstance(data, dict):
        raise RuntimeError("模型返回的 JSON 不是一个字典")

    required_keys = {"device_type", "symptoms", "possible_causes", "needs_more_info"}

    missing_keys = required_keys - data.keys()

    if missing_keys:
        raise RuntimeError(f"模型返回的 JSON 缺少字段：{', '.join(missing_keys)}")

    print("\n模型返回的 JSON：")
    print(json.dumps(data, ensure_ascii=False, indent=2))

    print("\n设备类型：")
    print(data["device_type"])

if __name__ == "__main__":
    main()