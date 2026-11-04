import os
import random
import time

import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def is_retryable_status(status_code: object) -> bool:
    """ 判断HTTP状态码是否适合重试 """
    return (
        status_code in {408,409,429}
        # in 用的是 == 比较，任何对象都能做，所以即使 status_code 是 None 也安全，只会返回 False。
        or isinstance(status_code,int) and status_code >= 500
        #先用 isinstance 确认是 int，再做 >= 比较。
        # 这是关键：>= 只有整数才支持，如果 status_code 是 None，None >= 500 会抛 TypeError；但 and 的短路特性保证 isinstance 为 False 时后面根本不执行。
    )

def call_with_retry(
    client: OpenAI,
    model: str,
    messages: list[dict[str,str]],
    max_attempts: int = 3,
):
    
    """
    max_attempts 表示总尝试次数，不是重试次数。

    max_attempts=3：
    第一次请求 + 最多重试两次。

    """
    for attempt in range (1, max_attempts +1):
        #max_attempts=3 时，attempt 依次为 1、2、3，共循环 3 次。
        # 每次循环 = 一次完整的请求尝试。
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
            )

# APITimeoutError	请求超时（服务端没在约定时间内响应）
# APIConnectionError	网络连不上（断网、DNS、连接被拒等）
        except (openai.APITimeoutError,openai.APIConnectionError) as exc:
            retryable_error = exc

# APIStatusError 是服务端返回了非 2xx 状态码时抛的异常（比如 400、429、500、503）。
        except openai.APIStatusError as exc:
            # 安全地取状态码。正常 exc.status_code 有值，万一没有就返回 None，不抛 AttributeError
            # 写法	                    名字来源	  属性缺失时
            # obj.attr	                代码里写死	  抛 AttributeError
            # getattr(obj, "attr")	    字符串/变量	  抛 AttributeError
            # getattr(obj, "attr", d)	字符串/变量	  返回默认值 d
            status_code = getattr(exc,"status_code",None)

            if not is_retryable_status(status_code):#状态码为408 409 429 或者500以上就会重试
                print(
                    f"不可重试的 API 错误："
                    f"{type(exc).__name__},状态码： {status_code}"
                )
                return None

            retryable_error = exc

        if attempt == max_attempts:
            print(
                f"已达到最大尝试次数，最终失败："
                f"{type(retryable_error).__name__}"
            )
            return None

        # 教学实验使用较短等待时间。
        # 生产环境通常会设置更长的退避时间和最大上限。
        delay = min(0.5 * (2**(attempt - 1)),2.0)#这就是指数退避：每失败一次，等待时间翻倍；min(..., 2.0) 是封顶，防止等太久。
        delay += random.uniform(0,0.2)#在基础等待上加 0~0.2 秒的随机抖动。

        print(
            f"第{attempt} 次请求失败，"
            f"{type(retryable_error).__name__}"
            f"{delay:.2f}秒后重试"
        ) 

        time.sleep(delay)


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL")

    missing = [
        name
        for name,value in {
            "OPENAI_API_KEY":api_key,
            "OPENAI_BASE_URL":base_url,
            "OPENAI_MODEL":model,
        }.items()
        if not value
    ]
    # {...}.items()	把三个配置项构成一个字典，.items() 返回 (名字, 值) 对
    # for name, value in ...	逐个取出配置项的名字和对应的变量值
    # if not value	过滤条件：not value 对 None、空字符串 ""、0、False 都为真，即"值为空"时保留
    # name	最终收集的是配置项的名字（字符串），而不是它的值

    if missing:
        raise RuntimeError(
            f"缺少环境变量：{','.join(missing)}"
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
            "content": "你是一个简洁的 AI 客服助手。",
        },
        {
            "role": "user",
            "content": "请用一句话解释什么是 RAG。",
        },
    ]

    response = call_with_retry(
        client=client,
        model=model,
        messages=messages,
        max_attempts=3,
    )

    if response is None:
        print("服务暂时不可用，请稍后重试。")
        return

    answer = response.choices[0].message.content
    print(answer)


if __name__ == "__main__":
    main()