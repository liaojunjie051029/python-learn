# 第四阶段学习文档：手写 Function Calling Agent

> 学习目录：C:\text\python\learning4
>
> 主文件：lesson1_tool_registry.py
>
> 学习时间：2026-10-23
>
> 本文档只记录已经实际运行、讨论和验证过的内容，并明确区分“已经完成”和“只是讨论过”的内容。

---

## 1. 学习背景和本阶段目标

### 1.1 已有背景

我已经掌握：

- TypeScript；
- Node.js；
- NestJS；
- OpenAI SDK；
- Function Calling；
- MCP；
- Redis；
- Prisma；
- PostgreSQL；
- Qdrant；
- SSE。

已有 AI 客服项目：

~~~
C:\text\ai-customer-service
~~~

Python 环境：

- Python 3.15；
- Windows；
- VS Code；
- PowerShell。

### 1.2 本阶段目标

不使用 LangChain，从底层手写一个 Agent，完整实现：

~~~
用户问题
  ↓
模型判断是否需要工具
  ↓
模型生成 tool_call
  ↓
Python 解析工具名称和参数
  ↓
执行工具
  ↓
把工具结果作为 tool 消息返回给模型
  ↓
模型生成最终回答
~~~

计划实现的能力：

1. 工具定义；
2. 工具注册表；
3. 工具执行器；
4. 统一 ToolResult；
5. 工具参数校验；
6. tool 消息；
7. 最大循环次数；
8. 工具异常处理；
9. 多工具调用；
10. 日志和调试信息。

使用的工具：

- local_get_current_time；
- local_get_product_info；
- local_get_url。

其中：

- local_get_current_time 已完成；
- local_get_product_info 已完成，使用模拟产品数据；
- local_get_url 按学习过程中的决定跳过，没有实现。

---

## 2. 环境和 .env 配置

### 2.1 为什么需要 .env

Python 程序需要读取：

- API Key；
- OpenAI-compatible 服务的 Base URL；
- 模型名称。

这些内容不应该硬编码到 Python 源码中，也不应该提交到 Git。

在 C:\text\python\learning4\.env 中使用类似配置：

~~~dotenv
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=https://你的兼容接口/v1
OPENAI_MODEL=你的模型名称
~~~

### 2.2 读取 .env

使用 python-dotenv：

~~~python
import os
from pathlib import Path

from dotenv import load_dotenv


ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(str(ENV_FILE))
~~~

构造客户端：

~~~python
from openai import OpenAI


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
~~~

### 2.3 遇到的模型参数问题

最初代码中出现过：

~~~python
model = os.getenv("OPENAI_MODEL"),
~~~

结尾的逗号会让 Python 把它变成元组：

~~~python
("模型名称",)
~~~

所以接口报错：

~~~text
The model parameter requires string type
~~~

正确写法：

~~~python
model = os.getenv("OPENAI_MODEL", "").strip()
~~~

这是一个重要的 Python 细节：

> 单元素元组通常是由结尾逗号决定的，而不是由括号决定的。

---

## 3. 第一部分：工具函数

### 3.1 当前时间工具

~~~python
from datetime import datetime


def local_get_current_time():
    now = datetime.now().astimezone()

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
    }
~~~

这个工具的特点：

- 不需要参数；
- 返回结构化字典；
- 用户询问当前时间时不能让模型自行猜测；
- 必须由 Python 工具返回真实时间。

### 3.2 模拟产品数据

~~~python
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
~~~

### 3.3 产品资料工具

~~~python
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
~~~

这里暂时没有连接真实数据库，目的是先理解 Agent 的工具调用链路。

---

## 4. 第二部分：工具定义 TOOL_DEFINITIONS

### 4.1 工具定义的职责

工具定义不是执行工具的代码，而是发送给模型的描述。

它告诉模型：

- 有什么工具；
- 工具什么时候使用；
- 工具需要哪些参数；
- 参数类型是什么；
- 参数有哪些可选值；
- 是否允许额外参数。

当前时间工具定义：

~~~python
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
    }
]
~~~

产品工具定义：

~~~python
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
}
~~~

### 4.2 additionalProperties: false

它表示：

> 参数对象中不能出现定义之外的字段。

合法参数：

~~~json
{
  "product_id": "P1001",
  "file_type": "document",
  "category": "troubleshooting"
}
~~~

非法参数：

~~~json
{
  "product_id": "P1001",
  "file_type": "document",
  "category": "troubleshooting",
  "random_field": "不应该出现"
}
~~~

它可以减少模型生成额外参数，也能帮助参数校验保持严格。

但是，不能只依赖模型端的 Schema。模型生成的参数仍然需要 Python 在本地再次校验。

---

## 5. 第三部分：工具注册表 TOOL_REGISTRY

### 5.1 注册表

~~~python
TOOL_REGISTRY = {
    "local_get_current_time": local_get_current_time,
    "local_get_product_info": local_get_product_info,
}
~~~

注册表的职责是：

~~~text
工具名称 → Python 函数
~~~

模型只会返回字符串名称，例如：

~~~text
local_get_product_info
~~~

Python 通过注册表找到真正要执行的函数。

### 5.2 未注册工具问题

曾经测试：

~~~python
tool_name = "local_get_product_info"
~~~

但是当 TOOL_REGISTRY 中没有这个名称时，输出：

~~~text
未知工具：local_get_product_info
~~~

原因不是模型不会调用，而是执行层找不到对应函数。

这个问题说明：

~~~text
TOOL_DEFINITIONS：模型可以看到什么
TOOL_REGISTRY：Python 实际可以执行什么
~~~

两者应该保持一致。

---

## 6. 第四部分：工具执行器

### 6.1 最初的直接执行方式

最初可以这样执行：

~~~python
tool_function = TOOL_REGISTRY.get(tool_name)

if tool_function is None:
    print(f"未知工具：{tool_name}")
    return

result = tool_function()
~~~

这种方式适合学习注册表，但还缺少：

- 参数校验；
- 异常捕获；
- 统一成功和失败结果；
- 给模型使用的 JSON 内容。

### 6.2 最终执行器结构

~~~python
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
~~~

执行器的责任是：

1. 根据名称查找函数；
2. 判断工具是否存在；
3. 校验参数；
4. 执行函数；
5. 捕获异常；
6. 返回统一结构。

---

## 7. 第五部分：统一 ToolResult

### 7.1 为什么需要统一结果

不同工具原本可能返回不同格式：

~~~python
{"date": "2026-10-23"}
~~~

~~~python
{"product_name": "智能空气净化器 X1"}
~~~

~~~python
"https://example.com/file"
~~~

如果工具异常，可能又直接抛出异常。

如果没有统一结果，Agent 主循环就需要为每个工具写特殊处理，复杂度会增加。

统一结果后，所有工具都变成：

~~~python
ToolResult(
    ok=True,
    data=工具返回值,
    error=None,
)
~~~

或者：

~~~python
ToolResult(
    ok=False,
    data=None,
    error="错误信息",
)
~~~

### 7.2 结构定义

~~~python
from dataclasses import dataclass
from typing import Any


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
~~~

### 7.3 面试理解

统一结果的价值是：

> 工具执行层负责把各种函数的输出转换成统一协议，Agent 主循环不需要知道每个工具内部的细节。

---

## 8. 第六部分：工具参数校验

### 8.1 为什么不能直接信任模型参数

模型生成的参数可能存在：

- 缺少必填字段；
- 枚举值错误；
- 多余字段；
- 类型错误；
- 产品编号不存在；
- 参数格式虽然合法，但业务上不允许。

因此：

~~~text
模型端 Schema 校验
      +
Python 执行前再次校验
~~~

### 8.2 实际验证过的错误

执行：

~~~powershell
python -c "from lesson1_tool_registry import execute_tool; print(execute_tool('local_get_product_info', {'product_id': 'P1001', 'file_type': 'document', 'category': 'unknown'}))"
~~~

得到：

~~~text
ToolResult(ok=False, data=None, error="ValueError: 参数 category 的值必须是：['introduction', 'tutorial', 'notes', 'troubleshooting']")
~~~

这说明错误没有让整个 Agent 直接崩溃，而是被转换成了统一失败结果。

### 8.3 参数校验的安全意义

不能因为模型是大模型，就把它当作可信后端。

工具可能涉及：

- 数据库查询；
- 文件访问；
- 发送消息；
- 退款；
- 删除数据；
- 外部 API 请求。

模型只负责提出意图，Python 执行层负责验证权限和参数。

---

## 9. 第七部分：解析模型的 tool_call

### 9.1 普通聊天和 Function Calling 的区别

普通聊天：

~~~text
用户问题 → 模型文本回答
~~~

Function Calling：

~~~text
用户问题 → 模型决定是否调用工具
         → 模型返回工具名称和 JSON 参数
         → Python 执行工具
         → Python 返回工具结果
         → 模型生成最终答案
~~~

### 9.2 模型原始返回

时间查询时曾经得到：

~~~json
{
  "content": "",
  "role": "assistant",
  "tool_calls": [
    {
      "id": "call_xxx",
      "function": {
        "arguments": "{}",
        "name": "local_get_current_time"
      },
      "type": "function"
    }
  ]
}
~~~

解析：

~~~python
tool_call = assistant_message.tool_calls[0]

tool_name = tool_call.function.name
tool_arguments = json.loads(
    tool_call.function.arguments
)
~~~

结果：

~~~text
工具名称： local_get_current_time
工具参数： {}
~~~

产品查询时：

~~~text
工具名称： local_get_product_info
工具参数： {
    'category': 'troubleshooting',
    'file_type': 'document',
    'product_id': 'P1001'
}
~~~

---

## 10. 第八部分：assistant 消息和 tool 消息

### 10.1 为什么要保存 assistant 的工具调用

模型返回工具调用后，不能只把结果直接发回模型。

必须保留模型刚才的调用意图：

~~~text
assistant：我调用了 local_get_product_info
tool：工具返回了产品故障排查信息
~~~

辅助函数：

~~~python
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
~~~

### 10.2 添加工具结果消息

~~~python
messages.append(
    build_assistant_tool_message(assistant_message)
)

messages.append(
    {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": tool_result.to_message_content(),
    }
)
~~~

其中 tool_call_id 很重要，它把工具结果和具体调用对应起来。

如果一次返回两个工具调用，就需要追加两个对应的 tool 消息。

### 10.3 不添加 tool 消息会怎样

模型看不到工具结果，可能：

- 无法生成正确答案；
- 重复调用工具；
- 丢失工具调用上下文；
- 在兼容 API 中直接触发消息协议错误。

这不等于一定会死循环，但会破坏 Agent 的消息协议。

---

## 11. 第九部分：Agent 循环和最大工具轮数

### 11.1 Agent 与普通工作流的区别

工作流通常是开发者提前决定：

~~~text
先执行 A
再执行 B
最后执行 C
~~~

Agent 的下一步由模型根据当前上下文决定：

~~~text
模型判断当前是否需要工具
模型决定调用哪个工具
工具执行后，模型再次判断下一步
~~~

### 11.2 主循环

核心结构：

~~~python
for round_number in range(1, MAX_TOOL_ROUNDS + 1):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOL_DEFINITIONS,
        tool_choice="auto",
        parallel_tool_calls=True,
    )

    assistant_message = response.choices[0].message

    if not assistant_message.tool_calls:
        print(assistant_message.content)
        return

    messages.append(
        build_assistant_tool_message(assistant_message)
    )

    # 执行当前轮工具，并把结果追加回 messages
~~~

### 11.3 为什么需要最大轮数

模型可能出现：

- 不断重复调用同一个工具；
- 工具返回错误后反复重试；
- 工具结果无法满足模型要求；
- 工具和模型之间形成循环。

例如：

~~~text
模型 → 工具 A
工具 A → 模型
模型 → 工具 A
工具 A → 模型
~~~

设置最大轮数，例如：

~~~python
MAX_TOOL_ROUNDS = 3
~~~

超过限制时：

~~~python
raise RuntimeError(
    f"达到最大工具轮数：{MAX_TOOL_ROUNDS}"
)
~~~

已经理解：

> 最大轮数是 Agent 的安全边界，可以避免死循环和无限消耗 Token。

---

## 12. 第十部分：多工具调用

### 12.1 同一轮返回多个工具

测试问题：

~~~text
请同时告诉我当前时间，并查询产品 P1001 的故障排查文档
~~~

第一轮模型返回两个调用：

~~~text
local_get_current_time
local_get_product_info
~~~

日志：

~~~text
model.response round=1 tool_calls=2
~~~

### 12.2 parallel_tool_calls=True 的含义

~~~python
parallel_tool_calls=True
~~~

表示：

> 允许模型在同一轮返回多个工具调用。

它不表示：

- 模型一定会返回多个工具；
- Python 一定会并行执行；
- 所有工具之间都没有依赖。

### 12.3 asyncio.gather() 的含义

~~~python
return await asyncio.gather(
    *(
        execute_one(tool_call)
        for tool_call in tool_calls
    )
)
~~~

它负责在 Python 侧并发调度多个异步任务。

因为当前工具函数是同步函数，所以使用：

~~~python
tool_result = await asyncio.to_thread(
    execute_tool,
    tool_name,
    tool_arguments,
)
~~~

完整关系：

~~~text
parallel_tool_calls=True
    模型层：允许返回多个调用

asyncio.gather()
    Python 层：并发执行多个任务

asyncio.to_thread()
    把同步工具函数放到线程中，避免阻塞事件循环
~~~

### 12.4 同一轮和不同轮

独立工具：

~~~text
第一轮模型：返回 A、B
Python：并行执行 A、B
第二轮模型：生成最终回答
~~~

存在依赖时，不能简单把所有工具一起并行。

不过，依赖调度不是第四阶段的核心实现目标。当前 Agent 使用模型多轮上下文来处理依赖：

~~~text
第一轮：模型调用前置工具
第二轮：模型看到前置结果后，调用后置工具
第三轮：生成最终回答
~~~

依赖感知调度器只是后续可以扩展的架构能力，本阶段没有实现。

---

## 13. 第十一部分：日志和调试

### 13.1 基础日志配置

~~~python
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("agent")
~~~

日志记录了：

- Agent 开始；
- 模型请求；
- 模型返回；
- 工具执行完成；
- Agent 结束。

### 13.2 工具耗时日志

~~~python
start_time = time.perf_counter()

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
~~~

### 13.3 遇到的 start_time 错误

最初使用了：

~~~python
time.perf_counter() - start_time
~~~

但是没有在执行前定义 start_time，所以出现：

~~~text
NameError: name 'start_time' is not defined
~~~

修复方式是把下面这句放到每个 execute_one() 内部：

~~~python
start_time = time.perf_counter()
~~~

必须每个工具单独记录开始时间，不能把所有工具共用一个开始时间。

### 13.4 遇到的重复日志问题

第一次并行测试时出现四条日志：

~~~text
tool.done current_time
tool.done product_info
tool.done current_time
tool.done product_info
~~~

通过在日志中加入 tool_call.id，确认相同调用 ID 被执行了两次。

最终定位到外层还有一个循环：

~~~python
for tool_call in assistant_message.tool_calls:
    tool_results = asyncio.run(
        execute_tool_calls_parallel(
            assistant_message.tool_calls
        )
    )
~~~

当列表中有两个工具时：

~~~text
外层循环第 1 次 → 执行完整工具列表 A、B
外层循环第 2 次 → 再次执行完整工具列表 A、B
~~~

所以 A、B 各执行两次。

正确写法：

~~~python
tool_results = asyncio.run(
    execute_tool_calls_parallel(
        assistant_message.tool_calls
    )
)
~~~

删除外层 for tool_call。

这个问题说明：

> 并行执行器内部已经负责遍历工具，外层不能再次对完整工具列表循环调用它。

---

## 14. 最终验证结果

修复后运行：

~~~powershell
PS C:\text\python\learning4> python .\lesson1_tool_registry.py
~~~

关键日志：

~~~text
model.response round=1 tool_calls=2
tool.done id=... name=local_get_current_time ok=True duration_ms=0.35
tool.done id=... name=local_get_product_info ok=True duration_ms=0.13
model.request round=2
model.response round=2 tool_calls=0
agent.finish
~~~

这证明：

1. 模型第一轮返回了两个工具调用；
2. 每个工具只执行了一次；
3. 工具结果成功追加回消息列表；
4. 第二轮模型没有继续调用工具；
5. 模型生成了最终客服回答；
6. Agent 正常结束。

---

## 15. 与 NestJS tools.service.ts 的对比

Node 文件：

~~~text
C:\text\ai-customer-service\src\ai\tools.service.ts
~~~

### 15.1 工具定义

NestJS 中：

~~~typescript
private readonly toolDefinitions = [
  // function definitions
];

getDefinitions() {
  return this.toolDefinitions;
}
~~~

Python 中：

~~~python
TOOL_DEFINITIONS = [
    # function definitions
]
~~~

概念相同，都是提供给模型的工具 Schema。

### 15.2 工具分发

NestJS 中使用 switch：

~~~typescript
switch (name) {
  case 'local_get_current_time':
    // execute
    break;
  case 'local_get_product_info':
    // execute
    break;
  default:
    return { error: '未知工具：' + name };
}
~~~

Python 中使用注册表：

~~~python
TOOL_REGISTRY = {
    "local_get_current_time": local_get_current_time,
    "local_get_product_info": local_get_product_info,
}
~~~

Python 版本用字典映射替代了较长的 switch。

### 15.3 产品资料查询

NestJS 中：

~~~typescript
this.knowledgeService.searchKnowledge(
  args.productId,
  args.category,
  args.fileType,
);
~~~

这是真实知识服务调用。

Python 当前版本：

~~~python
local_get_product_info(
    product_id,
    file_type,
    category,
)
~~~

使用的是 MOCK_PRODUCTS 模拟数据，尚未接入真实知识库。

### 15.4 文件 URL 工具

NestJS 中：

~~~typescript
this.ossService.generatePresignedUrl(args.filePath);
~~~

Python 的 local_get_url 按学习过程中的决定跳过，所以这一部分没有完成 Python 实现。

### 15.5 Python 版本额外实现的部分

相较于当前 NestJS 服务，Python 学习版本额外显式实现了：

- 工具注册表；
- ToolResult；
- 参数校验；
- 最大工具轮数；
- 多工具调用；
- asyncio.to_thread()；
- asyncio.gather()；
- 工具耗时日志；
- 调用 ID 调试。

这不是复制 Node 代码，而是使用 Python 的方式重新理解相同的 Agent 机制。

---

## 16. 本阶段遇到的问题和解决过程

### 问题 1：是否需要重新写文件

结论：不需要。直接在同一个 lesson1_tool_registry.py 中逐步扩展即可。

### 问题 2：工具没有注册

现象：

~~~text
未知工具：local_get_product_info
~~~

原因：工具名没有加入 TOOL_REGISTRY。

解决：

~~~python
TOOL_REGISTRY["local_get_product_info"] = local_get_product_info
~~~

### 问题 3：没有 API Key 和 Base URL

解决：使用 .env，通过 python-dotenv 读取：

~~~dotenv
OPENAI_API_KEY=...
OPENAI_BASE_URL=...
OPENAI_MODEL=...
~~~

### 问题 4：模型参数类型错误

原因：

~~~python
model = os.getenv("OPENAI_MODEL"),
~~~

尾部逗号导致字符串变成元组。

### 问题 5：模型没有调用工具

测试内容是让模型介绍自己，不涉及当前时间或产品资料。

模型没有调用工具是正确行为。

Function Calling 不是每次都必须调用工具，而是：

~~~text
模型根据用户意图决定是否需要工具
~~~

### 问题 6：模型成功返回 tool_call，但没有最终回答

原因：只执行了工具，没有把结果以 role="tool" 消息返回给模型。

解决：追加 assistant 工具调用消息和 tool 结果消息，然后再次调用模型。

### 问题 7：参数校验失败

传入未知枚举值：

~~~text
category = unknown
~~~

执行器返回：

~~~text
ToolResult(ok=False, error=...)
~~~

说明异常被统一处理，而不是让程序直接崩溃。

### 问题 8：达到最大工具轮数

最大轮数的作用是防止模型和工具无限循环，并控制 Token 消耗。

### 问题 9：parallel_tool_calls 是否等于实际并行

不等于。

~~~text
parallel_tool_calls=True
    模型允许返回多个工具调用

asyncio.gather()
    Python 并发执行多个工具任务
~~~

### 问题 10：start_time 未定义

原因：记录耗时前没有初始化计时器。

解决：

~~~python
start_time = time.perf_counter()
~~~

### 问题 11：工具重复执行

原因：外层 for tool_call 循环中重复调用了已经会遍历全部工具的并行执行器。

解决：删除外层循环，只调用一次：

~~~python
tool_results = asyncio.run(
    execute_tool_calls_parallel(
        assistant_message.tool_calls
    )
)
~~~

---

## 17. 工具依赖调度：讨论过，但没有纳入本阶段实现

这个问题是学习过程中临时讨论的架构扩展，不是当前阶段的必做内容。

### 17.1 依赖示例

~~~text
A：查询订单状态
B：根据订单状态判断退款
C：查询当前时间
~~~

依赖关系：

~~~text
B 依赖 A
C 不依赖其他工具
~~~

理论上可以：

~~~text
第一批：A、C 并行
第二批：B
~~~

### 17.2 重要结论

标准 Function Calling 的 tool_call 通常只有：

~~~text
id
name
arguments
~~~

它没有标准的：

~~~text
depends_on
~~~

即使自己在工具定义中增加 depends_on，API 或模型也不会自动帮忙调度。

如果要做严格的依赖调度，需要自己实现：

- 工具依赖契约；
- 调用计划；
- depends_on；
- 参数引用解析；
- 就绪工具筛选；
- 循环依赖检测；
- 分批执行。

### 17.3 当前阶段采用的简单思路

当前阶段不实现依赖调度器，使用 Agent 多轮机制理解依赖：

~~~text
第一轮模型：调用前置工具
Python：执行并返回 tool 结果
第二轮模型：根据结果生成后置工具调用
~~~

这已经能够说明：

~~~text
独立工具可以同轮并行
依赖工具通过下一轮模型调用顺序执行
~~~

依赖感知调度器适合后续工程化阶段再实现。

---

## 18. 当前阶段真正掌握的内容

通过实际运行和排查，已经掌握：

1. Function Calling 与普通聊天的区别；
2. TOOL_DEFINITIONS 的职责；
3. TOOL_REGISTRY 的职责；
4. 单个工具的执行流程；
5. 参数解析；
6. 参数校验；
7. ToolResult；
8. assistant tool-call 消息；
9. tool 结果消息；
10. Agent 多轮循环；
11. 最大工具轮数；
12. 工具异常处理；
13. 同一轮多工具调用；
14. parallel_tool_calls 和真正并发执行的区别；
15. asyncio.to_thread()；
16. asyncio.gather()；
17. 日志和耗时统计；
18. 通过日志定位重复执行问题；
19. Python .env 和 OpenAI 客户端配置；
20. Python 与 NestJS 工具服务的架构映射。

---

## 19. 面试官可能会问什么

### Function Calling 相关

1. Function Calling 和普通聊天有什么区别？
2. 模型返回 tool_call 后，为什么还要再次调用模型？
3. TOOL_DEFINITIONS 和 TOOL_REGISTRY 有什么区别？
4. 为什么工具结果要使用 role="tool"？
5. tool_call_id 的作用是什么？

### Agent 相关

1. Agent 和固定工作流有什么区别？
2. 为什么需要最大工具轮数？
3. 如果工具一直失败，Agent 怎么避免无限循环？
4. 模型是否可以直接执行 Python 函数？
5. 为什么必须由 Python 执行工具，而不是相信模型返回的文本？

### 安全和可靠性

1. 为什么要在 Python 侧再次校验参数？
2. additionalProperties: false 有什么作用？
3. 如何处理未知工具？
4. 工具执行异常如何返回给模型？
5. 如何防止模型传入非法枚举值？

### 并行调用

1. parallel_tool_calls=True 是否代表工具已经并行执行？
2. asyncio.gather() 负责什么？
3. 为什么同步函数还需要 asyncio.to_thread()？
4. 两个工具互相依赖时还能并行吗？
5. 如何定位工具被重复执行？

### 本阶段真实调试案例

可以这样回答重复执行问题：

> 我通过 tool_call.id 和工具耗时日志发现同一组调用被记录了两次。进一步检查执行路径后发现，外层 for 循环重复调用了本身已经遍历全部工具的并行执行函数。删除外层循环后，每个工具只执行一次。

---

## 20. 当前可以写进简历的内容

如果这些代码确实由自己完成并且能够解释，可以写在个人项目或学习项目中：

> 使用 Python 和 OpenAI-compatible SDK 独立实现无 LangChain 的 Function Calling Agent，支持工具注册、参数校验、统一工具结果、异常处理、最大工具轮次控制、多工具调用、独立工具并发执行和日志追踪。

也可以具体写：

> 使用 asyncio.to_thread() 和 asyncio.gather() 并发执行同一轮中互不依赖的同步工具函数。

注意当前真实边界：

- 产品数据仍然是模拟数据；
- local_get_url 没有实现；
- 依赖感知调度器没有实现；
- 当前不是生产级 Agent 服务。

---

## 21. 当前暂时不能写进简历的内容

当前 Python 阶段暂时不能声称已经完成：

- Python LangChain Agent；
- Python MCP；
- Python RAG；
- Python Qdrant；
- Python Redis；
- Python PostgreSQL；
- Python 真实知识库检索；
- Python local_get_url；
- 依赖感知执行计划和拓扑调度；
- 生产级重试、熔断、权限和分布式调度。

Node/NestJS 项目中已经存在的能力，不能自动算作 Python 阶段已经完成的能力。

---

## 22. 阶段结论和下一阶段

### 本阶段结论

第四阶段的核心目标已经完成：

~~~text
用户问题
→ 模型判断是否调用工具
→ 返回 tool_call
→ Python 解析工具
→ 注册表查找函数
→ 参数校验
→ 执行工具
→ 生成统一 ToolResult
→ 追加 tool 消息
→ 多轮循环
→ 最终回答
~~~

local_get_url 是按学习过程主动跳过的，不影响核心 Function Calling Agent 的完成。

### 下一阶段方向

下一阶段进入手写最小 RAG：

~~~text
本地产品文档
→ 文本切分
→ 文本检索
→ 返回相关内容
→ 封装成检索工具
→ 让 Agent 调用检索工具
~~~

下一阶段仍然不先使用 LangChain，也不一开始连接 Qdrant，而是先理解：

- RAG 与 Function Calling 的区别；
- 文档为什么需要切分；
- 检索结果如何进入模型上下文；
- 如何把检索封装成一个 Python 工具；
- 如何把 RAG 工具接入当前 Agent。

---

## 23. 当前文件和运行命令

主文件：

~~~text
C:\text\python\learning4\lesson1_tool_registry.py
~~~

运行：

~~~powershell
cd C:\text\python\learning4
python .\lesson1_tool_registry.py
~~~

当前阶段学习文档：

~~~text
C:\text\python\learning4\phase4_function_calling_agent_notes.md
~~~

