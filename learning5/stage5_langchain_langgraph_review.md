
# 第五阶段复盘：LangChain 与 LangGraph

> 目标：把已经手写过的 Agent 循环映射到 LangChain 和 LangGraph，理解框架替我们封装了什么、什么时候该用、什么时候不该用，并能在面试中讲清楚状态如何流转。
>
> 本文对应项目目录：`C:\text\python\learning5`

---

## 0. 先记住这一阶段最重要的一句话

LangChain 和 LangGraph 都不是模型。

- 模型负责理解问题、生成回答、决定是否请求工具。
- Python 函数负责真正查询数据库、调用 API、执行业务操作。
- LangChain 提供模型、消息、工具和 Agent 的封装。
- LangGraph 提供有状态的流程编排、分支、循环、暂停、恢复和持久化。
- FastAPI 负责把 Agent 暴露成 HTTP 服务。

整体关系：

```text
前端 / 其他服务
        ↓ HTTP / SSE
FastAPI
        ↓
Agent Service
        ↓
LangChain / LangGraph
        ↓
模型、工具、RAG、数据库、业务 API
```

LangGraph 不是 FastAPI 的替代品，也不是数据库的替代品，更不是模型本身。

---

## 1. 什么时候用原生 OpenAI SDK、LangChain 和 LangGraph

### 1.1 原生 OpenAI SDK

原生 Agent 的核心逻辑通常是：

```python
while True:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
    )

    assistant_message = response.choices[0].message
    messages.append(assistant_message)

    if not assistant_message.tool_calls:
        break

    for tool_call in assistant_message.tool_calls:
        result = execute_tool(tool_call)
        messages.append(result)
```

适合：

- 工具数量少；
- 流程简单；
- 需要完全控制底层请求和消息格式；
- 想精确调试 Function Calling；
- 不希望引入较重的框架。

优点：

- 依赖少；
- 行为透明；
- 容易和现有 NestJS、Node.js 服务融合；
- 便于自己设计消息持久化和业务流程。

缺点：

- 工具注册、参数校验、工具分发、循环、错误处理、重试、暂停恢复都要自己实现；
- 复杂后容易形成很长的 Agent 循环代码。

### 1.2 LangChain Agent

适合：

- 工具数量比较多；
- 基本流程仍然是“模型决定工具 → 执行工具 → 再次调用模型”；
- 不需要自己精细控制每一条流程边；
- 希望快速组合模型、工具和消息。

```text
用户消息
   ↓
模型
   ↓
有工具调用？
   ├─ 是 → 执行工具 → 再次调用模型
   └─ 否 → 返回回答
```

LangChain 的 `create_agent` 会替你封装这套循环。

### 1.3 LangGraph

适合：

- 多个明确的业务步骤；
- 条件分支；
- 多轮循环；
- 重试；
- 错误兜底；
- 人工审批；
- 中断后恢复；
- 需要保存流程状态；
- 希望每个节点都可以单独测试和观察。

例如退款流程：

```text
查询订单
   ↓
判断是否满足退款条件
   ↓
检查风险
   ↓
高风险？ ── 是 → 人工审批 → 恢复流程
   │
   否
   ↓
执行退款
   ↓
通知用户
```

### 1.4 三者对比

| 方案 | 主要职责 | 适合场景 | 你需要自己控制的部分 |
|---|---|---|---|
| 原生 OpenAI SDK | 最底层模型和工具调用 | 简单 Agent、底层控制 | 几乎全部 Agent 循环 |
| LangChain Agent | 封装常见 Agent 循环 | 工具多但流程简单 | 主要是工具和提示词 |
| LangGraph | 编排有状态流程 | 复杂业务流程、暂停、恢复 | 节点和边的设计 |

当前 LangChain 的 `create_agent` 底层也是基于 LangGraph 构建的。区别是：LangChain Agent 隐藏了很多图结构，而 LangGraph 让你显式描述流程。

---

## 2. 当前环境和依赖

### 2.1 Python 环境

本阶段实际验证使用：

- Python：3.14.8
- 虚拟环境：`.venv314`
- 工作目录：`C:\text\python\learning5`

已验证依赖：

| 包 | 版本 | 作用 |
|---|---:|---|
| `langchain-core` | 1.7.0 | 消息、工具、模型抽象等核心能力 |
| `langchain-openai` | 1.7.2 | `ChatOpenAI` 模型适配器 |
| `langchain` | 1.4.7 | 高层 Agent API，例如 `create_agent` |
| `langgraph` | 1.2.16 | State、Node、Edge、Checkpoint、Interrupt |
| `python-dotenv` | 1.2.4 | 从 `.env` 加载环境变量 |

### 2.2 创建虚拟环境

```powershell
py -3.14 -m venv .venv314
```

激活：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv314\Scripts\Activate.ps1
```

验证：

```powershell
python --version
python -c "import langchain_core; print(langchain_core.__version__)"
```

运行脚本时优先使用当前虚拟环境中的 `python`：

```powershell
python .\lesson_05_06.py
```

也可以不激活，直接使用绝对路径：

```powershell
.\.venv314\Scripts\python.exe .\lesson_05_06.py
```

### 2.3 安装依赖

重新创建环境时使用已经验证过的版本：

```powershell
python -m pip install "langchain-core==1.7.0" "langchain-openai==1.7.2" "langchain==1.4.7" "langgraph==1.2.16" "python-dotenv==1.2.4"
```

---

## 3. 阿里云百炼和 ChatOpenAI

你使用的是阿里云百炼，不是官方 OpenAI 服务。

百炼提供 OpenAI-compatible 接口，因此可以使用 LangChain 的 `ChatOpenAI` 适配器，但必须配置百炼的 `base_url`。

### 3.1 `.env`

不要把真实 API Key 直接写入 Python 文件，也不要提交到 Git。

```dotenv
OPENAI_API_KEY=你的百炼API密钥
OPENAI_MODEL=你的百炼模型名称
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 3.2 Python 读取配置

```python
import os
from dotenv import load_dotenv

load_dotenv()

model_name = os.environ["OPENAI_MODEL"]
api_key = os.environ["OPENAI_API_KEY"]
base_url = os.environ["OPENAI_BASE_URL"]
```

实例化：

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
)
```

`ChatOpenAI` 这个类名表示它使用 OpenAI-compatible Chat API 协议，不代表只能连接官方 OpenAI。

---

## 4. 本阶段的原生 Agent 到框架映射

| 手写 Agent | LangChain / LangGraph |
|---|---|
| `client.chat.completions.create(...)` | `model.invoke(messages)` |
| OpenAI messages 字典 | `HumanMessage`、`AIMessage`、`ToolMessage` |
| Python 函数 | LangChain Tool |
| 手动工具 Schema | `@tool` 根据函数生成 Schema |
| `tools` 配置 | `model.bind_tools(tools)` |
| 判断 `tool_calls` | 条件边 `add_conditional_edges` |
| 手动执行工具 | `ToolNode` 或自定义 Node |
| `while` 循环 | `tools -> call_model` 的图边 |
| 手动保存 messages | Checkpoint 或自己的数据库 |
| 人工暂停和恢复 | `interrupt()` + `Command(resume=...)` |

最重要的对应关系：

```text
model_with_tools.invoke()
        ↓
只调用模型，模型返回 AIMessage
        ↓
AIMessage.tool_calls
        ↓
ToolNode 执行 Python 函数
        ↓
生成 ToolMessage
        ↓
回到模型
```

---

## 5. LangChain 的 Model、Message、Tool

### 5.1 `langchain_core` 是什么

`langchain_core` 提供不绑定具体模型供应商的基础抽象：

- Message；
- Tool；
- Runnable；
- Chat Model 接口；
- 输入和输出格式。

它不是某个具体模型服务。

### 5.2 `langchain_openai` 是什么

`langchain_openai` 提供 OpenAI-compatible 模型适配器：

```python
from langchain_openai import ChatOpenAI
```

它把统一的 LangChain 调用方式转换成模型供应商能够理解的 HTTP 请求。

### 5.3 Message 类型

#### `HumanMessage`

表示用户消息：

```python
from langchain_core.messages import HumanMessage

message = HumanMessage(
    content="我的订单还没有发货，可以退款吗？"
)
```

#### `SystemMessage`

表示系统指令：

```python
from langchain_core.messages import SystemMessage

message = SystemMessage(
    content="你是一个专业的 AI 客服。"
)
```

#### `AIMessage`

表示模型消息：

```python
from langchain_core.messages import AIMessage

message = AIMessage(content="未发货订单可以申请退款。")
```

如果模型决定调用工具，`AIMessage.content` 可能为空，但 `AIMessage.tool_calls` 有内容：

```python
AIMessage(
    content="",
    tool_calls=[
        {
            "name": "search_faq",
            "args": {"question": "未发货订单可以退款吗？"},
            "id": "call_1",
            "type": "tool_call",
        }
    ],
)
```

#### `ToolMessage`

表示工具执行结果：

```python
from langchain_core.messages import ToolMessage

ToolMessage(
    content="退款规则：未发货订单可以申请退款。",
    tool_call_id="call_1",
)
```

`tool_call_id` 必须和模型发出的工具调用 ID 对应，这样模型才能知道这个结果属于哪一次工具调用。

### 5.4 `FakeMessagesListChatModel`

```python
from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
```

它是测试模型，不访问真实 API，也不消耗 API 额度。可以预先定义模型每次返回什么。

适合：

- 测试消息流转；
- 测试工具调用逻辑；
- 测试 Agent 循环；
- 避免测试时每次调用真实模型。

对应文件：

`lesson_05_01.py`

---

## 6. `@tool`：把 Python 函数包装成工具

代码：

```python
from langchain_core.tools import tool

@tool
def search_faq(question: str) -> str:
    """查询客服知识库中的常见问题。"""
    return "退款规则：未发货订单可以申请退款。"
```

这段代码做了两件事：

1. 在函数定义阶段，把普通 Python 函数包装成 LangChain 的 `StructuredTool`；
2. 根据函数名、文档字符串、类型提示生成工具描述和参数 Schema。

可以查看：

```python
print(search_faq.name)
print(search_faq.description)
print(search_faq.args)
```

可能得到：

```text
名称: search_faq
描述: 查询客服知识库中的常见问题。
参数: {
    "question": {
        "title": "Question",
        "type": "string"
    }
}
```

### 6.1 文档字符串为什么重要

```python
@tool
def get_order_status(order_id: str) -> str:
    """查询订单当前状态。"""
    ...
```

模型会根据工具名称、描述和参数决定是否调用它。因此描述不能随便写。

不好的描述：

```python
"""工具。"""
```

更好的描述：

```python
"""查询指定订单的当前状态。只适用于用户明确提供订单号的情况。"""
```

### 6.2 `@tool` 不会立即执行函数体

```python
@tool
def search_faq(question: str) -> str:
    print("函数体执行了")
    return "..."
```

装饰器阶段只是创建工具对象，不会执行 `print` 和 `return`。

实际执行需要：

```python
search_faq.invoke({
    "question": "未发货订单可以退款吗？"
})
```

或者由 `ToolNode`、Agent 内部工具执行逻辑调用。

---

## 7. `bind_tools`：把工具 Schema 告诉模型

代码：

```python
model_with_tools = model.bind_tools([
    search_faq,
    get_order_status,
])
```

这一步不是执行工具，而是把工具的配置放进模型请求：

- 工具名称；
- 工具描述；
- 参数 Schema。

模型看到这些信息后，才知道自己可以选择哪些工具。

### 7.1 绑定后产生新对象

```python
print(type(model).__name__)
print(type(model_with_tools).__name__)
print(model is model_with_tools)
```

典型输出：

```text
ChatOpenAI
_ChatModelBinding
False
```

说明：

- 原来的 `model` 没有被修改；
- `model_with_tools` 是一个绑定了工具配置的新 Runnable；
- 原模型仍然可以单独使用。

### 7.2 `model_with_tools.invoke` 不会执行 Python 函数

```python
ai_message = model_with_tools.invoke(messages)
```

这只调用一轮模型。

结果可能是：

```python
AIMessage(
    content="",
    tool_calls=[...]
)
```

它表达的是：

> 我建议调用 search_faq，并传入这些参数。

模型不会直接运行你的 Python 函数。后端或框架必须根据 `tool_calls` 执行函数。

对应文件：

`lesson_05_02.py`

---

## 8. LangChain Agent：封装标准 Agent 循环

当前版本的基本写法：

```python
from langchain.agents import create_agent

agent = create_agent(
    model=model,
    tools=[search_faq],
    system_prompt=(
        "你是一个专业的 AI 客服，只能基于客服知识库回答问题。"
    ),
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "我的订单还没有发货，可以退款吗？",
            }
        ]
    }
)
```

Agent 内部大致完成：

```text
1. 接收用户消息
2. 调用模型
3. 检查是否有 tool_calls
4. 有则执行工具
5. 将 ToolMessage 加回 messages
6. 再次调用模型
7. 没有 tool_calls 时结束
```

查看消息：

```python
for index, message in enumerate(result["messages"]):
    print(index, type(message).__name__)
    print(message.content)

    if getattr(message, "tool_calls", None):
        print(message.tool_calls)
```

### 8.1 `getattr` 的含义

```python
getattr(message, "tool_calls", None)
```

表示：

> 如果 message 有 tool_calls 属性，就取它；如果没有，就返回 None。

这样可以同时安全检查 `HumanMessage`、`AIMessage` 和 `ToolMessage`。

### 8.2 Agent 不是模型

本阶段运行时：

```text
模型类型: ChatOpenAI
Agent 类型: CompiledStateGraph
```

说明：

- `ChatOpenAI` 是模型对象；
- `agent` 是封装了流程的可执行图；
- Agent 不是新的模型。

对应文件：

`lesson_05_03.py`

---

## 9. LangGraph 的核心心智模型

LangGraph 可以理解为：

```text
State  = 流程中携带的数据
Node   = 处理数据的 Python 函数
Edge   = 节点之间的执行关系
Graph  = 完整流程
```

### 9.1 State

`State` 是流程中各个节点共享的数据结构。

最常见的是：

```python
from langgraph.graph import MessagesState

state = {
    "messages": [...]
}
```

也可以增加业务字段：

```python
class CustomerServiceState(MessagesState):
    user_id: str
    retrieved_docs: list[str]
    retry_count: int
    order_id: str
```

State 可以保存：

- messages；
- 检索结果；
- 用户问题；
- 订单编号；
- 重试次数；
- 当前答案；
- 风险判断；
- 业务状态。

### 9.2 State 不等于所有上下文

需要区分：

| 概念 | 作用 |
|---|---|
| State | 当前流程的数据 |
| Runtime Context | 当前调用的运行上下文，例如 user_id |
| config.thread_id | 当前会话线程的标识 |
| Store | 跨会话的长期记忆 |
| Checkpoint | 某个线程的状态快照 |

`user_id` 可以放进 State，但也可以通过 Runtime Context 传入。`lesson_05_08.py` 使用的是 Context：

```python
from dataclasses import dataclass

@dataclass
class Context:
    user_id: str
```

图声明：

```python
builder = StateGraph(
    MessagesState,
    context_schema=Context,
)
```

调用时：

```python
result = graph.invoke(
    input_state,
    config,
    context=Context(user_id="U1001"),
)
```

Node 中读取：

```python
def call_model_node(
    state: MessagesState,
    runtime: Runtime[Context],
):
    user_id = runtime.context.user_id
```

### 9.3 Node

Node 就是一个处理 State 的 Python 函数：

```python
def reply_node(state: MessagesState):
    user_message = state["messages"][-1]

    return {
        "messages": [
            AIMessage(
                content=f"收到：{user_message.content}"
            )
        ]
    }
```

Node 的规则：

- 接收当前 State；
- 读取所需字段；
- 返回要更新的字段；
- 不一定要返回完整 State。

注册 Node：

```python
builder.add_node("reply", reply_node)
```

注册不会立即执行，只是把函数放入图定义。

### 9.4 Edge

普通边表示固定顺序：

```python
builder.add_edge(START, "reply")
builder.add_edge("reply", END)
```

表示：

```text
START → reply → END
```

### 9.5 Conditional Edge

条件边根据 State 决定下一步：

```python
def route_after_model(state: MessagesState):
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"
```

注册：

```python
builder.add_conditional_edges(
    "call_model",
    route_after_model,
    {
        "tools": "tools",
        "end": END,
    },
)
```

注意：

- 条件函数返回的是映射表中的 key；
- `tools` 会跳转到名为 `tools` 的 Node；
- `end` 会跳转到 `END`；
- 判断的是 `AIMessage.tool_calls`，不是 `ToolMessage`。

### 9.6 `compile` 和 `invoke`

```python
graph = builder.compile()
```

作用：

> 把 State、Node、Edge 和配置组合成可执行 Graph。

```python
result = graph.invoke(input_state)
```

作用：

> 传入一次输入，真正执行 Graph。

类比：

```text
builder  = 设计施工图
compile  = 构建可运行系统
invoke   = 发送一次请求
```

---

## 10. 用 LangGraph 实现完整 Agent 循环

对应文件：

`lesson_05_06.py`

核心结构：

```python
builder = StateGraph(MessagesState)
tool_node = ToolNode([search_faq])

builder.add_node("call_model", call_model_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "call_model")

builder.add_conditional_edges(
    "call_model",
    route_after_model,
    {
        "tools": "tools",
        "end": END,
    },
)

builder.add_edge("tools", "call_model")
```

完整流程：

```text
START
  ↓
call_model
  ↓
route_after_model
  ├── 有 tool_calls → tools
  │                    ↓
  │                 ToolMessage
  │                    ↓
  │                 call_model
  │
  └── 没有 tool_calls → END
```

### 10.1 模型 Node

```python
def call_model_node(state: MessagesState):
    ai_message = model_with_tools.invoke(
        state["messages"]
    )

    return {
        "messages": [ai_message]
    }
```

它对应原生 Agent 中：

```python
response = client.chat.completions.create(...)
```

但是它只调用一次模型。

### 10.2 ToolNode

```python
tool_node = ToolNode([search_faq])
builder.add_node("tools", tool_node)
```

`ToolNode` 的职责：

1. 读取最后一条 AIMessage 的 `tool_calls`；
2. 根据工具名称找到 Python 工具；
3. 传入模型生成的参数；
4. 执行工具函数；
5. 生成 ToolMessage；
6. 把结果写回 State 的 `messages`。

### 10.3 ToolNode 的常见错误

曾经单独执行：

```python
tool_node.invoke({
    "messages": [ai_message]
})
```

当前版本报错：

```text
ValueError: Missing required config key 'N/A' for 'tools'.
```

原因不是工具函数写错，而是当前版本的 `ToolNode` 依赖 Graph Runtime 注入的运行配置。正确用法是把它注册进 Graph，让 Graph 来执行：

```python
builder.add_node("tools", tool_node)
graph = builder.compile()
graph.invoke(...)
```

### 10.4 不要同时添加冲突的结束边

下面这种设计容易产生歧义：

```python
builder.add_edge("call_model", END)
builder.add_conditional_edges("call_model", ...)
```

Agent 循环应使用：

```text
call_model → conditional edge
```

而不是同时添加固定的 `call_model → END`。

---

## 11. MessagesState 和消息合并

`MessagesState` 不是普通的简单字典，它对 `messages` 使用了消息合并规则。

Node 返回：

```python
return {
    "messages": [ai_message]
}
```

并不是把整个历史替换成一条消息，而是把新消息追加到已有消息中。

结果：

```text
HumanMessage
AIMessage(tool_calls)
ToolMessage
AIMessage(final)
```

如果自己定义普通 State，要注意消息字段的 reducer；否则可能发生旧消息被覆盖的问题。

手动理解消息追加可以使用：

```python
from langgraph.graph import add_messages

state["messages"] = add_messages(
    state["messages"],
    [new_message],
)
```

对应文件：

`lesson_05_04.py`

---

## 12. State、Checkpoint、Store 的区别

### 12.1 State

State 是当前流程正在使用的数据：

```python
{
    "messages": [...],
    "retrieved_docs": [...],
    "retry_count": 1,
    "order_id": "A1001"
}
```

### 12.2 Checkpoint

Checkpoint 是某一时刻保存下来的 State 快照，同时包含恢复流程所需的执行信息：

- messages；
- 自定义 State 字段；
- 下一步节点；
- 当前执行位置；
- interrupt 信息；
- 恢复所需的元数据。

使用：

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {
    "configurable": {
        "thread_id": "session-U1001-001"
    }
}
```

读取：

```python
snapshot = graph.get_state(config)

print(snapshot.values)
print(snapshot.next)
```

其中：

- `snapshot.values`：当前保存的 State；
- `snapshot.next`：下一步待执行节点；
- `snapshot.next == ()`：流程已经结束。

`InMemorySaver` 只存在 Python 进程内存中，适合学习和测试。生产环境需要持久化 Checkpointer。

### 12.3 Store

Store 用于跨会话长期记忆：

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

store.put(
    ("U1001", "memories"),
    "preferred_channel",
    {
        "preferred_channel": "sms"
    },
)

memories = store.search(("U1001", "memories"))
```

概念：

- `user_id`：用户身份；
- `namespace`：记忆分类；
- `memory_id`：某条记忆的编号；
- `value`：记忆内容。

```text
thread_id = 哪一条会话线程
user_id   = 哪一个用户
Checkpoint = 这个线程的流程状态
Store      = 这个用户跨会话的长期记忆
```

### 12.4 长期记忆注入模型

`lesson_05_08.py` 的关键流程：

```text
Runtime Context 读取 user_id
        ↓
Store.search(namespace)
        ↓
得到用户偏好
        ↓
转换成 SystemMessage
        ↓
和当前 messages 一起传给模型
```

代码：

```python
memories = runtime.store.search(namespace)

memory_lines = []

for item in memories:
    for key, value in item.value.items():
        memory_lines.append(f"{key}: {value}")

memory_text = "\n".join(memory_lines)

system_message = SystemMessage(
    content=(
        "以下是用户的长期记忆，只有在问题相关时才使用："
        f"\n{memory_text}"
    )
)

model_messages = [
    system_message,
    *state["messages"],
]

ai_message = model_with_tools.invoke(model_messages)
```

注意：Store 不会自动判断什么应该成为长期记忆。业务代码需要在适当时机调用 `store.put`。

---

## 13. Checkpoint 到底是不是聊天数据库

不应该把 Checkpoint 简单理解成聊天记录数据库。

### 简单一次性流程

```text
请求
  ↓
模型
  ↓
工具
  ↓
最终回答
  ↓
结束
```

如果不需要：

- 多轮继续；
- 人工审批；
- 中断恢复；
- 失败续跑；
- 长流程状态；

可以不用 Checkpoint。

### 需要 Checkpoint 的流程

```text
订单查询
  ↓
风险判断
  ↓
人工审批 interrupt
  ↓
保存状态
  ↓
几分钟后恢复
  ↓
执行退款
```

这类流程必须保存当前 State 和执行位置。

### 生产系统的分工

| 数据 | 推荐位置 |
|---|---|
| 正式聊天记录 | PostgreSQL |
| 订单和退款业务数据 | PostgreSQL |
| Agent 当前执行状态 | Checkpoint |
| 人工审批暂停信息 | Checkpoint |
| 用户长期偏好 | Store 或用户画像表 |
| 缓存 | Redis |
| 向量文档 | Qdrant |

原生 OpenAI Chat Completions 不会自动替你保存整个会话。原生 Agent 通常需要：

```text
根据 session_id 查询历史消息
        ↓
加入本次用户消息
        ↓
调用模型
        ↓
追加 AIMessage、tool_call、ToolMessage
        ↓
保存回数据库
```

LangGraph Checkpoint 帮你管理的是 Agent 流程状态，不一定要取代正式业务数据库。

---

## 14. RetryPolicy：节点重试

对应文件：

`lesson_05_09.py`

代码：

```python
from langgraph.types import RetryPolicy

builder.add_node(
    "retrieve_faq",
    retrieve_faq_node,
    retry_policy=RetryPolicy(
        max_attempts=3,
        initial_interval=0.1,
        backoff_factor=1.0,
        jitter=False,
        retry_on=ConnectionError,
    ),
)
```

参数含义：

- `max_attempts=3`：总共最多执行 3 次，包含第一次；
- `initial_interval=0.1`：第一次失败后等待 0.1 秒；
- `backoff_factor=1.0`：后续等待时间的倍数；
- `jitter=False`：不加入随机延迟，便于学习；
- `retry_on=ConnectionError`：只对指定异常重试。

执行：

```text
第 1 次：失败
第 2 次：失败
第 3 次：成功
```

### 14.1 什么错误适合重试

适合：

- 网络暂时不可用；
- 请求超时；
- 临时连接失败；
- 服务限流。

不适合：

- 参数校验错误；
- 权限错误；
- 订单不存在；
- 退款重复提交；
- 明确的业务拒绝。

涉及真实退款、扣款、发货等副作用时，必须考虑幂等性，否则重试可能重复执行业务操作。

---

## 15. error_handler：重试失败后的兜底

对应文件：

`lesson_05_10.py`

```python
from langgraph.errors import NodeError

def faq_error_handler(
    state: FAQState,
    error: NodeError,
):
    print(f"失败的 Node: {error.node}")
    print(f"最终错误: {error.error}")

    return {
        "answer": "客服知识库暂时不可用，请稍后重试，或转人工客服。"
    }
```

Node 配置：

```python
builder.add_node(
    "retrieve_faq",
    retrieve_faq_node,
    retry_policy=RetryPolicy(
        max_attempts=3,
        retry_on=ConnectionError,
    ),
    error_handler=faq_error_handler,
)
```

执行顺序：

```text
第 1 次失败
  ↓
第 2 次重试失败
  ↓
第 3 次重试失败
  ↓
error_handler
  ↓
返回兜底 State
```

区别：

| 文件 | 行为 |
|---|---|
| `lesson_05_09.py` | 重试成功后返回；重试失败则抛出异常 |
| `lesson_05_10.py` | 重试失败后进入 error_handler，返回可用的兜底结果 |

---

## 16. Human-in-the-loop：人工介入

对应文件：

`lesson_05_11.py`

### 16.1 `interrupt()`

```python
from langgraph.types import interrupt

decision = interrupt(
    {
        "action": "refund",
        "order_id": state["order_id"],
        "message": "是否批准退款？",
    }
)
```

作用：

1. 暂停 Graph；
2. 保存当前 State；
3. 把审批信息返回给调用方；
4. 等待外部人工决定。

### 16.2 第一次执行

```python
result = graph.invoke(
    {
        "order_id": "A1001",
        "status": "waiting",
    },
    config,
)
```

结果中会有：

```python
result["__interrupt__"]
```

### 16.3 恢复执行

```python
from langgraph.types import Command

resumed_result = graph.invoke(
    Command(
        resume={
            "approved": True
        }
    ),
    config,
)
```

这里的 `approved` 不是 LangGraph 固定关键字，而是自己定义的业务字段。

也可以设计成：

```python
{"decision": "approve"}
{"decision": "reject"}
```

或者：

```python
{
    "operator_id": "admin-001",
    "approved": True,
}
```

Node 中读取：

```python
decision = interrupt(...)

if decision["approved"]:
    return Command(goto="execute_refund")

return Command(goto="cancel_refund")
```

### 16.4 为什么必须有 Checkpoint

恢复时需要知道：

- 哪个用户的哪个订单；
- 当前流程暂停在哪个节点；
- 审批之前 State 是什么；
- 恢复后该从哪里继续。

因此必须：

- 使用 Checkpointer；
- 使用同一个 `thread_id`；
- 恢复时传入 `Command(resume=...)`。

---

## 17. 本阶段踩过的坑和解决方法

### 17.1 Python 3.15 和 3.14

你最初安装了 Python 3.15，后来使用 Python 3.14.8 创建了 `.venv314`。

本阶段选择 3.14 的原因是：

- 让 LangChain、LangGraph 和相关依赖使用已验证的组合；
- 降低新版本 Python 带来的兼容风险；
- 不是说 Python 3.15 永远不能用，而是当前学习环境以 3.14.8 验证。

### 17.2 `py install 3.14` 命令错误

你执行过：

```powershell
py install 3.14
```

但当前系统中的 `py.exe` 是旧版 Python Launcher，不支持这个安装命令。

正确做法是使用 Python 3.14 安装程序，安装后验证：

```powershell
py -3.14 --version
```

### 17.3 `.venv314\Scripts\python.exe` 找不到

这说明当前目录下还没有创建 `.venv314`，或路径名称不一致。

创建：

```powershell
py -3.14 -m venv .venv314
```

### 17.4 PowerShell 激活虚拟环境

如果执行策略阻止脚本：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv314\Scripts\Activate.ps1
```

`-Scope Process` 只影响当前 PowerShell 进程，不会永久修改系统策略。

### 17.5 把 VS Code 命令输入到终端

你曾经把：

```text
Python: Select Interpreter
→ .venv314\Scripts\python.exe
```

直接输入 PowerShell，于是 PowerShell 报“无法识别”。

正确操作：

1. 在 VS Code 按 `Ctrl + Shift + P`；
2. 输入 `Python: Select Interpreter`；
3. 选择 `.venv314\Scripts\python.exe`；
4. 重新打开终端；
5. 使用 `python --version` 验证。

### 17.6 VS Code 解释器正确，但终端仍然导入失败

如果：

```powershell
python -c "import langchain_core"
```

报：

```text
ModuleNotFoundError: No module named 'langchain_core'
```

通常是当前终端使用了错误的 Python。

检查：

```powershell
Get-Command python
python --version
python -m pip show langchain-core
```

最可靠的安装方式：

```powershell
python -m pip install ...
```

不要只使用裸 `pip`，因为它可能属于另一个 Python。

### 17.7 环境变量末尾多了逗号

曾经出现：

```python
model_name = os.getenv("OPENAI_MODEL"),
```

末尾逗号会创建元组：

```python
("模型名称",)
```

而不是字符串，因此 LangChain 内部调用 `model.lower()` 时会报：

```text
AttributeError: 'tuple' object has no attribute 'lower'
```

正确写法：

```python
model_name = os.getenv("OPENAI_MODEL")
```

### 17.8 百炼模型需要 `base_url`

使用阿里云百炼的 OpenAI-compatible 接口时：

```python
model = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
)
```

不要把官方 OpenAI 的默认地址和百炼配置混用。

### 17.9 `model_with_tools.invoke()` 没有执行函数

正确理解：

```python
ai_message = model_with_tools.invoke(messages)
```

只产生：

```python
ai_message.tool_calls
```

真正执行函数的是：

- 原生代码中的工具分发器；
- LangChain Agent 内部；
- LangGraph 的 `ToolNode`。

### 17.10 判断错消息类型

判断模型是否请求工具：

```python
last_message.tool_calls
```

这里的 `last_message` 应该是 `AIMessage`。

不是判断它是不是 `ToolMessage`，因为 `ToolMessage` 表示工具已经执行完并返回结果。

### 17.11 单独调用 ToolNode 报 Runtime 错误

当前版本的 `ToolNode` 应该放入编译后的 Graph 中使用，不要简单地把它当成普通函数脱离 Graph 运行。

推荐：

```python
builder.add_node("tools", ToolNode([search_faq]))
graph = builder.compile()
graph.invoke(...)
```

### 17.12 Checkpoint 需要 `thread_id`

如果编译时使用 Checkpointer：

```python
graph = builder.compile(checkpointer=checkpointer)
```

调用时必须传入：

```python
config = {
    "configurable": {
        "thread_id": "session-U1001-001"
    }
}
```

没有同一个 `thread_id`，就无法恢复同一个会话线程。

### 17.13 `InMemorySaver` 不是生产持久化

`InMemorySaver` 数据只在当前 Python 进程内存中：

- 进程重启会丢失；
- 多 Worker 之间不共享；
- 不适合生产环境。

### 17.14 模型可能补充工具结果中没有的事实

即使工具只返回：

```text
退款规则：未发货订单可以申请退款。
```

模型仍可能自行补充退款到账时间、原路返回、具体操作步骤等内容。

改进方式：

- 系统提示词要求只能依据工具结果；
- 检索结果明确标记；
- 对高风险答案进行校验；
- 使用结构化输出；
- 对涉及金额、退款、订单状态的内容进行业务层验证。

---

## 18. 11 个练习文件对应的知识点

| 文件 | 主要内容 | 实际验证 |
|---|---|---|
| `lesson_05_01.py` | Fake Model、Message、Tool、手动执行工具 | 是 |
| `lesson_05_02.py` | `@tool`、`bind_tools`、工具 Schema | 是 |
| `lesson_05_03.py` | LangChain `create_agent` | 是 |
| `lesson_05_04.py` | State、消息追加、`add_messages` | 是 |
| `lesson_05_05.py` | Node、固定 Edge、`compile`、`invoke` | 是 |
| `lesson_05_06.py` | LangGraph Agent 循环、条件边、ToolNode | 是 |
| `lesson_05_07.py` | 独立使用 InMemoryStore | 是 |
| `lesson_05_08.py` | Store、Runtime Context、长期记忆注入 | 是 |
| `lesson_05_09.py` | RetryPolicy | 是 |
| `lesson_05_10.py` | RetryPolicy + error_handler | 是 |
| `lesson_05_11.py` | interrupt、人工审批、Command resume | 是 |

---

## 19. 最终 Agent 的三种实现对比

### 19.1 原生 OpenAI SDK

自己负责：

- 定义工具 Schema；
- 保存 messages；
- 调用模型；
- 解析 tool_calls；
- 查找 Python 函数；
- 执行函数；
- 生成 tool message；
- 再次调用模型；
- 处理最大轮次；
- 处理异常；
- 保存会话。

### 19.2 LangChain Agent

LangChain 帮你封装：

- 工具 Schema 生成；
- 工具对象；
- 工具调用消息；
- 工具执行；
- Agent 循环；
- 基本消息流转。

你仍然必须理解：

- 模型为什么返回 tool_calls；
- 工具函数什么时候执行；
- ToolMessage 如何和 tool_call_id 对应；
- 工具结果如何影响下一轮模型调用；
- 业务工具是否安全、是否幂等。

### 19.3 LangGraph Agent

LangGraph 让你显式控制：

- State；
- Node；
- 固定 Edge；
- 条件 Edge；
- 循环；
- ToolNode；
- Checkpoint；
- Store；
- RetryPolicy；
- error_handler；
- interrupt；
- Command resume。

你仍然必须理解：

- 模型调用和工具执行是两件事；
- State 在节点之间如何流动；
- 条件函数如何决定下一条边；
- Checkpoint 和 Store 的区别；
- 重试是否会造成重复业务操作；
- 人工恢复时使用哪个 thread_id。

---

## 20. 面试回答模板

### 问：LangGraph 是什么？

可以回答：

> LangGraph 是一个基于 State、Node 和 Edge 的 Agent 流程编排框架。它不是模型，而是用来组织模型调用、工具执行、条件分支、循环、重试、人工介入和状态持久化的运行时。相比手写 while 循环，它更适合表达复杂、有状态、可暂停恢复的 Agent 流程。

### 问：模型会直接执行 Python 工具吗？

可以回答：

> 不会。模型只会根据工具 Schema 生成 tool call，包括工具名称和参数。后端或框架根据 tool call 找到对应 Python 函数并执行，再把执行结果包装成 ToolMessage 传回模型。

### 问：State 和 Checkpoint 有什么区别？

可以回答：

> State 是当前流程正在使用的数据，例如 messages、检索结果和重试次数。Checkpoint 是某个时刻保存下来的 State 快照，同时包含恢复流程所需的执行位置和中断信息。State 解决流程中携带什么数据，Checkpoint 解决流程之后如何继续。

### 问：Checkpoint 和长期 Memory 有什么区别？

可以回答：

> Checkpoint 通常面向一个 thread_id，用于保存同一条会话线程的流程状态。长期 Memory 使用 user_id 作为范围，用于保存跨会话的用户偏好和用户画像。前者是线程级状态，后者是用户级记忆。

### 问：为什么不用 LangGraph，直接用 LangChain Agent？

可以回答：

> 如果工具数量较多，但流程仍然是标准的模型和工具循环，LangChain Agent 更简单。如果流程包含明确的多步骤、条件分支、重试、人工审批和恢复，就需要 LangGraph 来显式编排流程。

### 问：FastAPI 和 LangGraph 分别负责什么？

可以回答：

> FastAPI 是 Web 服务层，负责 HTTP 请求、鉴权、参数校验、SSE 连接和响应。LangGraph 是 Agent 流程层，负责模型调用、工具调用、状态流转和流程控制。实际项目中通常由 FastAPI 路由调用 Agent Service，而不是把所有 Agent 逻辑直接写在路由函数中。

---

## 21. 当前可以写进简历的内容

建议使用准确、不过度夸大的表述：

> 使用 Python、LangChain 和 LangGraph 接入阿里云百炼 OpenAI-compatible 模型，构建 AI 客服 Agent 学习项目，实现工具调用、条件路由、Agent 循环、线程级 Checkpoint、长期 Memory、失败重试、错误兜底和人工审批恢复。

如果写成项目实践，可以补充：

- 使用 `@tool` 将客服知识库查询函数转换为结构化工具；
- 使用 `bind_tools` 将工具 Schema 暴露给模型；
- 使用 `StateGraph`、条件边和 `ToolNode` 实现模型—工具循环；
- 使用 `InMemorySaver` 验证线程状态保存；
- 使用 `InMemoryStore` 验证跨会话用户偏好读取；
- 使用 `RetryPolicy` 和 `error_handler` 处理临时失败和兜底；
- 使用 `interrupt` 与 `Command(resume=...)` 实现人工审批恢复。

### 暂时不要写成已经完成

目前学习项目还没有真正验证：

- Python FastAPI Agent 服务；
- Python SSE 流式输出；
- Python Qdrant RAG；
- PostgreSQL 业务工具；
- Redis 持久化；
- 生产级 Checkpointer；
- 生产级人工审批平台；
- 生产级多 Worker 部署。

这些可以作为下一阶段的实践目标。

---

## 22. 复习时必须能回答的核心问题

1. 模型调用和工具执行有什么区别？
2. `model_with_tools.invoke()` 为什么不会执行 Python 函数？
3. `@tool` 生成了什么？
4. `ToolNode` 什么时候执行？
5. `AIMessage.tool_calls` 和 `ToolMessage` 分别表示什么？
6. LangChain Agent 替你封装了什么？
7. LangGraph 的 State、Node、Edge 分别是什么？
8. `compile()` 和 `invoke()` 分别是什么？
9. 条件边如何决定下一步？
10. LangGraph 如何形成 Agent 循环？
11. State 和 Checkpoint 有什么区别？
12. Checkpoint 和 Store 有什么区别？
13. `thread_id` 和 `user_id` 有什么区别？
14. `InMemorySaver` 为什么不适合生产？
15. `RetryPolicy(max_attempts=3)` 是重试几次？
16. 什么异常适合重试？
17. `error_handler` 在什么时候执行？
18. `interrupt()` 为什么必须配合 Checkpoint？
19. `Command(resume=...)` 中的 `approved` 是什么？
20. FastAPI、LangChain、LangGraph 在实际项目中如何分层？

---

## 23. 你的阶段五真实掌握情况

已经掌握：

- 原生 Agent 循环和框架 Agent 的对应关系；
- LangChain Model、Message、Tool；
- 工具 Schema 和工具执行的区别；
- LangChain Agent 的基本使用；
- LangGraph State、Node、Edge；
- 条件分支和循环；
- Checkpoint 和 Store 的概念；
- RetryPolicy 和错误兜底；
- Human-in-the-loop 的暂停和恢复；
- 原生 OpenAI、LangChain、LangGraph 的选型边界。

还需要通过项目巩固：

- 不看笔记独立搭建一个完整 Graph；
- 将真实 Qdrant 检索接入 Node 或 Tool；
- 将真实 PostgreSQL 订单查询接入 Tool；
- 使用 FastAPI 暴露 Agent；
- 使用 SSE 推送 Graph 中间事件；
- 使用生产级 Checkpointer 和数据库；
- 设计工具幂等、权限和安全校验。

阶段五的核心已经完成，但“会解释”和“能独立搭建生产级服务”之间还差一次完整项目整合。

---

## 24. 下一阶段建议

下一阶段建议从最小的 FastAPI 接入开始：

```text
FastAPI POST /chat
        ↓
调用 LangGraph graph.invoke()
        ↓
返回最终答案
```

然后依次加入：

1. FastAPI 基础接口；
2. LangGraph Agent Service 分层；
3. PostgreSQL 订单查询工具；
4. Qdrant 检索 Node；
5. SSE 流式输出；
6. 持久化 Checkpoint；
7. 把学习代码整理成可写进简历的 Python AI 客服项目。

官方资料：

- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph Stores](https://docs.langchain.com/oss/python/langgraph/stores)
- [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)





