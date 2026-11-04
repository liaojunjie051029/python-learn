# 第三阶段：Python 大模型 API 与 Agent 开发

> 学习目标：使用 Python 直接调用 OpenAI-compatible 大模型 API，理解消息、异步、流式输出、结构化输出、超时、重试、Token、上下文、Function Calling、Agent Loop、FastAPI 和 SSE。
>
> 本阶段坚持不先使用 LangChain，优先理解底层请求、消息协议和 Agent 循环。

## 0. 本阶段的技术范围

本阶段使用了：

- Python 3.15
- Python 虚拟环境 .venv
- openai==2.54.0
- OpenAI-compatible API
- FastAPI、Uvicorn、Pydantic
- PowerShell
- Chat Completions API
- Function Calling / Tool Calling
- SSE（Server-Sent Events）

主要学习目录：

~~~text
C:\text\python\learning3
~~~

已经实际运行过的练习：

~~~text
lesson_01_chat.py
lesson_02_multi_turn.py
lesson_03_async.py
lesson_04_stream.py
lesson_05_json.py
lesson_06_timeout.py
lesson_07_retry.py
lesson_08_usage.py
lesson_09_context_window.py
lesson_10_tool_call.py
lesson_11_agent_loop.py
lesson_12_api_error.py
~~~

---

## 1. Python 虚拟环境与 OpenAI SDK

### 1.1 为什么需要虚拟环境

虚拟环境用于隔离不同项目的 Python 依赖。

如果所有项目都把依赖安装到全局 Python 中，可能出现：

~~~text
项目 A 需要 openai==1.x
项目 B 需要 openai==2.x
项目 C 需要另一版本的 pydantic
~~~

不同项目之间会互相影响。

推荐：

~~~powershell
cd C:\text\python\learning3
python -m venv .venv
.\.venv\Scripts\Activate.ps1
~~~

激活成功后，PowerShell 提示符会出现：

~~~text
(.venv) PS C:\text\python\learning3>
~~~

安装 SDK：

~~~powershell
python -m pip install "openai==2.54.0"
~~~

验证当前 Python：

~~~powershell
python -c "import sys; print(sys.executable); print('prefix =', sys.prefix); print('base =', sys.base_prefix)"
~~~

虚拟环境中应该看到：

~~~text
C:\text\python\learning3\.venv\Scripts\python.exe
~~~

并且：

~~~text
sys.prefix != sys.base_prefix
~~~

验证 SDK：

~~~powershell
python -m pip show openai
python -c "from openai import OpenAI; print('openai SDK import ok')"
~~~

### 1.2 踩过的坑：第一次安装到了全局环境

第一次安装 openai 时还没有激活 .venv，所以安装位置是：

~~~text
C:\Users\liaoj\AppData\Local\Programs\Python\Python315\Lib\site-packages
~~~

这说明当时安装到了全局 Python。

后来激活虚拟环境后，最终确认 SDK 位于：

~~~text
C:\text\python\learning3\.venv\Lib\site-packages
~~~

以后优先使用：

~~~powershell
python -m pip install ...
~~~

不要依赖来源不确定的 pip install。

### 1.3 环境变量

本阶段使用的变量：

~~~powershell
$env:OPENAI_API_KEY = "你的密钥"
$env:LLM_BASE_URL = "你的兼容接口地址"
$env:LLM_MODEL = "你的模型名称"
~~~

| 环境变量 | 作用 |
|---|---|
| OPENAI_API_KEY | 身份认证和访问权限 |
| LLM_BASE_URL | API 请求发送到哪个兼容服务地址 |
| LLM_MODEL | 请求使用哪个模型 |

Base URL 不一定是“运行模型的服务器地址”，也可能是云厂商网关、代理或 OpenAI-compatible 服务入口。

API Key 解决“我有没有权限访问”，Base URL 解决“请求发到哪里”，Model 解决“请求哪个模型”。三者不能混为一谈。

### 1.4 踩过的坑：环境变量名称不一致

PowerShell 设置的是：

~~~powershell
$env:LLM_MODEL = "..."
~~~

但脚本读取的是：

~~~python
os.getenv("OPENAI_MODEL")
~~~

于是出现：

~~~text
Error: OPENAI_MODEL environment variable is not set
~~~

解决方式是统一命名：

~~~python
base_url = os.getenv("LLM_BASE_URL")
model = os.getenv("LLM_MODEL")
~~~

或者统一改成 OPENAI_BASE_URL 和 OPENAI_MODEL。两种都可以，但代码和环境变量必须一致。

### 1.5 密钥安全

真实 API Key 不能：

- 写入 Python 源码；
- 提交到 Git；
- 放进截图；
- 发到聊天、工单或公开仓库；
- 出现在日志中。

如果真实 Key 已经泄露，应当立即撤销、重新生成，并检查调用记录和费用。

推荐：

~~~python
import os

api_key = os.getenv("OPENAI_API_KEY")
~~~

不推荐：

~~~python
api_key = "不要把密钥写在这里"
~~~

---

## 2. Python 程序入口与 __name__

### 2.1 __name__ 是什么

当文件被直接运行：

~~~powershell
python lesson_01_chat.py
~~~

该文件中的 __name__ 等于：

~~~text
"__main__"
~~~

当文件被其他文件导入：

~~~python
import lesson_01_chat
~~~

此时 __name__ 通常是：

~~~text
"lesson_01_chat"
~~~

### 2.2 为什么写入口保护

~~~python
def main():
    print("执行主程序")


if __name__ == "__main__":
    main()
~~~

直接运行文件时会执行 main()；被其他模块导入时不会自动执行。

如果直接写 main()，那么其他文件导入该模块时也会自动执行 main()。

---

## 3. 第一次调用大模型 API

### 3.1 最小同步调用

~~~python
import os

from openai import OpenAI


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

response = client.chat.completions.create(
    model=os.getenv("LLM_MODEL"),
    messages=[
        {
            "role": "user",
            "content": "请用一句话解释什么是 RAG",
        }
    ],
)

answer = response.choices[0].message.content
print(answer)
~~~

调用链路：

~~~text
Python 程序
    ↓
OpenAI Python SDK
    ↓
HTTP 请求
    ↓
OpenAI-compatible 服务
    ↓
大模型
    ↓
ChatCompletion 响应
~~~

本阶段使用 chat.completions.create，因为它和已有 NestJS 项目以及当前兼容服务的调用方式一致。OpenAI 当前文档也提供 Responses API，但学习过程中不应该随意混用两套消息和响应模型。

### 3.2 踩过的坑：错误的方法名

错误：

~~~python
client.chat.create(...)
~~~

错误：

~~~text
'Chat' object has no attribute 'create'
~~~

正确：

~~~python
client.chat.completions.create(...)
~~~

调用层级是：

~~~text
client
└── chat
    └── completions
        └── create
~~~

### 3.3 和 NestJS AiService 的对应关系

| NestJS | Python |
|---|---|
| OpenAI provider | OpenAI / AsyncOpenAI |
| AiService 封装 | Python 函数、类或 service 模块 |
| chat.completions.create() | client.chat.completions.create() |
| JSON.parse() | json.loads() |
| JSON.stringify() | json.dumps() |
| DTO / class-validator | Pydantic BaseModel |
| Observable / SSE | async generator / StreamingResponse |

Python SDK 负责网络调用，但 Agent 逻辑、工具执行、异常处理和上下文管理仍然需要自己编写。

---

## 4. 消息角色：system、user、assistant、tool

### 4.1 system

system 用来定义：

- Agent 的角色；
- 业务背景；
- 行为规则；
- 输出格式；
- 安全边界；
- 工具使用约束。

示例：

~~~python
{
    "role": "system",
    "content": "你是一个专业的 AI 客服，只能基于可靠信息回答问题。",
}
~~~

准确说法：

> system 不是普通聊天内容，而是应用开发者提供给模型的行为约束和业务背景。

### 4.2 user

用户实际输入：

~~~python
{
    "role": "user",
    "content": "我的挖掘机无法启动",
}
~~~

### 4.3 assistant

模型过去已经输出给用户的回答：

~~~python
{
    "role": "assistant",
    "content": "请先检查电瓶和安全锁杆",
}
~~~

assistant 不是模型内部思考过程，而是历史中的可见助手回答。

### 4.4 tool

工具执行结果：

~~~python
{
    "role": "tool",
    "tool_call_id": "call_123",
    "content": "{\"status\":\"已发货\"}",
}
~~~

tool 消息必须和模型生成的 tool_call_id 匹配。

---

## 5. 多轮对话与短期记忆

### 5.1 单轮调用

~~~python
messages = [
    {
        "role": "user",
        "content": "我叫小王",
    }
]
~~~

下一次如果只发送“我叫什么”，模型不一定知道“小王”。

### 5.2 多轮消息

~~~python
messages = [
    {
        "role": "system",
        "content": "你是客服",
    },
    {
        "role": "user",
        "content": "我叫小王",
    },
    {
        "role": "assistant",
        "content": "好的，小王",
    },
    {
        "role": "user",
        "content": "我叫什么？",
    },
]
~~~

模型不会自动访问 Python 进程中的历史变量。应用程序必须把历史重新组装到 messages 中。

### 5.3 内存中的历史

~~~python
conversation_history = []
~~~

成功后追加：

~~~python
conversation_history.append({
    "role": "user",
    "content": user_message,
})

conversation_history.append({
    "role": "assistant",
    "content": assistant_answer,
})
~~~

这种历史属于当前 Python 进程。

服务重启、进程崩溃或切换到其他 Worker 后，数据可能消失或不可见。

### 5.4 你回答正确和不完整的地方

你回答“当前代码只有一轮对话”，正确。

你回答“不加 assistant 消息会造成上下文缺失”，也正确。模型需要看到过去的 user 和 assistant 消息，才能理解对话已经进行到哪里。

你回答“程序关闭后要保留就存数据库”，基本正确，但还可以补充：

- Redis 适合短期会话和 TTL；
- PostgreSQL 适合持久化聊天记录和审计；
- Qdrant 主要用于向量检索，不是普通聊天历史数据库。

---

## 6. 异步调用

### 6.1 AsyncOpenAI

~~~python
import asyncio
import os

from openai import AsyncOpenAI


client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)


async def main():
    response = await client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {
                "role": "user",
                "content": "请解释什么是 RAG",
            }
        ],
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    asyncio.run(main())
~~~

### 6.2 async def 和 await

async def 表示协程函数。

~~~python
response = await client.chat.completions.create(...)
~~~

含义是：

> 当前协程在等待网络结果时暂停，把执行机会交还给事件循环；网络请求完成后再恢复当前协程。

并不是整个 Python 进程都被暂停。

### 6.3 你当时回答不够准确的地方

你说“异步不会阻塞总进程，效率更高”。

更准确的说法：

> 异步 I/O 可以避免当前线程在等待网络时被阻塞，使其他任务有机会继续运行，但不会让 CPU 密集型任务自动变快，也不保证每个请求的单次耗时一定更短。

你说“await 后面的操作会等待异步操作完成”。

当前协程中的后续代码确实要等待，但事件循环不一定停止，事件循环可以执行其他协程。

你说“FastAPI 是单线程事件循环加线程池”。

更准确的说法：

- async def 路由主要运行在事件循环；
- 普通 def 路由可能交给线程池；
- 多进程部署时会有多个独立进程；
- 最终并发模型取决于 Uvicorn、Gunicorn、Worker 配置。


## 7. 流式输出

### 7.1 同步流式调用

~~~python
stream = client.chat.completions.create(
    model=model,
    messages=messages,
    stream=True,
)

for chunk in stream:
    content = chunk.choices[0].delta.content

    if content:
        print(content, end="", flush=True)
~~~

### 7.2 异步流式调用

~~~python
stream = await client.chat.completions.create(
    model=model,
    messages=messages,
    stream=True,
)

async for chunk in stream:
    content = chunk.choices[0].delta.content

    if content:
        print(content, end="", flush=True)
~~~

### 7.3 stream=True

stream=True 让模型 API 不等完整答案生成完，而是逐步返回增量 chunk。

### 7.4 delta.content

流式响应中通常读取：

~~~python
chunk.choices[0].delta.content
~~~

它是当前 chunk 的增量内容，不一定是完整句子，也不一定是一个 Token。

可能看到：

~~~text
R
AG
是一种
检索增强生成技术
~~~

content 也可能为 None，所以必须判断。

### 7.5 chunk 不等于 Token

一次 chunk 可能包含：

- 一个字符；
- 多个 Token；
- 一个词的一部分；
- 换行；
- 空内容。

因此不应该把每个 chunk 直接保存成一条聊天记录。

正确做法通常是：

~~~text
流式 chunk → 拼接到内存 → 完整回答结束后保存一条 assistant 消息
~~~

如果确实需要审计流式过程，可以另外保存事件日志，但不要把事件日志当作普通聊天消息表。

### 7.6 flush=True

~~~python
print(content, end="", flush=True)
~~~

flush=True 会立即刷新 Python 标准输出缓冲区，让控制台尽快显示内容。

它主要影响：

~~~text
Python → 控制台
~~~

它不等于：

~~~text
Python → 浏览器 SSE
~~~

### 7.7 和 NestJS 的对应关系

NestJS：

~~~typescript
for await (const chunk of finalStream) {
  const content = chunk.choices[0]?.delta?.content;
}
~~~

Python：

~~~python
async for chunk in stream:
    content = chunk.choices[0].delta.content
~~~

两者本质都是消费异步流。

需要区分两个方向：

~~~text
大模型 → 后端
~~~

由 stream=True 控制。

~~~text
后端 → 前端
~~~

由 SSE、HTTP chunked response、WebSocket 或其他传输方式控制。

所以 NestJS 当然可以把流输出到控制台，也可以推送给前端。FastAPI 也不只能使用 SSE。



## 8. JSON Mode 与结构化输出

### 8.1 JSON Mode 解决什么问题

普通文本回答适合直接展示给用户，但 Agent 还需要把模型输出交给程序继续处理。例如，客服系统可能需要让模型返回：

- 设备类型；
- 症状；
- 可能原因；
- 还需要向用户追问的信息。

这时目标不是“看起来像 JSON”，而是让程序拿到可以被 json.loads() 解析的 JSON。

~~~python
import json

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": (
                "你是设备故障分析器。"
                "请只返回 JSON，不要添加 Markdown 代码块。"
            ),
        },
        {
            "role": "user",
            "content": "手机充电时电量不升反降，请分析。",
        },
    ],
    response_format={"type": "json_object"},
)

raw_content = response.choices[0].message.content
data = json.loads(raw_content)

print(data["device_type"])
print(data["possible_causes"])
~~~

你实际运行的 lesson_05_json.py 输出了：

~~~json
{
  "device_type": "手机",
  "symptoms": [
    "充电时电量不升反降（掉电）"
  ],
  "possible_causes": [
    "充电器或充电线故障，实际输出功率不足",
    "使用非原装或不匹配的充电设备，充电功率过低"
  ],
  "needs_more_info": [
    "手机型号和使用年限",
    "是否使用原装充电器和充电线"
  ]
}
~~~

### 8.2 JSON Mode 不是业务校验

response_format={"type": "json_object"} 主要保证模型输出是 JSON 对象，但它不自动保证：

- 一定存在 device_type；
- possible_causes 一定是列表；
- 列表中的每一项一定是字符串；
- 业务字段一定满足你的长度或枚举要求。

因此生产代码通常还需要第二层校验，例如用 Pydantic 定义业务结构：

~~~python
from pydantic import BaseModel

class FaultAnalysis(BaseModel):
    device_type: str
    symptoms: list[str]
    possible_causes: list[str]
    needs_more_info: list[str]

analysis = FaultAnalysis.model_validate(data)
~~~

这里有两层边界：

1. JSON 语法层：能不能被 json.loads() 解析；
2. 业务结构层：字段、类型和业务规则是否符合预期。

### 8.3 这个知识点在 Agent 系统中负责什么

结构化输出负责把模型的自然语言能力转换成程序可以消费的数据。它可以用于：

- 意图识别；
- 工具参数预提取；
- 工单分类；
- 客服问题路由；
- RAG 检索条件生成；
- 将用户问题转成数据库查询条件。

### 8.4 面试官可能怎么问

**问：JSON Mode 能不能保证字段一定存在？**

答：不能。它主要解决 JSON 语法问题，字段和类型仍然需要 schema 或 Pydantic 做业务校验。工具调用参数也不能只信模型返回，执行工具前必须校验。

**问：为什么不能直接把模型文本当 Python 对象？**

答：模型返回的是字符串。必须先用 json.loads() 解析；解析成功后才是 Python 的 dict 或 list。解析成功也不代表业务结构正确。

### 8.5 什么时候可以写进简历

如果你能复现 lesson_05_json.py，并能解释 JSON 解析与业务 schema 校验的区别，可以写：

> 使用 OpenAI 兼容 Python SDK 实现 JSON 结构化输出，并通过 Pydantic 校验模型返回的业务字段。

暂时不要写“保证模型 100% 输出正确业务数据”，因为结构化输出仍需要应用层校验和异常处理。

## 9. 超时：请求没有在规定时间内完成

### 9.1 SDK 超时参数

你使用过：

~~~python
from openai import OpenAI

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=20.0,
)
~~~

这里的 20.0 表示客户端等待网络请求完成的超时时间，单位是秒。你实际运行时：

- timeout=20.0 可以正常得到回答；
- timeout=0.00001 很快触发了超时。

捕获异常：

~~~python
import openai

try:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
except openai.APITimeoutError:
    print("请求超时：模型在规定时间内没有完成响应。")
~~~

### 9.2 对你原来回答的修正

你说“Python 的时间单位是秒，Node 的时间单位是毫秒”。这句话不准确。

更准确的说法是：

- 时间单位由具体 SDK 的参数约定决定；
- 当前 OpenAI Python SDK 的 timeout 使用秒；
- 你的 Node/NestJS HTTP 客户端可能使用毫秒；
- Python 语言本身并没有规定所有库都必须使用秒，Node.js 也不是所有库都必须使用毫秒。

面试时不要把 SDK 参数约定说成语言规则。

### 9.3 超时是否一定代表模型没有工作

不一定。可能发生在：

- 请求还没到模型服务；
- 网络连接阶段；
- 模型排队或生成阶段；
- 代理、网关或负载均衡等待阶段；
- 客户端等待时间太短。

因此日志中最好记录请求 ID、模型、耗时和异常类型，但不要记录 API Key。

### 9.4 FastAPI 中如何映射

如果模型请求超时，后端可以向前端返回 HTTP 504：

~~~python
from fastapi import HTTPException

try:
    answer = await call_model()
except openai.APITimeoutError:
    raise HTTPException(
        status_code=504,
        detail="模型服务响应超时，请稍后重试。",
    )
~~~

超时是后端服务依赖上游模型服务没有及时完成，不等同于 FastAPI 进程崩溃。

### 9.5 这个知识点在 Agent 系统中负责什么

超时是 Agent 的时间边界。Agent 可能依次调用：

1. 大模型；
2. Redis；
3. Qdrant；
4. MCP 工具；
5. 第三方订单系统。

任何一个环节都可能拖慢整条链路。没有超时，用户请求可能长期占用连接和协程。

### 9.6 面试官可能怎么问

**问：超时后能不能直接重试？**

答：要结合错误类型和操作是否有副作用。模型生成通常可以有限重试，但创建订单、退款、发短信等副作用操作不能无脑重试，必须结合幂等键或查询执行状态。

## 10. 有限重试与指数退避

### 10.1 max_attempts=3 到底请求几次

你实际运行了：

~~~text
第1次请求失败，APITimeoutError，0.62秒后重试
第2次请求失败，APITimeoutError，1.18秒后重试
已达到最大尝试次数，最终失败
~~~

总请求次数是 3 次：

- 第 1 次：初始请求；
- 第 2 次：第 1 次重试；
- 第 3 次：第 2 次重试。

所以 max_attempts=3 不是“重试 3 次”，而是“最多尝试 3 次”，最多重试 2 次。

### 10.2 一个可理解的重试骨架

~~~python
import random
import time
import openai

RETRYABLE_ERRORS = (
    openai.APITimeoutError,
    openai.APIConnectionError,
    openai.RateLimitError,
    openai.InternalServerError,
)

def call_with_retry(client, *, model, messages, max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
            )
        except RETRYABLE_ERRORS as exc:
            if attempt == max_attempts:
                raise

            base_delay = 0.5 * (2 ** (attempt - 1))
            jitter = random.uniform(0, 0.3)
            time.sleep(base_delay + jitter)
            print(f"第 {attempt} 次失败，准备重试：{type(exc).__name__}")
~~~

指数退避的核心是：失败次数越多，等待时间越长。随机抖动 jitter 可以减少大量请求同时重试造成的“惊群”。

### 10.3 哪些错误通常不应该重试

AuthenticationError 通常表示 Key 无效、过期、被撤销或没有权限。它不是等几秒就会自然恢复的临时错误，因此无脑重试只会浪费时间和资源。

BadRequestError 通常表示请求参数错误，例如：

- model 名称不正确；
- messages 格式不合法；
- 参数类型不正确；
- JSON schema 不符合要求。

必须修正请求，而不是重复发送相同请求。

### 10.4 SDK 自动重试与自己的重试

SDK 可能已经有默认重试行为。如果你在外层又写了一层重试，就可能出现：

~~~text
外层第 1 次
  SDK 内部重试若干次
外层第 2 次
  SDK 内部重试若干次
~~~

这会让真实请求次数和预期不一致。

你在学习代码中使用过：

~~~python
client = AsyncOpenAI(
    ...,
    max_retries=0,
)
~~~

这表示关闭 SDK 内部自动重试，把重试策略交给你自己的代码，便于观察和学习。生产环境需要明确谁负责重试，避免重复实现。

### 10.5 副作用工具为什么不能无脑重试

假设 Agent 调用：

- create_order；
- refund_payment；
- send_sms；
- send_email。

如果请求发给第三方后已经成功，但响应在网络中丢失，客户端看到的是超时。此时再次重试可能造成：

- 重复创建订单；
- 重复退款；
- 重复发送短信；
- 重复扣费。

正确思路是：

1. 使用业务幂等键，例如 request_id；
2. 重试前先查询原操作状态；
3. 第三方 API 支持时传递 Idempotency-Key；
4. 只有确认上一次没有执行时才重试；
5. 把“已提交但结果未知”与“明确失败”区分开。

### 10.6 这个知识点在 Agent 系统中负责什么

重试负责提高临时故障下的成功率，但它不是“所有错误都再调用一次”。Agent 中必须区分：

- 可安全重复的只读查询；
- 有幂等保护的写操作；
- 没有幂等保护的危险副作用操作。

### 10.7 面试官可能怎么问

**问：你如何设计大模型调用的重试？**

答：按错误类型白名单重试，例如超时、连接失败、限流和临时 5xx；指数退避加抖动；限制总尝试次数；认证和参数错误不重试；副作用工具要使用幂等键或先查询状态。

### 10.8 什么时候可以写进简历

如果你能运行 lesson_07_retry.py，并解释“总尝试次数”和“重试次数”的区别，可以写：

> 为 OpenAI 兼容模型调用实现超时、连接、限流等临时错误的有限重试与指数退避。

不要写“实现了分布式可靠消息和支付级幂等”，因为目前你还没有在 Python 项目中实现这些机制。


## 11. Token、上下文与成本

### 11.1 usage 字段怎么看

你运行 lesson_08_usage.py 时得到过：

~~~text
输入 Token：63
输出 Token：961
总 Token：1024
~~~

API 通常会返回：

~~~json
{
  "prompt_tokens": 63,
  "completion_tokens": 961,
  "total_tokens": 1024
}
~~~

它们的含义是：

- prompt_tokens：这次请求送给模型的输入 token；
- completion_tokens：模型生成的输出 token；
- total_tokens：输入和输出的总和。

在部分模型或供应商返回中，还可能看到：

- reasoning_tokens：推理过程相关 token；
- cached_tokens：命中缓存的输入 token；
- audio_tokens：音频相关 token。

这些可选字段可能是 null，或者不同兼容服务的命名和统计方式不同。不要把某个供应商的扩展字段当成所有模型都固定提供的字段。

### 11.2 prompt_tokens 包含什么

prompt_tokens 不只是当前用户的一句话，还可能包括：

1. system 或 developer 指令；
2. 历史 user 消息；
3. 历史 assistant 消息；
4. 当前 user 消息；
5. 工具 schema；
6. 以前的 assistant tool_calls；
7. 工具执行结果；
8. RAG 检索出来并拼入 prompt 的上下文；
9. 多模态内容的文本描述或图片相关输入。

因此 Agent 越运行越久，输入 token 可能越来越大，即使用户当前只问了一句话。

### 11.3 RAG 对输入和输出的影响

你回答“带 RAG 的最大”是有道理的，但需要说得更精确：

- RAG 通常会直接增加输入 token，因为检索片段被放进上下文；
- 输出 token 不一定增加，取决于模型最终生成多少内容；
- 更长的上下文可能间接影响模型输出长度、推理复杂度和成本；
- 如果检索内容重复、无关或过长，反而会降低回答质量。

一个粗略的成本模型是：

~~~text
一次调用成本 ≈ 输入 token 成本 + 输出 token 成本
输入 token = 系统指令 + 历史 + 当前问题 + 工具 schema + RAG 上下文
~~~

### 11.4 不裁剪会发生什么

如果每轮都把完整历史、完整工具记录和完整 RAG 文档继续传入：

- prompt_tokens 会持续增大；
- 请求延迟变长；
- 成本升高；
- 可能超过模型上下文窗口；
- 模型可能更难关注当前问题；
- 长历史中错误信息可能继续影响后续回答。

所以上下文管理不是简单地“把所有聊天记录永久发给模型”。

### 11.5 这个知识点在 Agent 系统中负责什么

Token 管理是 Agent 的资源管理。它直接影响：

- 单次请求成本；
- 端到端延迟；
- 并发吞吐；
- 上下文窗口是否溢出；
- RAG 召回内容应该放多少；
- 何时应该摘要或裁剪历史。

### 11.6 面试官可能怎么问

**问：RAG 会不会一定增加输出 token？**

答：不会。RAG 主要把检索内容作为输入上下文，因此通常增加 prompt_tokens。输出 token 由模型回答长度决定，可能增加，也可能不变甚至变少。

**问：如何定位一次请求为什么 token 很高？**

答：拆分统计系统指令、历史消息、工具 schema、工具结果和 RAG 文档，分别计算或记录长度，再决定裁剪、摘要、减少检索片段或缩短工具描述。

## 12. 上下文裁剪

### 12.1 最简单的按消息数量裁剪

学习阶段可以使用一个窗口：

~~~python
def build_messages(
    system_prompt: str,
    history: list[dict[str, str]],
    current_user_message: str,
    max_history_messages: int = 6,
) -> list[dict[str, str]]:
    recent_history = history[-max_history_messages:]

    return [
        {"role": "system", "content": system_prompt},
        *recent_history,
        {"role": "user", "content": current_user_message},
    ]
~~~

这表示只保留最近的若干条历史消息，同时始终保留系统提示词。

### 12.2 你回答“哪些历史消息被裁剪了”

你当时答：

> user：我正在排查一台挖掘机。  
> assistant：明白，目前设备是挖掘机。

这部分被裁剪了。

核心判断是对的：它们位于保留窗口之前，所以不再发送给模型。更严谨地说，不是数据库里的记录被删除，而是本次请求构造 prompt 时没有把它们放进去。

### 12.3 max_turns=1 时模型还知道名字吗

如果“小王”只出现在旧历史中，而当前请求没有名字、系统提示词也没有名字，那么裁剪后模型不知道。

但可以通过以下方式保留关键事实：

1. 把用户画像放在独立 profile 中；
2. 在每次请求前拼入摘要；
3. 使用 Redis 或数据库保存结构化状态；
4. 让模型先提取长期事实，再单独存储；
5. 不把所有历史都当作长期记忆。

例如：

~~~python
profile = {
    "name": "小王",
    "current_device": "挖掘机",
    "current_problem": "无法启动",
}

system_context = (
    f"用户姓名：{profile['name']}；"
    f"当前设备：{profile['current_device']}；"
    f"当前问题：{profile['current_problem']}。"
)
~~~

### 12.4 为什么不能删除系统提示词

系统提示词承担的是全局行为边界，例如：

- 角色；
- 语气；
- 输出格式；
- 安全边界；
- 不确定时如何回答；
- 是否允许调用某类工具；
- 不应编造设备诊断结论。

历史消息是短期上下文，系统提示词是规则和边界。两者职责不同，不能因为裁剪历史而随便删除系统提示词。

### 12.5 为什么 tool 消息不能从中间随便截断

一个完整的工具调用链可能是：

~~~text
assistant：我要调用 get_order_status
tool：订单 A1001 已发货
assistant：您的订单已发货
~~~

其中：

- assistant tool_calls 说明模型请求调用了什么；
- tool 消息提供执行结果；
- 后续 assistant 消息基于工具结果组织最终回答。

如果只留下 tool 结果却删掉前面的 tool_calls，模型可能不知道这条结果属于哪个工具调用。如果保留 tool_calls 却删掉对应 tool 结果，模型可能看到一个未完成的工具调用。

因此应该按完整消息组裁剪：

- 普通 user/assistant 对可以作为一个组；
- assistant tool_calls 与对应的一个或多个 tool 结果必须一起保留；
- 如果整个工具组放不下，应该在工具组之前截断，或者把工具组压缩成摘要；
- 不要把一条工具链从中间切开。

### 12.6 从“按条数”升级到“按 token 预算”

按条数简单，但不精确。一条历史可能只有几十 token，也可能包含一整篇 RAG 文档。

更合理的生产思路是：

~~~text
总预算
- system 预算
- 当前问题预算
- 工具 schema 预算
- 预留输出预算
= 历史和 RAG 可使用的输入预算
~~~

在预算不足时，可以依次：

1. 丢弃最旧的普通对话；
2. 把旧对话摘要；
3. 缩短工具描述；
4. 减少 RAG top_k；
5. 截断单个文档片段；
6. 保留关键 profile 和安全规则。

### 12.7 这个知识点在 Agent 系统中负责什么

上下文裁剪决定 Agent 的“短期记忆”边界；摘要和 profile 决定“长期记忆”边界；Redis/PostgreSQL 决定应用重启后能否恢复这些状态。

### 12.8 面试官可能怎么问

**问：工具调用历史怎么裁剪？**

答：不能简单按消息下标截断，要把 assistant 的 tool_calls、对应的 tool 结果以及必要的后续 assistant 消息看成一个原子组。要么完整保留，要么在组之前裁剪或把整组摘要。

**问：为什么不把所有历史都保留？**

答：成本、延迟和上下文窗口都会增长，而且无关历史会干扰模型。生产系统通常结合最近窗口、摘要、用户画像和结构化业务状态。

## 13. session_id、短期记忆与持久化

### 13.1 session_id 只是索引，不是记忆本身

一个最小内存实现可能是：

~~~python
conversation_store: dict[str, list[dict[str, str]]] = {}

def get_history(session_id: str) -> list[dict[str, str]]:
    return conversation_store.setdefault(session_id, [])
~~~

当客户端传入相同的 session_id 时，后端拿到同一份历史列表，所以模型可以继续看到前面的消息。

不同 session_id 对应不同列表，通常代表不同会话。

但 session_id 自己没有保存任何消息。真正的记忆在 conversation_store 里。

### 13.2 为什么服务重启后会丢失

如果 conversation_store 是普通 Python 字典，它只存在当前进程内：

- 进程退出，数据释放；
- 服务重启，数据消失；
- 多 worker 时，每个 worker 可能有自己的字典；
- 负载均衡把请求转到不同进程时，可能看不到同一份历史；
- 多实例部署时，实例之间也不共享。

你回答“要持久化需要数据库”是正确方向，但可以进一步区分：

- Redis：适合短期会话、TTL、快速读取；
- PostgreSQL：适合需要持久化、审计和关联用户的消息记录；
- 对象存储：适合大型文档和附件；
- 向量数据库：保存向量检索数据，不等于保存完整聊天历史。

### 13.3 失败请求是否应该写入历史

如果模型调用失败，不应该伪造一条正常 assistant 回复放入对话历史。

更合理的策略是：

- 保存用户消息时标记请求状态；
- 模型成功后保存 assistant 消息；
- 失败时保存错误事件或失败日志；
- 重试成功后再提交最终 assistant 消息；
- 避免下一轮模型把“请求失败提示”误当成业务事实。

你回答“模型返回失败，这轮提问其实是失效的”方向是对的，但在生产系统中还可以保留失败事件用于排查和审计，只是不应把它当成正常对话内容。

### 13.4 安全注意事项

session_id 不能单独作为授权凭证。否则用户可能猜测别人的 session_id 读取聊天记录。

生产系统应把会话绑定到：

- 登录用户 ID；
- 租户 ID；
- 权限范围；
- 服务端生成的不可预测会话标识。

查询时校验“当前用户是否拥有这个 session_id”。

### 13.5 这个知识点在 Agent 系统中负责什么

session 管理连接了 HTTP 请求与 Agent 状态。它负责：

- 让同一个用户继续当前问题；
- 隔离不同用户；
- 保存工具调用上下文；
- 支持人工接管；
- 支持异步任务和重新进入会话；
- 为审计和评估提供数据。

### 13.6 面试官可能怎么问

**问：session_id 相同就一定能保留上下文吗？**

答：只有当后端根据这个 ID 读取到同一份可用历史时才可以。内存字典只适合单进程学习；生产环境需要 Redis、数据库或其他共享存储，并且要做用户权限校验。



## 14. Function Calling / Tool Calling

### 14.1 工具调用解决什么问题

普通模型只能生成文本。客服 Agent 需要：

- 查询订单；
- 查询物流；
- 查询库存；
- 查询用户权益；
- 创建工单；
- 调用 MCP 工具；
- 读取内部系统。

工具调用的本质是：

~~~text
用户问题
  ↓
模型判断是否需要工具
  ↓
模型返回工具名和参数
  ↓
你的 Python 代码真正执行函数
  ↓
把执行结果作为 tool 消息发回模型
  ↓
模型生成面向用户的最终回答
~~~

模型不会自动执行你的 Python 函数。模型只负责提出结构化的调用请求，真正的执行权在应用程序。

### 14.2 工具 schema 示例

~~~python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "查询订单当前状态和预计送达时间",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号，例如 A1001",
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    }
]
~~~

工具 schema 的作用是把可调用能力告诉模型：

- name 是模型要选择的唯一函数名；
- description 帮助模型判断什么时候使用；
- parameters 描述参数结构；
- required 描述必填字段；
- additionalProperties 可以限制额外参数。

不要把工具 schema 当作权限系统。即使模型请求了工具，后端仍然要再次校验参数、用户身份和业务权限。

### 14.3 第一次响应为什么不是最终回答

你实际运行 lesson_10_tool_call.py 时看到：

~~~text
Python 正在执行工具： get_order_status {"order_id": "A1001"}

最终回答：
您好！已为您查询到订单 A1001 的状态：
订单状态：已发货
预计送达时间：明天
~~~

第一次模型响应的关键内容是 tool_calls，而不是面向用户的最终文本。

代码判断通常类似：

~~~python
message = response.choices[0].message

if message.tool_calls:
    for tool_call in message.tool_calls:
        print(tool_call.function.name)
        print(tool_call.function.arguments)
else:
    print(message.content)
~~~

### 14.4 arguments 为什么要 json.loads()

tool_call.function.arguments 看起来像：

~~~text
{"order_id": "A1001"}
~~~

但在 Chat Completions 的工具调用结构里，它通常是 JSON 字符串，不是 Python dict。

所以需要：

~~~python
import json

arguments = json.loads(tool_call.function.arguments)
order_id = arguments["order_id"]
result = get_order_status(order_id)
~~~

这里发生了明确的类型转换：

~~~text
JSON 字符串
  ↓ json.loads()
Python dict
  ↓
Python 函数参数
~~~

你之前说“arguments 已经是对象，为什么还要转换”，需要修正为：

- 外层 tool_call 是 SDK 返回的 Python 对象；
- tool_call.function.arguments 这个字段的值通常仍是字符串；
- SDK 没有替你把 JSON 参数自动转换成业务函数需要的 Python dict；
- 因此应用层必须解析、校验和转换。

### 14.5 你在 NestJS 中其实也做过同一步

你曾经认为 NestJS 版本没有这一步，但检查当前项目中的 AiService 后，可以看到类似：

~~~typescript
const args = JSON.parse(toolCall.function.arguments);
~~~

它位于你项目的工具调用处理逻辑中，例如：

~~~text
src/ai/ai.service.ts
~~~

所以 Python 的 json.loads() 对应 NestJS/TypeScript 的 JSON.parse()。不是 Python 特有的麻烦，而是两种语言对 JSON 字符串做对象解析时使用了不同的标准库函数。

### 14.6 执行工具时不要使用 eval

不安全的做法：

~~~python
eval(tool_call.function.name)(**arguments)
~~~

原因是模型输出不能被当作可信代码。更安全的是显式映射：

~~~python
TOOL_HANDLERS = {
    "get_order_status": get_order_status,
}

tool_name = tool_call.function.name
handler = TOOL_HANDLERS.get(tool_name)

if handler is None:
    raise ValueError(f"不允许调用工具：{tool_name}")

arguments = json.loads(tool_call.function.arguments)
result = handler(**arguments)
~~~

这样只有 TOOL_HANDLERS 中注册的函数才可以被调用。

### 14.7 tool 消息如何回传

执行完工具后，要把两类消息追加到历史：

1. assistant 消息：保留模型产生的 tool_calls；
2. tool 消息：返回工具结果，并携带匹配的 tool_call_id。

示意代码：

~~~python
messages.append(message.model_dump(exclude_none=True))

messages.append(
    {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(result, ensure_ascii=False),
    }
)

follow_up = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=tools,
)
~~~

tool_call_id 的作用是把执行结果和具体的调用请求关联起来。它不是为了“保证方法唯一”，而是为了让模型知道这个结果对应哪一个 tool call。

如果一次响应包含多个 tool_calls，每个调用都应该：

- 取自己的 name；
- 解析自己的 arguments；
- 执行自己的函数；
- 返回自己的 tool_call_id；
- 返回对应的工具结果。

### 14.8 tool 结果为什么必须发回模型

工具执行发生在你的应用程序里，模型并不知道执行结果。

例如工具返回：

~~~json
{
  "order_id": "A1001",
  "status": "已发货",
  "estimated_delivery": "明天"
}
~~~

模型只有重新看到这个 tool 消息，才知道可以基于真实数据组织最终回答。否则模型可能：

- 不知道工具是否成功；
- 不知道订单状态；
- 编造一个订单状态；
- 重复调用同一个工具；
- 直接说“我无法查询”。

你回答“如果没有这个消息，大模型都不知道是否调用了”是正确方向。

### 14.9 auto 与强制工具

tool_choice="auto" 表示交给模型判断：

- 普通问候可以直接回答；
- 查询订单时可以请求 get_order_status；
- 不需要订单信息时不调用工具。

强制指定某个工具时，模型会被要求调用它。若把这个强制行为放进每一轮 Agent 循环，就可能出现：

- 每一轮都重复调用；
- 工具已经返回结果仍被强制调用；
- max_steps 被耗尽；
- 无法自然结束。

因此 auto 不是“永远调用”，而是“允许模型根据上下文决定”。

### 14.10 这个知识点在 Agent 系统中负责什么

Function Calling 是 Agent 连接现实系统的边界。模型负责规划和选择，程序负责：

- 权限校验；
- 参数校验；
- 真正执行；
- 处理异常；
- 记录审计；
- 把结果回传给模型。

### 14.11 面试官可能怎么问

**问：tool_call.function.arguments 是什么类型？**

答：在 Chat Completions 工具调用中通常是 JSON 字符串，需要 json.loads() 转成 Python dict，再做 schema 校验后传给业务函数。TypeScript 中对应 JSON.parse()。

**问：为什么工具执行结果要带 tool_call_id？**

答：一次响应可能有多个工具调用，tool_call_id 用来把每个 tool 结果对应到具体调用请求，保证消息链完整。

**问：模型能直接执行你的函数吗？**

答：不能。模型只产生结构化调用请求，应用程序通过白名单映射执行真实函数，再把结果回传模型。

## 15. Agent Loop：从一次工具调用到多轮循环

### 15.1 为什么需要循环

一次工具调用可能还不够：

~~~text
第 1 轮：模型请求查询订单
第 2 轮：模型读取查询结果并生成最终回答
~~~

如果工具结果还需要另一个工具：

~~~text
第 1 轮：查询订单
第 2 轮：查询物流
第 3 轮：生成最终回答
~~~

所以 Agent 不能只写“调用一次模型、执行一次工具、结束”，而应该有一个有上限的循环。

### 15.2 Agent Loop 的核心伪代码

~~~python
for step in range(max_steps):
    response = call_model(messages, tools=tools)
    message = response.choices[0].message

    if not message.tool_calls:
        return message.content

    messages.append(message.model_dump(exclude_none=True))

    for tool_call in message.tool_calls:
        result = execute_tool_safely(tool_call)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            }
        )

raise RuntimeError("Agent 超过最大步数，可能出现循环")
~~~

### 15.3 max_steps 的真正作用

你实际回答：

> 查询订单时循环执行了两轮。普通问候时没有执行工具。max_steps 为了避免死循环。

这是正确的。

补充一点：max_steps 是上限，不是每次必须执行的轮数。

- 普通问候：第一次模型响应没有 tool_calls，马上结束；
- 查询订单：第一次产生 tool_calls，第二次得到最终回答；
- 复杂任务：可能需要多轮工具；
- 工具或提示词有问题：可能反复调用，最终被 max_steps 截断。

### 15.4 订单不存在与工具异常不是一回事

你测试 order_id=FAIL 时，工具可以正常返回业务结果：

~~~json
{
  "order_id": "FAIL",
  "status": "未找到订单",
  "estimated_delivery": ""
}
~~~

这表示工具执行成功，只是业务上没有查到订单。模型可以根据这个业务结果向用户说明“订单不存在”。

另一种情况是工具内部抛出 RuntimeError：

~~~text
内部工具异常：RuntimeError
~~~

这表示工具执行失败。Agent 应该捕获异常、记录内部日志，并把有限信息作为结构化工具结果返回给模型，例如：

~~~json
{
  "ok": false,
  "error_code": "ORDER_SERVICE_UNAVAILABLE",
  "message": "订单服务暂时不可用"
}
~~~

不要把 Python 堆栈直接展示给用户。模型可以根据 error_code 判断应当道歉、建议稍后重试，而不是伪造订单状态。

### 15.5 工具异常的安全处理

~~~python
def execute_tool_safely(tool_call):
    try:
        arguments = json.loads(tool_call.function.arguments)
        validate_tool_arguments(tool_call.function.name, arguments)
        result = TOOL_HANDLERS[tool_call.function.name](**arguments)
        return {
            "ok": True,
            "data": result,
        }
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error_code": "INVALID_TOOL_ARGUMENTS",
            "message": "工具参数不是合法 JSON",
        }
    except Exception:
        logger.exception("工具执行失败")
        return {
            "ok": False,
            "error_code": "TOOL_EXECUTION_FAILED",
            "message": "工具暂时不可用",
        }
~~~

生产代码还需要更细的异常分类，不能让一个宽泛的 Exception 把所有问题都混在一起。

### 15.6 工具调用的边界

一个成熟的 Agent Loop 至少要控制：

- 最大步骤数；
- 每个工具的超时；
- 工具参数 schema；
- 用户权限；
- 工具白名单；
- 单次调用次数；
- 总耗时；
- 总 token；
- 敏感操作是否需要用户确认；
- 读操作和写操作是否分开。

### 15.7 这个知识点在 Agent 系统中负责什么

Agent Loop 是“模型决策—工具执行—结果回传—再次决策”的运行时控制器。它把一次 LLM 调用升级为能够完成任务的闭环。

### 15.8 面试官可能怎么问

**问：如何避免 Agent 无限调用工具？**

答：设置 max_steps、总耗时和单工具调用上限；识别重复参数；保留完整 tool_call/tool 结果链；对工具错误做结构化返回；必要时要求用户确认副作用操作。

**问：工具返回业务失败和工具执行异常有什么区别？**

答：业务失败表示函数正常执行但查不到数据或业务条件不满足；执行异常表示函数、依赖服务或网络本身失败。两者需要不同的 error_code 和用户提示。

## 16. API 异常与工具异常

### 16.1 两条不同的错误边界

你曾经说：

> API 异常是模型上面的问题，而方法异常是第三方的问题。

方向是想把两类异常分开，但范围说窄了。更准确的区别是：它们发生在不同的执行边界。

模型 API 异常可能来自：

- 认证；
- 网络连接；
- 超时；
- 限流；
- 请求参数；
- 上游模型服务；
- 代理或网关。

工具异常可能来自：

- 你自己的 Python 业务函数；
- PostgreSQL；
- Redis；
- Qdrant；
- MCP server；
- 订单系统；
- 第三方物流 API；
- 参数校验或权限校验。

工具不一定是第三方；API 也不只是模型本身的问题。

### 16.2 常见异常处理表

| 异常 | 常见原因 | 通常策略 | HTTP 映射示例 |
|---|---|---|---|
| APITimeoutError | 等待模型超时 | 有限重试、退避 | 504 |
| APIConnectionError | 网络、代理、TLS | 检查网络、有限重试 | 503 |
| AuthenticationError | Key 无效或无权限 | 修复配置，不重试 | 401/500 |
| RateLimitError | 速率或额度限制 | 退避、限流、检查额度 | 429 |
| BadRequestError | 请求参数不合法 | 修复代码，不重试 | 400 |
| InternalServerError | 上游临时 5xx | 有限重试 | 502/503 |
| APIError | SDK/API 基类异常 | 记录类型并降级 | 502/503 |

实际 HTTP 状态码应根据你的服务契约决定，表格只是常见映射。

### 16.3 API 异常处理示例

~~~python
import openai
from fastapi import HTTPException

try:
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
    )
except openai.APITimeoutError:
    raise HTTPException(status_code=504, detail="模型服务超时")
except openai.AuthenticationError:
    logger.exception("模型认证失败")
    raise HTTPException(status_code=500, detail="模型服务配置错误")
except openai.BadRequestError:
    logger.exception("模型请求参数错误")
    raise HTTPException(status_code=400, detail="请求参数不合法")
except openai.APIError:
    logger.exception("模型 API 异常")
    raise HTTPException(status_code=502, detail="模型服务暂时不可用")
~~~

不要把所有异常都返回原始错误文本。原始异常可能包含内部 URL、请求参数或敏感信息。

### 16.4 这个知识点在 Agent 系统中负责什么

统一异常处理让 Agent 在故障时：

- 对用户返回稳定的业务错误；
- 对日志保留足够的诊断信息；
- 对可重试错误进行恢复；
- 对不可重试错误快速失败；
- 不把内部堆栈和凭证泄露给客户端。

### 16.5 面试官可能怎么问

**问：AuthenticationError 为什么不重试？**

答：它通常代表 Key 无效、过期、撤销或权限不够。除非配置已经被修复，否则重复请求不会改变结果。

**问：工具失败时为什么还要把结果发给模型？**

答：让模型知道工具没有成功，避免模型把缺失数据当成真实数据编造答案。工具结果可以是结构化错误对象，最终由模型生成用户可理解的提示。


## 17. FastAPI 最小聊天服务

### 17.1 为什么需要 FastAPI 层

直接运行 Python 脚本只能在终端发起请求。客服系统需要：

- 前端通过 HTTP 调用；
- 接收 JSON 请求体；
- 校验字段；
- 返回 JSON；
- 统一处理超时和异常；
- 后续支持 session_id、流式输出和工具调用。

FastAPI 负责 HTTP 接入层；OpenAI Python SDK 负责模型调用；你的业务代码负责会话、工具和错误策略。

### 17.2 /health 与 /chat

你实现并测试过两个核心接口：

~~~python
@app.get("/health")
async def health():
    return {"status": "ok"}
~~~

/health 是健康检查接口，主要确认：

- FastAPI 进程是否启动；
- 路由是否可以访问；
- 基本服务是否存活。

它不代表模型 API、Redis、PostgreSQL 或 Qdrant 一定正常。如果要做更完整的 readiness 检查，还应该分别检查关键依赖。

聊天接口可以用 Pydantic 模型校验请求：

~~~python
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=2000)

@app.post("/chat")
async def chat(request: ChatRequest):
    answer = await call_model(request.message)
    return {
        "session_id": request.session_id,
        "answer": answer,
    }
~~~

你回答“ChatRequest 的作用是校验输入参数类型和长度”是正确的。它的价值还包括：

- 统一请求结构；
- 自动生成 OpenAPI/Swagger 文档；
- 在请求进入业务逻辑前拒绝非法数据；
- 让函数参数有明确类型；
- 避免把空字符串或异常长度直接送给模型。

### 17.3 异步路由

模型请求是网络 I/O，适合：

~~~python
@app.post("/chat")
async def chat(request: ChatRequest):
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request.message},
        ],
    )
    return {
        "answer": response.choices[0].message.content,
    }
~~~

这里的 await 表示当前协程在等待网络结果期间可以把控制权交还事件循环，让其他请求有机会运行。

它不代表：

- 模型请求会更快；
- 总计算量变少；
- 所有代码都不会阻塞；
- 自动创建多个线程；
- 一定比同步代码吞吐高。

如果在 async 路由里直接调用长时间阻塞的同步函数，仍可能阻塞事件循环。异步是否有收益，要看具体 I/O 库和部署方式。

### 17.4 你关于 FastAPI 的几个回答修正

你说“FastAPI 本身也是单线程事件循环加线程池”。这个说法需要更谨慎：

- FastAPI 通常运行在 ASGI 服务器上，例如 Uvicorn；
- async 路由由事件循环调度；
- 普通 def 路由可以由框架放到线程池执行；
- 多 worker 可以启动多个进程；
- 具体线程和进程行为取决于服务器、配置和代码；
- FastAPI 不等于固定的“单线程加线程池”模型。

你说“异步应该快一点，因为没有阻塞主进程”，也需要补充：

- 异步主要改善 I/O 等待期间的并发利用率；
- 单个模型请求的服务端生成速度不会因为 await 自动变快；
- 如果任务是 CPU 密集型，异步通常不能解决 CPU 阻塞；
- 如果函数本身阻塞事件循环，使用 async 语法也没有实际收益。

### 17.5 timeout 在 FastAPI 中的统一处理

~~~python
from fastapi import HTTPException

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.message},
            ],
        )
    except openai.APITimeoutError:
        raise HTTPException(
            status_code=504,
            detail="模型服务响应超时，请稍后重试。",
        )

    return {
        "answer": response.choices[0].message.content,
        "usage": response.usage.model_dump() if response.usage else None,
    }
~~~

### 17.6 你实际测试得到的结果

你用 PowerShell 请求 /health 得到：

~~~text
status
------
ok
~~~

你调用 /chat 后得到了 answer 和 usage。后来返回结构包括：

~~~json
{
  "answer": "RAG（检索增强生成）是一种让大语言模型在回答问题前先从外部知识库检索相关信息，再结合检索结果生成答案的技术。",
  "usage": {
    "completion_tokens": 216,
    "prompt_tokens": 31,
    "total_tokens": 247
  }
}
~~~

这说明：

- HTTP 路由可访问；
- 请求体能被 Pydantic 解析；
- 模型调用成功；
- 响应能够被序列化为 JSON；
- usage 可以作为观测信息返回。

生产接口是否直接把 usage 返回给前端，要根据产品需要决定；也可以只写日志或监控。

### 17.7 配置命名要保持一致

你前面使用过：

~~~text
OPENAI_API_KEY
LLM_BASE_URL
LLM_MODEL
~~~

之后某份 FastAPI 代码使用了：

~~~text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
~~~

两者都可以，但程序读取的名字必须和实际环境变量一致。否则会出现：

- required_env 找不到变量；
- model 为 None；
- base_url 为 None；
- 使用了错误的默认服务；
- 启动时才发现配置问题。

建议在一个项目内选定一套名字，并通过 .env.example 明确列出：

~~~text
OPENAI_API_KEY=
LLM_BASE_URL=
LLM_MODEL=
~~~

### 17.8 FastAPI 与 NestJS 的对应关系

| NestJS | FastAPI/Python |
|---|---|
| Controller 路由 | @app.get 或 @app.post |
| DTO class-validator | Pydantic BaseModel/Field |
| @Body() | 函数参数中的请求模型 |
| Injectable Service | 普通模块、类或依赖注入函数 |
| async/await | async/await |
| HttpException | HTTPException |
| Response DTO | dict 或 Pydantic response_model |
| RxJS/Observable 流 | async generator/StreamingResponse |

结构相似，但不是逐行翻译：

- NestJS 常把路由与 Service 组织在 class 中；
- FastAPI 学习阶段可以先用模块函数；
- NestJS 的装饰器对应 FastAPI 的路由声明和类型注解；
- 两者都需要自己设计会话、错误、重试和工具执行边界。

### 17.9 这个知识点在 Agent 系统中负责什么

FastAPI 是 Agent 的外部接口层。它把内部 Agent Loop 暴露为：

- 普通问答 API；
- 带 session_id 的多轮 API；
- 流式 SSE API；
- 健康检查 API；
- 后续的工具审批和任务状态 API。

### 17.10 面试官可能怎么问

**问：为什么 /health 返回 ok 不能证明整个 AI 服务正常？**

答：它通常只检查 Web 服务进程和路由。模型、Redis、数据库、Qdrant、MCP 等依赖需要单独的 readiness 检查或依赖探针。

**问：为什么异步调用不一定让单个请求更快？**

答：异步主要避免当前协程在 I/O 等待期间阻塞事件循环，提高并发利用率；模型服务端生成时间不会因为使用 await 自动变短。



## 18. FastAPI SSE 与 POST 流式输出

### 18.1 SSE 的消息格式

Server-Sent Events 的基本消息通常是：

~~~text
data: {"content":"R"}

data: {"content":"AG"}

data: [DONE]

~~~

每条事件以两个换行符结束，也就是事件之间使用空行分隔。

后端可以用异步生成器逐条产生：

~~~python
import json
from collections.abc import AsyncIterator

def make_sse_data(payload: object) -> str:
    data = json.dumps(payload, ensure_ascii=False)
    return f"data: {data}\n\n"

async def generate_sse(message: str) -> AsyncIterator[str]:
    stream = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是专业的 AI 客服，请简洁准确地回答。",
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        stream=True,
    )

    async for chunk in stream:
        if not chunk.choices:
            continue

        content = chunk.choices[0].delta.content
        if content:
            yield make_sse_data({"content": content})

    yield "data: [DONE]\n\n"
~~~

然后用 StreamingResponse 返回：

~~~python
from fastapi.responses import StreamingResponse

@app.get("/chat/stream")
async def chat_stream(message: str):
    return StreamingResponse(
        generate_sse(message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
~~~

### 18.2 上游流和下游流是两个层次

你之前说 NestJS SSE 和 Python SSE 没什么区别，这个判断从“网络效果”看基本正确，但需要区分两条流：

~~~text
上游：模型服务 → Python/FastAPI
      stream=True，async for 读取模型 chunk

下游：Python/FastAPI → 浏览器
      StreamingResponse，按 SSE 格式 yield
~~~

Python 服务先作为模型客户端读取上游流，再把内容包装成下游 SSE。NestJS 中同样可能：

~~~typescript
for await (const chunk of finalStream) {
  res.write("data: " + JSON.stringify(chunk) + "\n\n");
}
~~~

所以不是“async for 负责 SSE”。更准确地说：

- async for 负责异步迭代上游流；
- yield 负责从生成器产生下游数据；
- StreamingResponse 负责把生成器暴露为 HTTP 响应；
- data: 内容和双换行决定 SSE 的事件格式。

### 18.3 delta.content 为什么不是完整答案

流式 chunk 通常是增量事件。delta.content 取的是本次事件中新增的文本片段。

它可能是：

~~~text
R
AG（检索增强
生成）
~~~

不能假设每个 chunk：

- 恰好是一个 token；
- 一定有 content；
- 一定只包含文本；
- 每个 chunk 都是完整 JSON；
- 第一个 chunk 就含有完整 role；
- 最后一个 chunk 一定还有文本。

因此要跳过没有 choices 或没有 content 的 chunk，并在服务端或前端按需拼接。

### 18.4 为什么不能把每个 chunk 保存成聊天记录

你回答“每个 chunk 存一条会浪费资源，历史不方便”是正确的。还可以具体化：

- 数据库行数暴增；
- 索引和查询成本增加；
- 同一条回答被拆成大量碎片；
- 事务和写放大；
- 回放历史时需要再次排序拼接；
- 统计 token 和消息状态更复杂；
- 中途断开时会留下大量不完整碎片。

更常见的做法是：

1. 流式输出给前端；
2. 服务端在内存中累计文本；
3. 发送 DONE 后，把完整 assistant 消息一次性保存；
4. 如果连接中断，记录 interrupted 状态或保存可恢复草稿。

### 18.5 flush=True 的作用

在终端流式打印中：

~~~python
print(content, end="", flush=True)
~~~

flush=True 表示立即刷新标准输出缓冲区，尽快把已写入的内容交给终端显示。

如果不 flush，内容可能先留在 stdout 缓冲区里，用户看不到逐步输出，而是过一段时间集中出现。

注意：

- flush=True 影响终端 stdout；
- 它不是 SSE 协议；
- 它不是 HTTP chunk 的唯一控制手段；
- FastAPI 的 StreamingResponse 是否及时传输，还会受到 ASGI 服务器、代理、缓存和网络缓冲影响。



### 18.6 GET、EventSource 与 POST

浏览器原生 EventSource API 主要用于 GET SSE 连接：

~~~javascript
const source = new EventSource(
  "/chat/stream?message=" + encodeURIComponent(message)
);

source.onmessage = (event) => {
  if (event.data === "[DONE]") {
    source.close();
    return;
  }

  const payload = JSON.parse(event.data);
  appendText(payload.content);
};

source.onerror = () => {
  source.close();
};
~~~

你回答：

1. EventSource 只能 GET；
2. event.data 是服务端 data 行里的字符串；
3. 收到 [DONE] 后关闭连接；
4. POST 使用 fetch 加 ReadableStream。

这四点方向都是对的。

补充两个细节：

- EventSource 的 GET 限制来自浏览器 API，不是 SSE 协议规定只能 GET；
- HTTP 本身可以用 POST 返回 text/event-stream，FastAPI 的 StreamingResponse 也可以；
- 只是浏览器原生 EventSource 无法让你自定义 POST body；
- 需要请求体时可用 fetch，然后读取 response.body。



### 18.7 POST + fetch + ReadableStream

后端：

~~~python
class StreamRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

@app.post("/chat/stream-post")
async def chat_stream_post(request: StreamRequest):
    return StreamingResponse(
        generate_sse(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
~~~

前端最小读取示意：

~~~javascript
const response = await fetch("/chat/stream-post", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: "请用三句话解释什么是 RAG",
  }),
});

if (!response.ok) {
  throw new Error("HTTP " + response.status);
}

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = "";

while (true) {
  const result = await reader.read();
  const value = result.value;
  const done = result.done;

  if (done) {
    break;
  }

  buffer += decoder.decode(value, { stream: true });

  const events = buffer.split("\n\n");
  buffer = events.pop() ?? "";

  for (const event of events) {
    if (!event.startsWith("data: ")) {
      continue;
    }

    const data = event.slice("data: ".length);

    if (data === "[DONE]") {
      await reader.cancel();
      break;
    }

    const payload = JSON.parse(data);
    appendText(payload.content);
  }
}
~~~

这里的 buffer 很重要。一次 reader.read() 不一定刚好得到一条 SSE 事件，可能出现：

- 半条事件；
- 多条事件；
- JSON 被拆成两段；
- 一段中包含多个事件。

所以不能每次 read 后直接 JSON.parse 整块内容，应该先按 SSE 分隔符组装事件。



### 18.8 event.data、[DONE] 与 reader.done

这三个概念不同：

- event.data：浏览器 EventSource 解析后提供的 data 字符串；
- [DONE]：你们应用约定的业务结束标记；
- reader.read() 返回的 done：底层 HTTP readable stream 已经结束。

通常先收到 [DONE]，前端主动关闭；如果网络断开，可能直接得到 reader done，却没有 [DONE]。

### 18.9 流开始后错误如何处理

普通 JSON API 可以在响应头阶段返回 504 或 502。SSE 开始发送数据后，HTTP 状态码通常已经发出，不能中途改成新的状态码。

因此流式生成器中可以发送：

~~~text
event: error
data: {"code":"timeout","message":"模型请求超时，请稍后重试。"}

~~~

前端需要监听 error 事件或解析事件名，再结束 UI 状态。


### 18.10 你遇到的 PowerShell/curl 坑

你第一次使用 curl.exe POST 时遇到：

~~~json
{
  "detail": [
    {
      "type": "json_invalid",
      "msg": "JSON decode error"
    }
  ]
}
~~~

当时后端代码和环境配置都没有问题，真正问题是 PowerShell 中引号、反斜杠和 curl 参数传递导致服务端收到的内容不是合法 JSON。

你后来采用一行命令：

~~~powershell
$payload = '{"message":"Explain RAG in three sentences"}'
$payload | curl.exe -N -X POST "http://127.0.0.1:8000/chat/stream-post" -H "Content-Type: application/json" --data-binary "@-"
~~~

请求成功。这里：

- $payload 先保存完整 JSON 字符串；
- 管道把它写到 curl.exe 的标准输入；
- --data-binary "@-" 表示从 stdin 读取原始请求体；
- Content-Type 告诉 FastAPI 按 JSON 解析。

### 18.11 中文显示乱码不一定是后端乱码

你使用 Invoke-RestMethod 时看到过类似：

~~~text
æ¨å¥½ï¼
~~~

这更像是 PowerShell 输出编码显示不匹配，不一定说明服务端响应内容已经损坏。Swagger 中能够显示：

~~~text
data: {"content": "中文测试成功"}

data: [DONE]
~~~

说明后端至少已经正确产生了 UTF-8 SSE 数据。

如果需要在 Windows PowerShell 中排查，可以尝试：

~~~powershell
chcp 65001
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
~~~

不同 PowerShell 版本、终端和 curl.exe 组合的编码行为可能不同。可以分别检查：

1. Swagger 是否正确；
2. curl.exe 是否原样收到 UTF-8；
3. 服务端日志中的 request body；
4. 浏览器 fetch 解码后的文本。

你还遇到过中文请求从 PowerShell stdin 传给 curl 后变成问号，导致模型误以为用户输入不清楚。这说明请求体编码和响应显示编码是两个不同问题。

### 18.12 SSE 是否只能用 GET

不能把“EventSource 只能发 GET”扩大成“SSE 只能用 GET”。

准确区分：

- SSE 是一种服务端向客户端持续推送的事件格式和连接方式；
- HTTP 方法本身可以是 GET 或 POST；
- 原生 EventSource API 通常只能发起 GET；
- FastAPI StreamingResponse 可以响应 POST；
- POST 场景通常由 fetch 读取 ReadableStream；
- 若要使用 POST + 浏览器自动重连，需要自己实现重连、事件 ID 和状态恢复。

### 18.13 这个知识点在 Agent 系统中负责什么

流式输出负责降低用户感知延迟：

- 用户先看到模型开始回答；
- 长回答不用等完整生成后才显示；
- Agent 可以把状态、工具进度和文本分开推送；
- 前端可以展示“正在查询订单”“正在检索知识库”等状态。

但流式输出不会自动解决：

- 历史消息持久化；
- 中途断线恢复；
- 取消模型请求；
- 多 worker 状态共享；
- 代理缓冲；
- 工具副作用安全；
- 最终消息的完整保存。

### 18.14 面试官可能怎么问

**问：为什么 EventSource 只能 GET，但你还实现了 POST 流式接口？**

答：限制来自浏览器原生 EventSource API，不是服务器端 SSE 不能使用 POST。FastAPI 可以用 StreamingResponse 响应 POST，前端用 fetch 和 ReadableStream 读取。

**问：为什么不能每次 read 后直接 JSON.parse？**

答：网络读取边界和 SSE 事件边界不一致。一块数据可能是半个 JSON，也可能包含多个事件，所以要用 buffer 按两个换行符切分完整事件。

**问：收到 [DONE] 后为什么 close？**

答：[DONE] 是应用层约定的生成结束标记，收到后可以结束 UI 状态并关闭客户端连接，避免继续监听或等待。


## 19. 这次阶段的踩坑总表

### 19.1 环境与 SDK

| 踩坑 | 现象 | 正确理解 |
|---|---|---|
| 先在全局 Python 安装 openai | pip show 显示在 Python315 的全局 site-packages | 创建 .venv 后，必须在激活环境里重新安装 |
| 没确认解释器 | 不知道当前脚本用哪个 Python | 用 sys.executable、sys.prefix、sys.base_prefix 检查 |
| 环境变量名称不一致 | OPENAI_MODEL、LLM_MODEL、OPENAI_BASE_URL、LLM_BASE_URL 混用 | 程序读取名和实际设置名必须一致 |
| 把 API Key 和 Base URL 混为一谈 | 认为它们都是模型服务器地址 | Key 负责认证；Base URL 负责请求发送到哪个兼容 API 服务 |
| 使用 client.chat.create | 报 Chat object has no attribute create | Chat Completions 的路径是 client.chat.completions.create |
| 把真实 Key 打到终端日志 | 日志里出现完整 API Key | 永远不要打印、提交或写入文档；已经暴露的 Key 应立即轮换 |

### 19.2 消息与多轮对话

| 踩坑 | 现象 | 正确理解 |
|---|---|---|
| 认为模型自动记住上一轮 | 只发送当前 user 消息，却期待模型记住名字 | API 调用通常是无状态的，应用必须传历史或读取会话存储 |
| 不保存 assistant 消息 | 第二轮缺少模型之前的回答 | assistant 消息也是上下文的一部分，尤其是澄清和任务状态 |
| 把 session_id 当作记忆 | 只换或复用 ID 就以为会自动记忆 | ID 只是查找键，真正的历史在内存、Redis 或数据库 |
| 以为内存字典是持久化 | 服务重启后历史消失 | 内存只适合学习或单进程临时状态 |
| 删除系统提示词来裁剪 | 规则和角色消失 | 系统提示词应作为核心上下文保留 |
| 从 tool 消息中间截断 | 模型看见孤立 tool 结果或未完成调用 | assistant tool_calls 和对应 tool 结果要原子保留 |

### 19.3 异步与流式

| 踩坑 | 现象 | 正确理解 |
|---|---|---|
| 认为 async 一定更快 | 单个模型请求速度没有明显变化 | async 主要提高 I/O 等待期间的并发利用率 |
| 认为 async 永远不阻塞 | 在 async 路由中调用阻塞同步函数 | 阻塞代码仍可能卡住事件循环 |
| 不清楚 flush=True | 只知道和输出有关 | 它刷新终端 stdout 缓冲，不是 SSE 协议 |
| 把一个 chunk 当一个 token | 用 chunk 数估算 token 数 | chunk 是传输增量，和 tokenizer 的 token 不是同一概念 |
| 把上游流和下游 SSE 混为一谈 | 认为 async for 自己就完成 SSE | async for 读取模型流，StreamingResponse/yield 才负责下游输出 |
| 每个 chunk 保存一条消息 | 历史被拆成大量记录 | 累计完整 assistant 文本后再保存 |

### 19.4 JSON、Token、超时与重试

| 踩坑 | 现象 | 正确理解 |
|---|---|---|
| JSON Mode 等于业务 schema | 以为字段一定存在且类型正确 | JSON 语法和业务结构是两层校验 |
| 只关注 completion_tokens | 忽略上下文成本 | prompt_tokens 包含历史、工具 schema、工具结果和 RAG |
| 不裁剪历史 | 输入 token 持续增长 | 结合窗口、摘要、profile 和 token 预算 |
| 把秒/毫秒归因于语言 | 认为 Python 固定秒、Node 固定毫秒 | 由具体 SDK 参数约定决定 |
| max_attempts=3 误认为重试 3 次 | 实际出现 3 次请求 | 总尝试 3 次，最多重试 2 次 |
| 所有错误都重试 | AuthenticationError 反复请求 | 按错误类型白名单重试 |
| 只重试超时，不考虑副作用 | 订单、退款可能重复执行 | 写操作必须做幂等或查询状态 |

### 19.5 Function Calling 与 Agent

| 踩坑 | 现象 | 正确理解 |
|---|---|---|
| 认为 arguments 已经是 Python dict | 直接传给函数失败 | arguments 通常是 JSON 字符串，要 json.loads() |
| 误以为 NestJS 没有这一步 | 忘记当前 AiService 中有 JSON.parse | Python json.loads() 对应 TypeScript JSON.parse() |
| 不把 tool 结果回传模型 | 模型不知道工具是否成功 | 追加 assistant tool_calls 和 role=tool 消息 |
| 不使用 tool_call_id | 多个工具调用难以对应 | 每个工具结果要关联自己的调用 ID |
| tool 名称直接执行 | 使用 eval 或动态执行 | 使用白名单 TOOL_HANDLERS |
| 强制工具每轮调用 | Agent 重复调用直到达到上限 | auto 允许模型自主判断，写操作要单独控制 |
| 没有 max_steps | Agent 可能无限循环 | 设置步骤、耗时和调用次数上限 |
| 把业务未找到当系统异常 | 用户只输入不存在订单时直接报系统故障 | 业务空结果和工具执行异常分开建模 |
| 把所有错误都交给模型 | 模型看到堆栈后泄露内部细节 | 内部日志保留堆栈，给模型结构化、脱敏的错误结果 |

### 19.6 FastAPI、SSE 与 PowerShell

| 踩坑 | 现象 | 正确理解 |
|---|---|---|
| /health 返回 ok 就认为全链路正常 | 模型或数据库仍可能不可用 | health、readiness 和依赖探针职责不同 |
| 认为 EventSource 限制等于 SSE 只能 GET | POST 流式接口被误判不支持 | 原生 EventSource 主要限制 GET；POST 可用 fetch 读取流 |
| 看到乱码就认为后端乱码 | Invoke-RestMethod 显示 mojibake | 先区分 UTF-8 响应和终端显示编码 |
| curl JSON 引号错误 | FastAPI 返回 json_invalid | 先保存 payload，再用 stdin 和 data-binary 传输 |
| 中文 stdin 变成问号 | 模型理解成乱码 | 检查 PowerShell、curl 和控制台编码链路 |
| event.data 直接当对象 | JSON.parse 报错 | event.data 是字符串 |
| 把 [DONE] 当 JSON | JSON.parse 失败 | 先判断结束标记，再解析普通 data |
| 把 reader done 当 [DONE] | 断线和正常结束无法区分 | [DONE] 是应用标记，done 是底层流关闭 |
| 每次 read 直接 JSON.parse | 偶发解析失败 | 用 buffer 按 SSE 事件边界组装 |

## 20. 面试问题与可用回答

### 20.1 OpenAI Python SDK

**问：你如何在 Python 中配置 OpenAI 兼容客户端？**

答：我在虚拟环境中安装固定版本的 openai SDK，使用环境变量读取 API Key、Base URL 和模型名，再创建 OpenAI 或 AsyncOpenAI 客户端。API Key 不写入源代码，Base URL 用于切换官方服务或兼容服务，模型名也由环境变量管理。

**问：为什么要使用虚拟环境？**

答：隔离项目依赖和全局 Python。当前项目的 openai、pydantic、httpx 等版本不会污染其他项目，也方便生成依赖清单和复现环境。

**问：普通调用和异步调用的区别是什么？**

答：普通 OpenAI 客户端直接返回结果；AsyncOpenAI 返回可等待的协程，需要 await。异步主要改善网络 I/O 等待期间的并发利用率，不会自动缩短模型生成时间。

### 20.2 消息与上下文

**问：system、user、assistant、tool 分别负责什么？**

答：system 定义全局角色、规则和边界；user 是用户输入；assistant 是模型历史输出，包括普通文本和工具调用请求；tool 是应用执行工具后返回给模型的结果。

**问：为什么 API 调用要手动传历史？**

答：模型调用通常是无状态的。服务端如果没有会话机制，模型不会自动知道上一轮内容。应用需要保存并重新发送相关消息，或者使用服务端会话能力。

**问：上下文裁剪为什么不能简单按数组下标切？**

答：普通对话可以按窗口裁剪，但工具调用有消息依赖。assistant tool_calls 和对应的 tool 结果必须作为完整组保留，否则模型可能看到孤立结果或未完成调用。

### 20.3 流式输出

**问：stream=True 改变了什么？**

答：它让模型响应以增量事件返回，而不是等待完整文本一次性返回。客户端可以逐块显示，降低用户感知延迟。

**问：为什么读取 delta.content？**

答：Chat Completions 流式事件把本次新增内容放在 choice 的 delta 中，content 是其中的文本增量。某些事件可能没有 content，所以要先判断。

**问：chunk 是 token 吗？**

答：不是。chunk 是传输层增量，可能包含一个或多个 token，也可能包含角色、结束原因或空内容。准确 token 数应以 usage 或 tokenizer 统计为准。

**问：flush=True 和 SSE 是什么关系？**

答：flush=True 只刷新终端 stdout 缓冲；SSE 是 HTTP 响应格式。二者都能让内容更早显示，但属于不同层次。

### 20.4 超时、重试、Token

**问：你如何设计 API 重试？**

答：只对白名单中的临时异常重试，例如超时、连接失败、限流和临时 5xx；使用指数退避和随机抖动，限制总尝试次数；认证和请求参数错误不重试。

**问：为什么不能无脑重试退款工具？**

答：超时并不代表服务端没有执行。第一次退款可能已经成功但响应丢失，再次请求可能重复退款。要使用幂等键、查询原操作状态或人工确认。

**问：RAG 为什么会增加成本？**

答：检索结果通常拼进 prompt，所以会增加输入 token；输出 token 不一定增加。需要控制 top_k、片段长度、重复内容和上下文预算。

**问：Token 统计中输入部分包括什么？**

答：系统指令、当前问题、历史消息、工具 schema、工具调用消息、工具结果和 RAG 上下文都可能属于输入。

### 20.5 Function Calling 与 Agent

**问：工具调用的完整流程是什么？**

答：先把工具 JSON schema 提供给模型；模型返回 tool_calls；应用解析函数名和 JSON 参数；通过白名单执行真实函数；把 assistant tool_calls 和 role=tool 结果追加回消息；再次调用模型，直到得到没有 tool_calls 的最终回答或达到 max_steps。

**问：arguments 为什么要解析？**

答：SDK 返回的 function.arguments 通常是 JSON 字符串，不是业务函数可以直接使用的 Python dict。要先 json.loads()，再做参数校验。

**问：模型可以直接执行数据库查询吗？**

答：不能。模型只能提出调用请求，数据库查询必须由应用程序执行。这样才能控制权限、参数、超时、审计和返回结果。

**问：max_steps 为什么必要？**

答：模型、工具结果或提示词可能导致重复调用。max_steps 是硬上限，避免无限循环、无限成本和请求长期占用。

### 20.6 FastAPI 与 SSE

**问：FastAPI 中 BaseModel 的作用是什么？**

答：定义请求数据结构并做类型、长度和字段校验，同时生成 OpenAPI 文档。它把非法输入挡在模型调用之前。

**问：EventSource 和 fetch 流读取怎么选？**

答：只需要 GET 和浏览器原生 SSE 自动重连时可以用 EventSource；需要 POST body、自定义 headers 或更灵活的控制时使用 fetch + ReadableStream。

**问：为什么 SSE 开始后不能返回新的 504？**

答：响应头和状态码通常已经发送。后续只能发送事件内容，例如 event:error 和结构化错误数据，不能再把已建立的 HTTP 响应改成另一种状态码。

## 21. 当前能写进简历与暂时不能写的内容

### 21.1 当前可以写，但面试必须能演示

以下内容你已经通过实际脚本或服务测试过：

> 使用 Python OpenAI 兼容 SDK 实现同步、异步模型调用，支持环境变量配置、JSON 结构化输出、流式增量输出、请求超时、有限重试与指数退避。

> 基于 Chat Completions 的消息历史实现多轮对话，并通过上下文窗口控制输入规模，统计 prompt、completion 和 total token 使用情况。

> 实现基于 Function Calling 的订单状态查询 Agent：解析模型返回的工具名和 JSON 参数，执行白名单工具，将 tool 结果回传模型并通过 max_steps 控制 Agent Loop。

> 使用 FastAPI 构建异步聊天接口，基于 Pydantic 校验请求，统一映射模型超时和 API 异常，并返回回答及 usage 信息。

> 使用 FastAPI StreamingResponse 实现 SSE 流式输出，并通过 POST 请求体配合浏览器 ReadableStream 读取增量内容。

> 实现基于 session_id 的单进程内存多轮对话和基础上下文裁剪。

这些表述的前提是：你能重新运行示例、解释关键代码，并明确这是学习项目或最小实现。

### 21.2 现在暂时不要写

以下内容目前还没有在 Python 项目中完整实现或验证，不应直接写成“已掌握”：

- Python Redis 分布式会话和 TTL；
- PostgreSQL 聊天历史持久化；
- 多 worker 下的一致会话状态；
- 生产级 SSE 断线恢复、心跳、取消和事件重放；
- 反向代理下的 SSE 缓冲配置和压测；
- 生产级工具审批和高风险操作确认；
- 订单、退款等写工具的完整幂等系统；
- Python 版本的完整 RAG pipeline；
- Embedding、文档切块、Qdrant upsert 和检索评估；
- Python 版本的 MCP Client/Server 集成；
- 生产级 tracing、指标、告警和成本控制；
- 复杂 Agent 的评估集和自动回归测试。

你在 Node/NestJS 项目中真正做过的技术可以写在 Node 项目经历里，但不要把它们自动移植成“Python 已实现”。

## 22. 第三阶段阶段总结

### 22.1 你真正掌握了什么

你已经建立了从模型 API 到 Agent 服务的完整基础链路：

~~~text
虚拟环境
  ↓
环境变量与 SDK 配置
  ↓
普通 Chat Completions
  ↓
system/user/assistant 消息
  ↓
手动多轮历史
  ↓
AsyncOpenAI 与 await
  ↓
stream=True 与增量 delta
  ↓
JSON Mode 与 json.loads
  ↓
timeout 与异常捕获
  ↓
有限重试与指数退避
  ↓
usage 与 Token 成本
  ↓
上下文裁剪与 session_id
  ↓
Function Calling
  ↓
工具执行与 tool 消息
  ↓
Agent Loop 与 max_steps
  ↓
FastAPI /chat
  ↓
SSE GET 与 POST 流式接口
~~~

### 22.2 你实际做过的代码和验证

你完成或运行过：

- lesson_01_chat.py：最小模型调用；
- lesson_02_multi_turn.py：多轮历史；
- lesson_03_async.py：异步调用；
- lesson_04_stream.py：终端流式输出；
- lesson_05_json.py：JSON 结构化输出；
- lesson_06_timeout.py：超时；
- lesson_07_retry.py：有限重试；
- lesson_08_usage.py：usage 统计；
- 上下文裁剪练习：保留系统提示、裁剪旧历史；
- lesson_10_tool_call.py：订单查询工具调用；
- lesson_11_agent_loop.py：Agent 多轮循环和工具异常；
- lesson_12_api_error.py：统一 API 异常处理；
- FastAPI /health 和 /chat；
- FastAPI /chat/stream；
- FastAPI /chat/stream-post；
- PowerShell、curl.exe 和 Swagger 测试。

### 22.3 你答得不完整或需要修正的重点

1. “Python 时间单位是秒、Node 时间单位是毫秒”  
   应改为“由具体 SDK 参数约定决定”。

2. “异步不会阻塞总进程”  
   应改为“正确的异步 I/O 可以避免当前协程在等待期间阻塞事件循环，但阻塞同步代码仍会阻塞”。

3. “异步一定更快”  
   应改为“主要提升 I/O 等待期间的并发利用率，不保证单个模型请求更快”。

4. “工具异常就是第三方异常”  
   应改为“按执行边界区分；工具可能是本地函数、数据库、Redis、Qdrant、MCP 或第三方服务”。

5. “arguments 已经是对象”  
   应改为“外层响应是 SDK 对象，但 function.arguments 通常是 JSON 字符串”。

6. “tool_call_id 保证方法唯一”  
   应改为“把工具结果关联到具体调用，尤其支持一次响应中的多个工具调用”。

7. “RAG 一定导致输出 token 增加”  
   应改为“RAG 主要增加输入 token，输出由生成内容决定”。

8. “SSE 只能 GET”  
   应改为“原生 EventSource 主要只能 GET，HTTP 和 FastAPI 可以用 POST 返回 text/event-stream”。

9. “失败这一轮完全失效”  
   应改为“不要伪造正常 assistant 回复；可以记录失败事件、重试状态和审计日志”。

10. “max_attempts=3 是重试三次”  
    应改为“总尝试三次，最多重试两次”。

### 22.4 下一阶段建议

下一阶段进入 Python 原生 RAG：

1. 文档加载和清洗；
2. 文本切块；
3. Embedding API；
4. Qdrant collection；
5. 向量写入；
6. 相似度检索；
7. 把检索结果拼入 prompt；
8. 用来源信息约束模型；
9. 评估召回和回答质量；
10. 把 RAG 接入当前 FastAPI Agent。

仍然先不依赖 LangChain，先把检索、上下文拼接和模型调用的底层链路写清楚，再考虑框架封装。

## 23. 官方资料

以下资料用于继续查 API 细节，代码仍应以你当前使用的兼容服务实际支持范围为准：

- OpenAI Python API library：  
  https://developers.openai.com/api/reference/python

- Chat Completions create：  
  https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create

- Function calling：  
  https://developers.openai.com/api/docs/guides/function-calling

- OpenAI API error codes：  
  https://developers.openai.com/api/docs/guides/error-codes

- Python asyncio：  
  https://docs.python.org/3/library/asyncio.html

- FastAPI StreamingResponse：  
  https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse

- HTML Server-Sent Events 标准：  
  https://html.spec.whatwg.org/multipage/server-sent-events.html

注意：OpenAI 官方文档当前把 Responses API 作为主要文本 API，同时仍支持 Chat Completions。你这第三阶段的目标是理解 Chat Completions、工具消息和 Agent Loop 底层原理，因此学习代码继续沿用你已有的 Chat Completions 思路；进入后续阶段时再专门比较 Responses API 与 Chat Completions 的消息模型和工具调用差异。

