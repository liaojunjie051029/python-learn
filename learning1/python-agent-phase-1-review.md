# Python AI Agent 开发基础：第一阶段复盘文档

> 学习目标：不是系统学习全部 Python 语法，而是掌握开发 AI 客服、工具调用、RAG 和 Agent 时最先会用到的 Python 基础。
>
> 学习环境：Windows + VS Code + PowerShell + Python 3.15.0
>
> 练习目录：C:\text\python\learning
>
> 记录日期：2026-10-15

---

## 1. 阶段结论先看

这一阶段已经完成了 Python Agent 开发所需的第一轮基础训练，并且每个知识点都使用了 AI 客服中的消息、工具调用、订单结果或 Agent 状态作为例子。

**阶段状态：已完成。** 除了基础知识点，最后的工具注册表和动态工具执行器也已经实际编写、运行和测试。

目前已经真正练习过的内容包括：

- 能在 VS Code 的 PowerShell 终端检查并运行 Python 文件；
- 能使用变量、字符串、数字、布尔值描述 Agent 状态；
- 能使用列表、字典、元组、集合组织消息、工具调用和权限集合；
- 能使用 if、for、while 编写工具校验、遍历和重试逻辑；
- 能编写带参数和返回值的工具函数；
- 能使用类型注解表达工具输入和返回值；
- 能区分业务失败和程序异常；
- 能读写文本、Markdown 和 JSON 文件；
- 能拆分模块和包，并进行显式导入；
- 能使用类和 dataclass 描述工具元数据；
- 能从 PowerShell 环境变量读取 Agent 配置；
- 能使用 async/await 和 asyncio.gather 并发调用多个异步工具；
- 能使用标准库通过 HTTP 获取 JSON 数据，并完成 bytes → str → dict 的解析。

本阶段的收尾项目已经完成：

- 使用工具对象保存工具名称、描述、处理函数和启用状态；
- 使用字典实现工具注册表；
- 根据工具名称动态查找工具；
- 检查工具是否存在以及是否启用；
- 使用 handler(\*\*arguments) 传递工具参数；
- 捕获未知工具、禁用工具和参数缺失等错误；
- 始终返回统一的 success/data/error 结构。

因此，第一阶段已经从“分别学习 Python 基础”完成到了“用 Python 组装一个最小 Agent 工具层”。

---

## 2. 学习进度总表

| 顺序 | 知识点                     | 状态   | 在 AI Agent 中的用途                               |
| ---- | -------------------------- | ------ | -------------------------------------------------- |
| 1    | 变量、字符串、数字、布尔值 | 已完成 | 表示用户消息、工具名、重试次数、开关和 Agent 状态  |
| 2    | 列表、字典、元组、集合     | 已完成 | 表示消息列表、工具调用、工具结果、白名单和去重集合 |
| 3    | if、for、while             | 已完成 | 判断成功失败、遍历工具、执行重试                   |
| 4    | 函数、参数、返回值         | 已完成 | 把订单查询、取消订单等能力封装成工具函数           |
| 5    | 类型注解                   | 已完成 | 表达工具参数类型和返回结果类型，提高可读性         |
| 6    | 异常处理                   | 已完成 | 处理非法输入、网络异常和工具内部错误               |
| 7    | 文件和 JSON                | 已完成 | 保存 Agent 状态、读取配置和解析接口结果            |
| 8    | 模块和包                   | 已完成 | 拆分订单工具、FAQ 工具和公共导出入口               |
| 9    | 类、对象和 dataclass       | 已完成 | 描述工具名称、描述和启用状态等元数据               |
| 10   | 环境变量                   | 已完成 | 配置运行模式、超时时间、重试次数和 API Key         |
| 11   | async/await                | 已完成 | 并发执行多个独立的工具或外部 API 请求              |
| 12   | HTTP 请求                  | 已完成 | 访问订单服务、知识库服务或其他外部工具服务         |
| 13   | 工具注册表和执行器         | 已完成 | 根据工具名称动态查找并执行函数                     |

---

## 3. 运行环境和 PowerShell 基础

### 3.1 当前环境

```text
Python 3.15.0
Windows
VS Code 集成终端
PowerShell
```

练习文件位于：

```powershell
C:\text\python\learning
```

运行 Python 文件：

```powershell
cd C:\text\python\learning
python --version
python .\lesson_01.py
```

查看当前目录中的 Python 文件：

```powershell
Get-ChildItem -Name *.py
```

查看文件内容：

```powershell
Get-Content .\lesson_01.py
```

### 3.2 曾经遇到的 VS Code 问题

最初在 VS Code 终端执行 python --version 没有输出，而在单独打开的 PowerShell 中可以得到 Python 3.15.0。当时 python 命令解析到了：

```text
C:\Users\liaoj\AppData\Local\Microsoft\WindowsApps\python.exe
```

这通常说明 VS Code 进程启动时还没有拿到最新的 PATH，或者命中了 WindowsApps 的 Python 别名。重新启动 VS Code，并新建一个终端后问题解决。

以后遇到类似问题，可以按这个顺序检查：

```powershell
python --version
Get-Command python -All
where.exe python
```

重点是区分：

- Python 没安装；
- Python 已安装，但 PATH 没更新；
- 命令被 WindowsApps 的别名拦截；
- VS Code 进程没有继承最新环境变量；
- 文件名写错，例如 lesson_01.py 和 lesson-01.py 不是同一个文件。

---

## 4. 统一的工具结果协议

这一阶段所有工具都尽量使用下面的结构返回结果：

```python
{
    "success": True,
    "data": ...,
    "error": None
}
```

失败时：

```python
{
    "success": False,
    "data": None,
    "error": "订单不存在"
}
```

这个结构类似于前端或 Node.js 项目中约定的统一响应格式。它的价值是：Agent 不需要为每个工具设计完全不同的判断逻辑。

```python
result = get_order_status("A1001")

if result["success"]:
    print("可以把 data 交给 Agent 继续处理")
else:
    print("工具失败：", result["error"])
```

后续实现工具注册表时，所有工具都应该继续遵守这个协议。

---

## 5. 变量、字符串、数字和布尔值

### 5.1 基本写法

```python
user_message = "我的订单到哪了？"
tool_name = "get_order_status"
max_retry_count = 2
tool_enabled = True
agent_state = "waiting_for_tool"
```

Python 中直接使用变量名赋值，不需要像 TypeScript 那样写 let 或 const：

```typescript
const toolName = "get_order_status";
let maxRetryCount = 2;
```

对应的 Python 是：

```python
tool_name = "get_order_status"
max_retry_count = 2
```

### 5.2 和 Agent 的关系

| Python 值    | AI 客服中的含义              |
| ------------ | ---------------------------- |
| 字符串 str   | 用户消息、工具名称、订单状态 |
| 整数 int     | 重试次数、超时时间、分页大小 |
| 浮点数 float | 价格、置信度、耗时           |
| 布尔值 bool  | 工具是否启用、调用是否成功   |

一个最小的打印练习：

```python
print("用户消息：", user_message)
print("准备调用工具：", tool_name)
print("最大重试次数：", max_retry_count)
print("工具是否启用：", tool_enabled)
print("Agent 当前状态：", agent_state)
```

### 5.3 需要记住的点

- Python 字符串可以使用单引号或双引号；
- True、False 首字母必须大写；
- None 表示没有值，类似 JavaScript 的 null，但不是完全相同的类型；
- Python 变量名通常使用蛇形命名法，例如 max_retry_count；
- Python 是动态类型语言，变量不要求提前声明类型。

---

## 6. 列表、字典、元组和集合

### 6.1 列表：消息序列或工具列表

```python
messages = [
    "用户：我的订单到哪了？",
    "Agent：准备调用订单查询工具",
]

print(messages[0])
```

列表的特点：

- 有顺序；
- 可以重复；
- 可以通过下标访问；
- 适合保存消息历史、工具调用顺序和搜索结果。

### 6.2 字典：工具调用和工具结果

```python
tool_call = {
    "name": "get_order_status",
    "arguments": {
        "order_id": "A1001"
    }
}

print(tool_call["name"])
print(tool_call["arguments"]["order_id"])
```

工具结果：

```python
tool_result = {
    "success": True,
    "data": {
        "status": "已发货",
        "estimated_delivery": "明天"
    },
    "error": None
}
```

字典是 Python 中非常重要的数据结构，实际开发中经常用于表示：

- LLM 返回的结构化结果；
- Function Calling 的工具名称和参数；
- HTTP JSON 响应解析后的对象；
- Agent 状态；
- 配置项和工具注册表。

### 6.3 元组：固定的工具身份

```python
tool_identity = ("cancel_order", "v1")

print(tool_identity[0])
print(tool_identity[1])
```

元组适合表示不希望随意修改的固定组合，例如工具名和版本号。

### 6.4 集合：白名单和去重

```python
allowed_tools = {
    "get_order_status",
    "cancel_order",
    "search_faq",
}

requested_tools = [
    "get_order_status",
    "cancel_order",
    "cancel_order",
    "search_faq",
]

unique_requested_tools = set(requested_tools)

print("cancel_order 是否允许：", "cancel_order" in allowed_tools)
print("去重后的工具集合：", unique_requested_tools)
```

集合的两个典型用途：

1. 使用 in 快速检查工具是否在白名单中；
2. 使用 set(list_value) 去掉重复工具名称。

注意：

```python
set()  # 空集合
{}     # 空字典，不是空集合
```

### 6.5 Python 字典、JSON 和 JavaScript 对象的区别

它们看起来相似，但不是一回事：

| 概念              | 本质                                              |
| ----------------- | ------------------------------------------------- |
| Python dict       | Python 进程内存中的数据结构                       |
| JavaScript object | JavaScript 运行时中的对象，可能通过原型链查找属性 |
| JSON              | 一种文本数据交换格式                              |

Python 字典通常这样取值：

```python
tool_call["name"]
```

这不是 JavaScript 原型链，而是在字典中按照 key 查找值。Python 字典没有 JavaScript 那种对象原型链语义。

如果 key 可能不存在，可以使用：

```python
tool_name = tool_call.get("name")
order_id = tool_call.get("arguments", {}).get("order_id")
```

tool_call["name"] 找不到 key 时通常会抛出 KeyError；get 找不到时默认返回 None。

---

## 7. if、for 和 while

### 7.1 if：判断工具是否成功

```python
if tool_result["success"]:
    print("Agent：工具调用成功")
else:
    print("Agent：工具调用失败")
    print("失败原因：", tool_result["error"])
```

这对应 Agent 中最基本的分支：成功时继续生成答案，失败时向用户解释、切换工具或重试。

### 7.2 for：遍历工具请求

```python
requested_tools = [
    "get_order_status",
    "cancel_order",
    "refund_order",
]

allowed_tools = {
    "get_order_status",
    "cancel_order",
}

for tool_name in requested_tools:
    if tool_name in allowed_tools:
        print("允许调用：", tool_name)
    else:
        print("拒绝调用：", tool_name)
```

这相当于一个简单的工具权限检查器。

### 7.3 while：工具失败重试

```python
attempt = 0
max_retry_count = 3
tool_success = False

while attempt < max_retry_count and not tool_success:
    attempt += 1
    print(f"第 {attempt} 次调用 get_order_status")

    tool_success = call_tool()

    if not tool_success:
        print("工具调用失败，准备重试")

if tool_success:
    print("Agent：已拿到订单状态")
else:
    print("Agent：多次调用失败")
```

实际项目中还需要考虑：

- 哪些错误值得重试；
- 是否使用指数退避；
- 是否设置最大总耗时；
- 是否避免对取消订单等非幂等操作盲目重试。

当前练习只掌握了最小的循环和重试结构，还没有实现生产级重试策略。

---

## 8. 函数、参数和返回值

### 8.1 把订单查询封装成工具函数

```python
def get_order_status(order_id):
    if order_id == "A1001":
        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "status": "已发货",
            },
            "error": None,
        }

    return {
        "success": False,
        "data": None,
        "error": "订单不存在",
    }
```

调用：

```python
result = get_order_status("A1001")
print(result)
```

### 8.2 函数在 Agent 中的意义

一个工具通常就是一个函数，函数负责：

1. 接收结构化参数；
2. 校验参数；
3. 访问数据库、HTTP 服务或知识库；
4. 返回统一结构；
5. 不直接决定整个 Agent 的对话流程。

这为后续的工具注册表提供了基础：注册表保存“工具名 → 函数”的映射，执行器根据名称调用函数。

### 8.3 默认参数和关键字参数

后续工具函数可能会出现：

```python
def search_faq(query: str, top_k: int = 3):
    ...
```

调用：

```python
search_faq("如何取消订单")
search_faq(query="如何取消订单", top_k=5)
```

目前重点是理解参数和返回值，复杂参数设计放到工具注册表阶段继续练习。

---

## 9. 类型注解

### 9.1 函数参数和返回值注解

```python
def get_order_status(order_id: str) -> dict:
    ...
```

变量注解：

```python
tool_name: str = "get_order_status"
max_retry_count: int = 3
tool_enabled: bool = True
```

### 9.2 和 TypeScript 的区别

TypeScript 的类型系统会参与编译检查；Python 的类型注解默认主要用于：

- 提高代码可读性；
- 给 VS Code 和静态检查工具提示；
- 帮助团队理解函数契约；
- 方便后续接入更严格的校验工具。

Python 解释器默认不会因为你写了 order_id: str 就自动拒绝所有非字符串值。因此不要把类型注解误认为运行时校验。

类型注解表达的是“我希望这里是什么类型”，不是“运行时已经强制保证了这个类型”。

---

## 10. 异常处理

### 10.1 参数错误和业务失败要区分

订单号为空属于输入错误，可以抛出异常并捕获：

```python
def get_order_status(order_id: str) -> dict:
    try:
        if not order_id:
            raise ValueError("order_id 不能为空")
    except ValueError as error:
        return {
            "success": False,
            "data": None,
            "error": str(error),
        }

    if order_id != "A1001":
        return {
            "success": False,
            "data": None,
            "error": "订单不存在",
        }

    return {
        "success": True,
        "data": {
            "order_id": order_id,
            "status": "已发货",
        },
        "error": None,
    }
```

这里有几种失败：

| 情况                               | 更适合的表达                       |
| ---------------------------------- | ---------------------------------- |
| order_id 为空，输入不合法          | 异常，例如 ValueError              |
| 订单格式合法，但数据库没有这笔订单 | 正常业务结果，success=False        |
| 网络超时、连接断开                 | 异常，通常由上层捕获并决定是否重试 |
| 订单已发货，取消不允许             | 正常业务结果，返回失败原因         |

不要为了“看起来统一”而把所有错误都抛成异常，也不要把程序崩溃吞掉后假装工具成功。

---

## 11. 文件和 JSON

### 11.1 写入普通文本、Markdown 和 JSON

file 不是需要导入的模块名，而是 with open(...) as file 创建出来的文件对象变量：

```python
with open("agent_log.txt", "w", encoding="utf-8") as file:
    file.write("Agent 开始调用订单工具\n")
```

写 Markdown 也是同样的方式：

```python
with open("agent_notes.md", "w", encoding="utf-8") as file:
    file.write("# Agent 运行记录\n\n工具调用成功。\n")
```

写 JSON：

```python
import json

agent_state = {
    "current_tool": "get_order_status",
    "status": "waiting_for_result",
}

with open("agent_state.json", "w", encoding="utf-8") as file:
    json.dump(
        agent_state,
        file,
        ensure_ascii=False,
        indent=2,
    )
```

### 11.2 json.dump 参数解释

```python
json.dump(agent_state, file, ensure_ascii=False, indent=2)
```

| 参数               | 含义                                     |
| ------------------ | ---------------------------------------- |
| agent_state        | 要序列化的 Python 对象，通常是字典或列表 |
| file               | 已经打开的文件对象                       |
| ensure_ascii=False | 不把中文转成 \u 编码，文件中保留可读中文 |
| indent=2           | 使用 2 个空格缩进，让 JSON 更易读        |

### 11.3 dump、dumps、load、loads

| API        | 输入                   | 输出         |
| ---------- | ---------------------- | ------------ |
| json.dump  | Python 对象 + 文件对象 | 直接写入文件 |
| json.dumps | Python 对象            | JSON 字符串  |
| json.load  | 文件对象               | Python 对象  |
| json.loads | JSON 字符串            | Python 对象  |

示例：

```python
json_text = json.dumps(agent_state, ensure_ascii=False)
restored_state = json.loads(json_text)
```

### 11.4 Python 字典和 JSON 的边界

```text
Python dict  --json.dumps-->  JSON 字符串  --网络或文件-->  JSON 字符串
JSON 字符串  --json.loads-->  Python dict
```

Python 字典是程序内存中的对象；JSON 是可以保存或传输的文本。两者不能因为结构相似就当成完全相同的东西。

Python 的 True、False、None 转换为 JSON 后分别是 true、false、null。

---

## 12. 模块、包和导入

### 12.1 模块

一个 .py 文件就是一个模块。例如 order_tools.py 可以提供：

```python
def get_order_status(order_id: str) -> dict:
    ...

def cancel_order(order_id: str) -> dict:
    ...
```

另一个文件中显式导入：

```python
from order_tools import get_order_status, cancel_order

result = get_order_status("A1001")
cancel_result = cancel_order("A1001")
```

Python 没有 TypeScript/ES Module 中完全对应的 export 关键字。模块顶层定义通常可以被导入；实际项目中主要通过命名、显式导入和 **all** 管理公开接口。

### 12.2 包和 **init**.py

一个工具包可以组织为：

```text
tools/
├── __init__.py
├── order_tools.py
└── text_tools.py
```

tools/**init**.py 可以作为统一入口：

```python
from .order_tools import get_order_status, cancel_order
from .text_tools import search_faq

__all__ = [
    "get_order_status",
    "cancel_order",
    "search_faq",
]
```

外部代码可以写：

```python
from tools import get_order_status, cancel_order, search_faq
```

### 12.3 **all** 和通配符导入的风险

```python
from order_tools import *
from text_tools import *
```

如果两个模块都暴露了同名函数，例如都存在 get_order_status，后一次导入可能覆盖前一次导入绑定的名称。此时：

```python
result = get_order_status("A1001")
```

代码表面上能运行，但你可能无法直观看出调用的是哪个模块的函数。

更推荐：

```python
import order_tools
import text_tools

order_result = order_tools.get_order_status("A1001")
faq_result = text_tools.search_faq("如何取消订单")
```

或者使用别名：

```python
from order_tools import get_order_status as get_order_status_tool
from text_tools import get_order_status as get_text_order_status
```

**all** 主要影响 from module import \* 的导出列表，不是强制的访问控制，也不是 TypeScript 的 export 等价物。

### 12.4 **init** 方法和 **init**.py 的区别

它们名字相似，但作用不同：

| 名称        | 作用                         |
| ----------- | ---------------------------- |
| **init**.py | 包目录的初始化文件和导出入口 |
| **init**    | 类实例创建时自动执行的方法   |

---

## 13. 类、对象和 dataclass

### 13.1 手写类

工具不仅有执行函数，还有名称、描述、启用状态等元数据：

```python
class Tool:
    def __init__(self, name: str, description: str, enabled: bool = True):
        self.name = name
        self.description = description
        self.enabled = enabled

    def summary(self) -> str:
        return f"{self.name}: {self.description}"
```

使用：

```python
order_tool = Tool(
    name="get_order_status",
    description="查询订单状态",
)

print(order_tool.name)
print(order_tool.summary())
```

### 13.2 使用 dataclass

```python
from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    description: str
    enabled: bool = True

    def summary(self) -> str:
        return f"{self.name}: {self.description}"
```

dataclass 是 Python 标准库，不需要安装第三方包。它可以自动生成常见的初始化方法、对象展示和比较逻辑，适合描述工具定义、Agent 状态和配置对象。

### 13.3 工具元数据和工具函数是两件事

需要区分：

```text
Tool 对象：工具叫什么、描述是什么、是否启用
工具函数：真正执行查询、取消、搜索等动作
```

后续的工具注册表要把两者连接起来：

```text
工具名称 -> 工具元数据 + 可执行函数
```

这正是从“零散工具函数”走向“Agent 工具系统”的关键一步。

---

## 14. 环境变量

### 14.1 从 PowerShell 设置环境变量

```powershell
$env:AGENT_MODE = "development"
$env:TOOL_TIMEOUT_SECONDS = "5"
$env:MAX_RETRY_COUNT = "4"
python .\lesson_15.py
```

只对当前 PowerShell 进程及其子进程有效。关闭终端后通常不会自动保留。

### 14.2 Python 中读取

```python
import os

agent_mode = os.getenv("AGENT_MODE", "development")
tool_timeout_seconds = int(os.getenv("TOOL_TIMEOUT_SECONDS", "5"))
max_retry_count = int(os.getenv("MAX_RETRY_COUNT", "3"))

api_key = os.getenv("OPENAI_API_KEY")
has_api_key = bool(api_key)
```

重要事实：环境变量读出来通常是字符串，所以数字配置要显式转换：

```python
"5"      # 字符串
int("5") # 整数 5
```

不要把 API Key 打印到终端或日志中，只判断是否配置即可。

### 14.3 和 Node.js dotenv/config 的区别

Node.js 中常见：

```javascript
import "dotenv/config";
console.log(process.env.AGENT_MODE);
```

它通常会自动读取 .env 文件并写入 process.env。

Python 标准库中的：

```python
os.getenv("AGENT_MODE")
```

只负责读取已经存在的环境变量，不会自动读取 .env 文件。

如果以后需要使用 .env 文件，需要额外安装 python-dotenv，然后：

```python
from dotenv import load_dotenv

load_dotenv()
```

目前的练习只使用 PowerShell 设置环境变量，因此还没有安装这个第三方依赖。

---

## 15. async/await 和并发工具调用

### 15.1 异步函数

```python
import asyncio


async def call_order_tool(tool_name: str) -> dict:
    print("开始调用：", tool_name)
    await asyncio.sleep(1)

    return {
        "success": True,
        "data": {"tool": tool_name},
        "error": None,
    }


async def main():
    result = await call_order_tool("get_order_status")
    print("工具结果：", result)


asyncio.run(main())
```

关键概念：

- async def 定义协程函数；
- await 等待另一个异步操作；
- asyncio.run(main()) 启动事件循环并运行入口协程；
- await asyncio.sleep(...) 不会像同步阻塞那样占住整个线程。

### 15.2 并发执行多个独立工具

```python
results = await asyncio.gather(
    call_order_tool("get_order_status"),
    call_order_tool("search_faq"),
    call_order_tool("get_shipping_info"),
)
```

如果三个工具相互独立，就不必严格串行等待。对于 Agent 来说，典型场景是：

- 同时查询订单状态和物流信息；
- 同时搜索 FAQ 和商品知识库；
- 同时调用多个独立的内部服务。

asyncio.gather 的结果顺序通常与传入任务的顺序一致，但任务本身可能按照耗时先后完成。

### 15.3 和 Node.js 的对应关系

| Python         | Node.js / TypeScript   |
| -------------- | ---------------------- |
| async def      | async function         |
| await          | await                  |
| asyncio.gather | Promise.all            |
| asyncio.run    | 启动异步入口的运行方式 |

不要把所有函数都写成异步。只有存在网络、文件、数据库或其他等待操作时，异步才有明显价值。还要避免在异步函数中直接使用耗时的同步阻塞调用，例如不加区分地使用 time.sleep。

---

## 16. HTTP 请求和 JSON 响应

### 16.1 使用标准库访问本地 HTTP 服务

本次练习使用 Python 自带的静态 HTTP 服务，避免一开始安装第三方 HTTP 客户端。

终端 A：

```powershell
cd C:\text\python\learning
python -m http.server 8000
```

终端 B：

```python
from urllib.request import urlopen
import json

url = "http://127.0.0.1:8000/http_data.json"

with urlopen(url, timeout=5) as response:
    status_code = response.status
    body_bytes = response.read()

body_text = body_bytes.decode("utf-8")
data = json.loads(body_text)

print("HTTP 状态码：", status_code)
print("响应数据：", data)
print("消息：", data["data"]["message"])
```

### 16.2 HTTP 响应数据的转换过程

```text
response.read()
        ↓
bytes（二进制字节）
        ↓ decode("utf-8")
str（JSON 文本）
        ↓ json.loads(...)
dict / list（Python 对象）
```

这和 Node.js 中拿到响应后调用 response.json() 的效果相似，只是 Python 标准库示例把每一步拆开展示了。

### 16.3 一个重要纠正：响应体不是响应头

练习输出中曾经使用了“响应头”这个标签，但执行的是：

```python
body_bytes = response.read()
```

response.read() 读取的是响应体，不是响应头。真正读取响应头应该使用：

```python
print(response.headers)
```

后续写日志时要准确区分：

- response.status：状态码，例如 200、404；
- response.headers：响应头；
- response.read()：响应体。

### 16.4 404 的排查方式

练习中第一次请求得到：

```text
HTTP Error 404: File not found
```

原因是 HTTP 服务的根目录和 http_data.json 所在目录不一致，或者请求路径和真实文件名不一致。排查顺序：

1. 确认服务终端当前目录；
2. 确认该目录下存在 http_data.json；
3. 确认 URL 文件名完全一致；
4. 确认端口号和服务端口一致；
5. 重新请求。

这比直接认为“Python HTTP 请求写错了”更准确。

---

## 17. 本阶段练习文件和成果

主要练习目录：

```text
C:\text\python\learning
```

已使用或涉及的练习文件包括：

```text
lesson_01.py  变量、字符串、数字、布尔值、Agent 状态
lesson_02.py  列表、字典、嵌套工具调用结果
lesson_03.py  元组、集合、白名单和去重
lesson_04.py  if/else 判断工具成功失败
lesson_05.py  for 遍历和工具权限检查
lesson_06.py  while 重试逻辑
lesson_07.py  函数、参数、返回值
lesson_08.py  类型注解
lesson_09.py  异常处理和输入校验
lesson_10.py  文件和 JSON
lesson_11.py  模块导入相关练习
lesson_12.py  工具包和显式导入
lesson_13.py  手写 Tool 类
lesson_14.py  dataclass Tool
lesson_15.py  环境变量
lesson_16.py  async/await
lesson_17.py  asyncio.gather 并发工具调用
lesson_18.py  HTTP + JSON
```

还涉及以下工具组织文件或数据文件：

```text
order_tools.py
tools/__init__.py
tools/order_tools.py
tools/text_tools.py
agent_state.json
http_data.json
```

其中，agent_state.json 和 http_data.json 是练习中使用的状态或 HTTP 数据文件；如果本地文件名或目录略有调整，应以实际目录为准。

后续综合测试文件位于：

```text
C:\text\python\learning1\test
```

包括：

```text
check_tool_call.py
state_persistence_test.py
tool_models.py
tool_app.py
config_test.py
async_tools_test.py
http_tools_test.py
tool_registry_test.py
```

已经观察到的代表性运行结果：

```text
查询结果： {'success': True, 'data': {'order_id': 'A1001', 'status': '已发货'}, 'error': None}
取消结果： {'success': False, 'data': None, 'error': '订单已经发货，无法取消'}
faq结果： {'success': True, 'data': ['如何取消订单的答案是：这是一个示例答案。'], 'error': None}
```

以及并发工具调用：

```text
开始调用： get_order_status
开始调用： search_faq
开始调用： get_shipping_info
```

这说明当前已经能写出一个包含动态注册和统一调度的最小 Agent 工具层原型。

### 17.1 最终综合项目：工具注册表和执行器

工具定义保存的是工具元数据和真正执行的处理函数：

```text
Tool 对象
├── name
├── description
├── handler
└── enabled
```

注册表使用工具名称作为 key：

```python
tool_registry = {
    "get_order_status": get_order_status,
    "search_faq": search_faq,
    "cancel_order": cancel_order,
}
```

执行器的核心流程：

```python
def execute_tool(tool_name: str, arguments: dict) -> dict:
    try:
        tool = tool_registry.get(tool_name)

        if tool is None:
            raise ValueError("无效的工具调用")

        if not tool.enabled:
            raise ValueError("工具已禁用")

        return tool.handler(**arguments)

    except (ValueError, TypeError) as error:
        return {
            "success": False,
            "data": None,
            "error": str(error),
        }
```

其中：

```python
arguments = {"order_id": "A1001"}
tool.handler(**arguments)
```

等价于：

```python
get_order_status_handler(order_id="A1001")
```

最终测试覆盖了五种情况：

```text
get_order_status：调用成功
search_faq：调用成功
refund_order：未知工具，返回失败
cancel_order：工具已禁用，返回失败
get_order_status 缺少 order_id：参数错误，返回失败但程序不崩溃
```

这一步证明你已经掌握了从“固定调用函数”到“根据字符串动态调度工具”的基本过程。

---

## 18. 面试复盘：可能会被怎么问

### 问题 1：Python 字典和 JSON 有什么区别？

建议回答：

> Python 字典是 Python 进程内存中的数据结构，JSON 是用于传输和保存的文本格式。可以用 json.dumps 把字典转成 JSON 字符串，用 json.loads 把 JSON 字符串还原成 Python 对象；写文件时对应 dump 和 load。两者结构相似，但不是同一个概念。

### 问题 2：为什么工具结果要统一成 success/data/error？

建议回答：

> Agent 可能会调用很多不同工具。如果每个工具返回结构都不同，上层流程会充满特殊判断。统一协议后，Agent 只需要先判断 success，成功处理 data，失败处理 error，工具可以被更容易地注册、替换和测试。

### 问题 3：订单不存在为什么不一定抛异常？

建议回答：

> 订单不存在通常是合法请求产生的业务结果，不一定代表程序出错，所以可以返回 success=False 和业务错误信息。空参数、类型错误、网络超时等更像输入或系统异常，可以通过异常机制交给上层处理。

### 问题 4：set 在工具系统中有什么用途？

建议回答：

> 我会用集合保存工具白名单，利用 tool_name in allowed_tools 判断是否允许调用；也可以把模型生成的工具列表转换成集合来去重。集合不保证原始列表顺序，因此如果顺序重要，仍然要保留列表。

### 问题 5：为什么不推荐多个 from xxx import \*？

建议回答：

> 不同模块可能暴露同名函数，后导入的名称可能覆盖先导入的名称，导致调用来源不清晰。工具系统更适合显式导入、模块名限定或使用别名，这样审查工具权限和定位问题都更容易。

### 问题 6：dataclass 解决了什么问题？

建议回答：

> 工具对象通常包含名称、描述、启用状态等数据字段。dataclass 可以减少手写初始化方法和展示逻辑的样板代码，同时保留类的类型注解和方法，适合表达工具定义和 Agent 状态。

### 问题 7：Python 类型注解会自动进行运行时校验吗？

建议回答：

> 默认不会。类型注解主要服务于可读性、编辑器提示和静态检查。真正的输入校验仍然需要代码、校验库或框架来完成。

### 问题 8：asyncio.gather 为什么适合 Agent？

建议回答：

> 当多个工具调用相互独立时，可以并发等待它们，减少总耗时。例如同时查询订单状态、物流信息和 FAQ。它适合 I/O 等待场景，但仍需处理超时、异常和取消任务。

### 问题 9：HTTP 响应为什么要先 decode 再 loads？

建议回答：

> response.read() 得到的是 bytes，decode("utf-8") 后才是 JSON 文本字符串，json.loads 再把文本解析成 Python 字典或列表。每一步的类型不同，明确拆开有利于排查编码和解析错误。

### 问题 10：当前能不能说自己会 Python Agent？

建议回答：

> 我已经完成了 Python Agent 工具层的基础练习，能够编写统一返回结构、白名单检查、重试、异常处理、模块化工具、工具注册表、动态工具执行器、异步调用和 HTTP/JSON 交互。下一步还需要接入真实模型和 Function Calling，才能形成更完整的 Python Agent 项目经验。

---

## 19. 简历边界：现在能写什么，暂时不能写什么

### 19.1 当前可以如实写成“实践过”的内容

前提是简历语境明确这是练习项目或个人学习项目：

> 使用 Python 实现 AI 客服工具调用原型，统一工具返回协议，包含工具白名单校验、失败重试、异常处理、模块化工具组织、dataclass 工具元数据、异步工具调用以及 HTTP/JSON 数据交互。

更完整的阶段项目描述可以写成：

> 使用 Python 实现最小 AI 客服工具层，设计 Tool 工具元数据模型和字典型工具注册表，根据模型返回的工具名称动态查找并执行处理函数，统一处理未知工具、禁用工具和参数错误，并返回 success/data/error 结构。

也可以拆成技术点：

- Python 基础数据结构和函数封装；
- Python 模块、包和显式导入；
- dataclass 描述工具元数据；
- 字典型工具注册表和动态工具执行器；
- asyncio 并发调用独立工具；
- 标准库 HTTP 请求和 JSON 解析；
- PowerShell 环境变量配置。

### 19.2 目前不能把它写成已经完成的内容

当前这阶段还不能直接声称已经用 Python 完成：

- Python OpenAI SDK 的真实模型调用；
- Python Function Calling 的完整闭环；
- Python MCP Server 或 MCP Client；
- Python RAG、Embedding、Qdrant 检索；
- Python Redis、PostgreSQL、Prisma 等生产连接；
- Python SSE 流式输出；
- LangChain 或 LangGraph Agent；
- 生产环境级的重试、熔断、鉴权、监控和部署。

你已有 Node.js / TypeScript AI 客服项目中的相关经验可以单独如实描述，但不能把 Node.js 已完成的能力自动当成 Python 已完成的项目经验。

---

## 20. 复盘清单

下次复习时，不要只重新阅读文档，建议在 C:\text\python\learning 中逐项操作：

- [ ] 把 A1001 改成一个不存在的订单号，观察统一失败结果；
- [ ] 传入空订单号，观察异常处理结果；
- [ ] 在工具白名单中增加或删除一个工具，观察 for 检查结果；
- [ ] 给 requested_tools 增加重复值，观察 set 去重；
- [ ] 把工具结果写入 .txt、.md 和 .json 三种文件；
- [ ] 解释 json.dump 和 json.dumps 的区别；
- [ ] 在两个模块中定义同名函数，验证通配符导入覆盖风险；
- [ ] 把 Tool 类改成 dataclass，增加一个 timeout_seconds 字段；
- [ ] 修改 PowerShell 中的 MAX_RETRY_COUNT，观察 Python 读取结果；
- [ ] 给三个异步工具设置不同等待时间，观察启动顺序和结果顺序；
- [ ] 故意把 HTTP 文件名写错，解释 404 的原因；
- [ ] 解释响应状态码、响应头和响应体的区别；
- [ ] 不看答案，独立写出 get_order_status("A1001") 的统一返回结构。
- [ ] 不看答案，独立写出一个工具注册表和 execute_tool 函数。

可以用下面的命令快速验证环境：

```powershell
cd C:\text\python\learning
python --version
python .\lesson_15.py
python .\lesson_17.py
```

---

## 21. 后续阶段：真实 LLM 和 Function Calling

第一阶段的工具注册表和执行器已经完成。下一阶段将把真实的大语言模型接入当前工具层，目标接口大致如下：

```python
result = execute_tool(
    "get_order_status",
    {"order_id": "A1001"},
)
```

后续学习重点：

1. 安装并配置 Python OpenAI SDK；
2. 使用环境变量安全读取 API Key；
3. 发送用户消息和工具定义给模型；
4. 解析模型返回的工具名称和参数；
5. 调用已经完成的 execute_tool；
6. 把工具结果追加回对话消息；
7. 让模型根据工具结果生成最终客服回复；
8. 处理模型调用失败、工具失败和多轮工具调用。

当前工具层和真实模型之间的关系：

```text
工具名称
    ↓
工具注册表
    ↓
工具定义（名称、描述、enabled、函数）
    ↓
工具执行器
    ↓
统一工具结果
```

下一阶段完成后，才会形成“模型决定调用什么工具，Python 执行工具并把结果交还给模型”的完整 Function Calling 闭环。

---

## 22. 官方参考资料

- [Python json 标准库文档](https://docs.python.org/3.15/library/json.html)
- [Python dataclasses 文档](https://docs.python.org/3.15/library/dataclasses.html)
- [Python asyncio 任务和协程文档](https://docs.python.org/3.15/library/asyncio-task.html)
- [Python urllib.request 文档](https://docs.python.org/3.15/library/urllib.request.html)
- [python-dotenv 官方仓库说明](https://github.com/motdotla/dotenv#readme)

---

## 最后自测：用一句话总结本阶段

> 我已经能够使用 Python 的数据结构、控制流、函数、异常、文件、模块、类、环境变量、异步和 HTTP 基础，编写一个包含工具注册表和动态执行器的 AI 客服工具层原型；下一步是接入真实 LLM 和 Function Calling。
