# Python AI Agent 第二阶段复习文档：FastAPI 与 Pydantic

> 适用项目：`C:\text\python\learning2\python-agent`
>
> 学习目标：使用 Python 构建 AI 服务和 Agent，而不是单独学习 Python 语法。
>
> 当前状态：本阶段基础知识已经跑通，但还需要进一步做工程化整理、测试和更真实的 AI 服务接入。

---

## 1. 当前学习背景

你已经熟悉：

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

本阶段的目标不是重新学习 Python 语法，而是掌握 Python 中与 AI 后端最相关的 FastAPI、Pydantic、异步接口、流式输出、配置管理和依赖注入。

当前 Python 项目独立放在：

```text
C:\text\python\learning2\python-agent
```

它与原来的 NestJS 项目分开，不修改 NestJS 代码。

---

## 2. Python 运行环境与 Node.js 的区别

### 2.1 官网安装的 Python 3.15 是什么

安装 Python 3.15 后，电脑上拥有的是一个基础 Python 运行时，例如：

```text
Python 解释器
标准库
pip 包管理工具
```

它类似于电脑上安装的 Node.js 本体。

验证当前 Python：

```powershell
python --version
```

你当前使用的是 Python 3.15。

### 2.2 虚拟环境是什么

创建虚拟环境：

```powershell
python -m venv .venv
```

这条命令的含义是：

```text
使用当前的 Python 解释器
创建一个名为 .venv 的隔离 Python 环境
```

虚拟环境中通常会有：

```text
.venv/
├── Scripts/
│   ├── python.exe
│   ├── pip.exe
│   └── Activate.ps1
└── Lib/
    └── site-packages/
```

第三方依赖会安装到：

```text
python-agent\.venv\Lib\site-packages
```

而不是全局 Python 的目录。

### 2.3 `venv` 和 `npm init -y` 不是完全等价

之前的类比容易造成误解：

```text
python -m venv .venv
```

主要是创建 Python 的隔离运行环境。

而：

```powershell
npm init -y
```

主要是创建：

```text
package.json
```

它本身不会安装 `node_modules`。

Node.js 中更准确的对应关系是：

| Node.js | Python |
|---|---|
| 安装 Node.js | 安装 Python 3.15 |
| `package.json` | `requirements.txt` 或 `pyproject.toml` |
| `npm install` | `pip install -r requirements.txt` |
| `node_modules` | `.venv/Lib/site-packages` |
| npm 依赖目录 | 虚拟环境依赖目录 |

### 2.4 激活虚拟环境

在 PowerShell 中：

```powershell
.\.venv\Scripts\Activate.ps1
```

看到提示符前出现：

```text
(.venv) PS C:\text\python\learning2\python-agent>
```

就代表当前 PowerShell 已经激活虚拟环境。

也可以用命令验证：

```powershell
python -c "import sys; print(sys.executable); print(sys.prefix != sys.base_prefix)"
```

你已经验证过，输出类似：

```text
C:\text\python\learning2\python-agent\.venv\Scripts\python.exe
True
```

其中：

- `sys.executable` 表示当前真正执行的 Python 路径；
- `True` 表示当前使用的是虚拟环境，而不是基础 Python 环境。

### 2.5 为什么之前进了 Python 交互模式后不能激活

当看到：

```text
>>>
```

说明你进入了 Python 交互解释器。

此时输入：

```text
pip
```

Python 会把它当成变量名，而不是 PowerShell 命令，所以出现：

```text
NameError: name 'pip' is not defined
```

同样：

```text
.venv\Scripts\
```

也会被当成 Python 代码，因此出现语法错误。

退出 Python 交互模式：

```python
exit()
```

或者按：

```text
Ctrl + Z，然后回车
```

之后再回到 PowerShell 执行激活命令。

结论：

```text
PowerShell 命令和 Python 代码不是同一种语言。
```

---

## 3. Python 依赖管理

### 3.1 `pip` 是什么

`pip` 是 Python 的包管理工具，类似 npm 或 pnpm。

推荐使用：

```powershell
python -m pip --version
```

而不是直接依赖：

```powershell
pip --version
```

因为 `python -m pip` 能确保使用的是当前 `python` 对应的 pip。

你已经验证过当前 pip 位于：

```text
C:\text\python\learning2\python-agent\.venv\Lib\site-packages
```

这说明 pip 使用的是项目虚拟环境。

### 3.2 当前依赖

项目中的 `requirements.txt`：

```text
fastapi==0.143.1
uvicorn==0.54.0
pydantic-settings==2.16.0
```

安装：

```powershell
python -m pip install -r requirements.txt
```

其中：

- `fastapi`：Web API 框架；
- `uvicorn`：ASGI 服务器；
- `pydantic-settings`：从环境变量和 `.env` 加载、转换、校验配置。

`pydantic-settings` 还带来了：

```text
python-dotenv
```

它负责读取 `.env` 文件。

### 3.3 `requirements.txt`、`pyproject.toml` 和 `pip freeze`

`requirements.txt` 通常用于简单项目，记录需要安装的依赖：

```text
fastapi==0.143.1
uvicorn==0.54.0
```

它不会因为执行 `pip install` 自动生成，需要手动创建或导出。

导出当前虚拟环境全部已安装包：

```powershell
python -m pip freeze > requirements.txt
```

但 `pip freeze` 可能包含间接依赖，例如 `starlette`、`anyio`、`h11` 等，不一定都是项目直接使用的依赖。

`pyproject.toml` 是更现代的 Python 项目配置文件，可以同时描述：

- 项目元数据；
- 依赖；
- 构建方式；
- 工具配置。

当前阶段使用 `requirements.txt` 已经足够，不需要同时引入 Poetry、uv 或其他包管理器。

---

## 4. FastAPI 项目启动

### 4.1 `app.main:app` 的含义

执行：

```powershell
python -m uvicorn app.main:app --reload
```

可以拆成：

```text
app.main  -> app/main.py 模块
app       -> main.py 中名为 app 的 FastAPI 对象
```

例如：

```python
from fastapi import FastAPI

app = FastAPI()
```

`--reload` 表示开发模式下监听代码变化并自动重启服务。

启动成功后：

```text
http://127.0.0.1:8000
```

可以访问：

```text
/docs
/redoc
```

其中 `/docs` 是 Swagger UI，可以直接测试接口，也能查看 Pydantic 生成的请求和响应结构。

### 4.2 FastAPI 和 NestJS 的对应关系

| FastAPI | NestJS |
|---|---|
| `FastAPI()` | Nest 应用实例 |
| `@app.get()` | `@Get()` |
| `@app.post()` | `@Post()` |
| Pydantic `BaseModel` | DTO |
| `Field()` | `class-validator` 装饰器 |
| `Depends()` | 部分依赖注入/请求前置处理能力 |
| Uvicorn | Node HTTP/Express/Fastify 服务器 |
| `HTTPException` | Nest HTTP 异常 |
| `StreamingResponse` | Node 中的流式 Response |

FastAPI 不强制要求 NestJS 那种 Module 结构。项目如何拆分，主要由开发者自己决定。

---

## 5. 路由和请求方法

### 5.1 健康检查接口

```python
@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

请求：

```text
GET /health
```

响应：

```json
{
  "status": "ok"
}
```

健康检查通常用于：

- Docker/Kubernetes 探活；
- 负载均衡器检查；
- 部署后确认服务是否启动。

### 5.2 根路径

```python
@app.get("/")
async def root():
    return {"service": "python-agent"}
```

### 5.3 GET 和 POST

```python
@app.get("/config")
async def read_config():
    ...
```

GET 通常用于读取资源。

```python
@app.post("/chat")
async def chat(request: ChatRequest):
    ...
```

POST 通常用于提交请求体、创建任务或执行操作。

---

## 6. Pydantic 请求模型

### 6.1 请求模型

```python
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
```

这个模型同时表达了：

- 请求必须是对象；
- 必须有 `message` 字段；
- `message` 必须是字符串；
- 最少 1 个字符；
- 最多 2000 个字符。

### 6.2 在路由中使用

```python
@app.post("/chat")
async def chat(request: ChatRequest):
    return {
        "message": request.message,
        "reply": "这是一个占位回复",
    }
```

`request: ChatRequest` 表示 FastAPI：

1. 从 JSON body 读取请求；
2. 转换为 `ChatRequest` 对象；
3. 执行字段校验；
4. 校验成功后才执行接口函数。

### 6.3 校验失败

请求：

```json
{
  "message": ""
}
```

会返回 HTTP 422，并且类似：

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "message"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {"min_length": 1}
    }
  ]
}
```

这相当于 NestJS 中 DTO 配合 `class-validator` 后，由框架自动返回校验错误。

---

## 7. Pydantic 响应模型

```python
class ChatResponse(BaseModel):
    message: str
    reply: str
```

在路由上声明：

```python
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(
        message=request.message,
        reply="这是一个占位回复",
    )
```

`response_model=ChatResponse` 的作用：

- 定义响应结构；
- 校验返回值；
- 过滤多余字段；
- 自动生成 OpenAPI/Swagger 文档；
- 帮助前后端明确接口契约。

可以把它理解为：

```text
请求 DTO + class-validator
响应 DTO + 序列化/校验
```

---

## 8. FastAPI 异常处理

```python
from fastapi import HTTPException


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if request.message == "simulate_error":
        raise HTTPException(
            status_code=503,
            detail="LLM service unavailable",
        )

    return ChatResponse(
        message=request.message,
        reply="这是一个占位回复",
    )
```

请求：

```json
{
  "message": "simulate_error"
}
```

响应：

```json
{
  "detail": "LLM service unavailable"
}
```

HTTP 503 表示服务暂时不可用，适合模拟：

- LLM 服务不可用；
- 向量数据库不可用；
- 上游 API 超时；
- 服务降级。

抛出异常的方式是：

```python
raise HTTPException(...)
```

不是：

```python
return HTTPException(...)
```

---

## 9. Service 层和路由层

简单项目可以这样理解：

```text
路由层：接收 HTTP 请求、校验参数、返回 HTTP 响应
Service 层：编写 AI 客服和 Agent 业务逻辑
```

示例：

```python
class AgentService:
    async def run(self, message: str):
        return {
            "message": message,
            "reply": f"处理：{message}",
        }
```

路由层：

```python
@app.post("/agent/run", response_model=ChatResponse)
async def run_agent(request: ChatRequest):
    result = await agent_service.run(request.message)
    return ChatResponse(**result)
```

当前项目只有一个简单服务时，推荐先这样组装：

```python
settings = get_settings()
agent_service = AgentService(settings)
```

然后多个路由共用这个实例。

### 9.1 什么情况下再增加第三层

真正的三层通常是：

```text
API/Router 层
    ↓
Service/Use Case 层
    ↓
Infrastructure 层
```

例如真实 AI Agent：

```text
POST /agent/run
    ↓
AgentService：编排 Agent 循环、工具调用、RAG
    ↓
OpenAIClient / QdrantRepository / RedisClient / MCPClient
```

当项目出现以下情况时，再考虑拆分：

- Agent 流程包含多个步骤；
- 同一个业务同时被 HTTP、SSE、后台任务调用；
- 需要使用 OpenAI、Qdrant、Redis、MCP；
- 需要替换真实客户端进行测试；
- 路由函数开始包含大量业务判断；
- 多人协作开发。

不要仅仅因为服务数量变多就强行拆层。

---

## 10. `Depends` 到底是什么

### 10.1 直接调用和 Depends 的区别

直接调用：

```python
@app.get("/agent/context")
async def agent_context():
    return get_agent_context()
```

这完全可以运行。

使用依赖注入：

```python
@app.get("/agent/context")
async def agent_context(
    context: dict[str, str] = Depends(get_agent_context),
):
    return context
```

这里：

```python
context: dict[str, str]
```

是类型标注，表示最终注入的值是字符串字典。

```python
Depends(get_agent_context)
```

不是立刻执行函数，也不是把 `Depends` 对象赋给 `context`。

它只是告诉 FastAPI：

```text
请求到达时，先调用 get_agent_context()
把结果放进 context 参数
```

### 10.2 `Depends` 解决什么问题

它主要解决：

- 多个路由共享前置逻辑；
- 依赖层级自动组装；
- 请求级资源的创建和清理；
- 认证信息提取；
- 测试时替换真实依赖。

它不是 Python 必须的写法，也不是所有服务都必须使用。

### 10.3 `Depends` 会不会每次创建新对象

如果依赖函数是：

```python
def get_agent_service(
    settings: Settings = Depends(get_settings),
) -> AgentService:
    return AgentService(settings)
```

那么不同请求通常会创建不同的 `AgentService` 实例。

FastAPI 默认只保证：

```text
同一个请求内，同一个依赖只解析一次
```

它不保证不同请求之间共享实例。

而顶部实例化：

```python
agent_service = AgentService(settings)
```

表示同一个 Uvicorn 进程中的所有请求共享这个实例。

但是使用多个 worker 时：

```text
worker 1 有一个实例
worker 2 有一个实例
worker 3 有一个实例
```

所以“全局单例”通常是“每个进程一个实例”，不是整个服务器集群只有一个实例。

### 10.4 `dependencies.py` 什么时候需要

`dependencies.py` 不是强制架构层，只是用来集中放依赖工厂函数的文件。

当多个路由都需要构建同一个复杂服务时，可以写：

```python
def get_agent_service(
    llm_client: LLMClient = Depends(get_llm_client),
    retriever: Retriever = Depends(get_retriever),
    redis: RedisClient = Depends(get_redis_client),
) -> AgentService:
    return AgentService(llm_client, retriever, redis)
```

路由只需要：

```python
@app.post("/agent/run")
async def run_agent(
    request: ChatRequest,
    service: AgentService = Depends(get_agent_service),
):
    return await service.run(request.message)
```

这样可以把“如何创建 AgentService”集中管理。

但如果依赖很简单：

```python
settings = get_settings()
agent_service = AgentService(settings)
```

直接顶部实例化更容易理解。

### 10.5 当前用户为什么适合用 Depends

可以直接写：

```python
@app.get("/orders")
async def get_orders(authorization: str = Header(...)):
    user = decode_token(authorization)
    return await query_orders(user.id)
```

这没有错。

如果很多接口都需要当前用户：

```python
async def get_current_user(
    authorization: str = Header(...),
):
    return decode_token(authorization)


@app.get("/orders")
async def get_orders(user: User = Depends(get_current_user)):
    return await query_orders(user.id)
```

执行顺序并没有改变：

```text
读取 Token → 解码用户 → 执行业务
```

`Depends` 只是把可复用的前置逻辑抽出来。

### 10.6 数据库 Session 是什么

数据库 Session 可以理解为一次数据库操作上下文，类似于 Prisma 中一组查询或事务的上下文对象。

它通常负责：

- 执行查询；
- 管理事务；
- 提交；
- 回滚；
- 释放连接。

概念示例：

```python
def get_db_session():
    session = create_session()

    try:
        yield session
    finally:
        session.close()
```

FastAPI 可以保证：

```text
请求开始 → 创建 Session → 注入路由
请求结束 → 关闭 Session
```

当前项目使用 Prisma，暂时不需要学习 Python 数据库 Session。以后如果使用 SQLAlchemy，再单独学习。

---

## 11. Python 异步接口

### 11.1 `async def` 不一定必须有 `await`

下面的代码语法上完全合法：

```python
@app.get("/events")
async def events():
    return StreamingResponse(event_generator())
```

因为 `events()` 的职责只是：

```text
创建并返回 StreamingResponse
```

真正的异步等待发生在 `event_generator()` 内部：

```python
async def event_generator():
    for token in tokens:
        yield f"data: {token}\n\n"
        await asyncio.sleep(0.5)
```

TypeScript 中 `async function` 没有 `await` 也同样合法，只是可能被 linter 提示。

### 11.2 为什么 AI 服务经常需要异步

AI 服务通常会等待：

- LLM API；
- 数据库；
- Redis；
- Qdrant；
- MCP 工具；
- 文件或网络 IO。

如果同步阻塞，服务器在等待一个请求时可能无法高效处理其他请求。

异步接口的目标不是让单个请求一定更快，而是让等待 IO 时能够处理其他任务。

---

## 12. SSE 流式返回

### 12.1 `yield` 是什么

`yield` 是 Python 关键字，不需要导入。

普通函数遇到 `return` 就结束。

生成器函数遇到 `yield` 会：

1. 返回一段数据；
2. 暂停当前位置；
3. 下次继续执行；
4. 直到没有更多数据。

`async def` 加 `yield` 后，就是异步生成器。

### 12.2 `StreamingResponse`

```python
from fastapi.responses import StreamingResponse
```

示例：

```python
async def event_generator():
    tokens = ["你好", "，", "这是", "一条", "流式回复"]

    for token in tokens:
        yield f"data: {token}\n\n"
        await asyncio.sleep(0.5)


@app.get("/events")
async def events():
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
```

### 12.3 参数解释

```python
StreamingResponse(
    content,
    status_code=200,
    headers=None,
    media_type=None,
    background=None,
)
```

调用时：

```python
StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
)
```

第一个位置参数就是 `content`，所以不会传错。

这些写法效果相近：

```python
media_type="text/event-stream"
```

和：

```python
headers={
    "content-type": "text/event-stream; charset=utf-8"
}
```

但推荐使用 `media_type`，因为它明确表达响应媒体类型，框架会负责生成合适的 Content-Type。

### 12.4 `background`

`background` 是响应发送完成后执行的后台任务，例如：

- 写日志；
- 清理临时资源；
- 记录统计信息。

它不是 Celery，也不是 Redis 队列，不能用于可靠的长时间任务。

---

## 13. 配置和环境变量

### 13.1 `.env`

当前 `.env`：

```env
APP_NAME=AI Customer Service Python Agent
APP_ENV=dev
DEBUG=false
```

`.env` 存放当前环境的实际配置值，不应该提交 API Key、密码等敏感信息。

### 13.2 为什么需要 `config.py`

三处内容分别承担不同职责：

```text
.env       实际值
config.py  配置字段、类型和校验规则
业务代码    使用解析后的配置对象
```

不是重复保存同一个值。

例如：

```python
class Settings(BaseSettings):
    app_name: str
    app_env: str
    debug: bool
```

这里是在声明配置契约，而不是再次写入配置值。

### 13.3 `Settings` 继承 `BaseSettings`

```python
class Settings(BaseSettings):
```

等价于 TypeScript：

```typescript
class Settings extends BaseSettings {}
```

继承后得到：

- 读取 `.env`；
- 读取环境变量；
- 类型转换；
- 字段校验；
- `model_dump()`。

### 13.4 配置代码

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Default App"
    app_env: str = "dev"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

测试：

```powershell
python -c "from app.core.config import Settings; print(Settings().model_dump())"
```

你已经验证过：

```text
{'app_name': 'AI Customer Service Python Agent', 'app_env': 'dev', 'debug': True}
```

后来将 `.env` 改成 `DEBUG=false` 并重启服务后，接口返回了：

```text
debug False
```

这说明 Pydantic Settings 把字符串配置转换成了真正的布尔值。

### 13.5 和 `python-dotenv` 的区别

简单做法：

```python
from dotenv import load_dotenv
import os

load_dotenv()

app_name = os.getenv("APP_NAME")
```

它类似于 Node.js：

```typescript
import "dotenv/config";

const appName = process.env.APP_NAME;
```

`python-dotenv + os.getenv` 主要是读取配置。

`pydantic-settings` 在此基础上增加：

- 类型转换；
- 必填字段校验；
- 统一配置对象；
- 配置模型；
- 测试时方便传入不同配置。

AI 服务配置通常不只有一个字符串，还包括：

- API Key；
- 超时时间；
- 模型名称；
- Redis 地址；
- Qdrant 地址；
- 日志开关；
- 环境名称。

因此使用 Settings 更适合工程项目。

---

## 14. 当前已经完成并验证的接口

### `GET /health`

已验证：

```json
{
  "status": "ok"
}
```

### `GET /`

已验证：

```json
{
  "service": "python-agent"
}
```

### `POST /chat`

正常请求：

```json
{
  "message": "你好"
}
```

响应：

```json
{
  "message": "你好",
  "reply": "这是一个占位回复"
}
```

### `POST /agent/run`

已验证能够调用 `AgentService` 并返回占位结果。

当前建议的简化版结构是：

```python
settings = get_settings()
agent_service = AgentService(settings)
```

路由直接调用全局服务实例，而不是为了一个简单服务强行增加 `get_agent_service`。

### `GET /events`

已验证 SSE 流式返回能够分段输出文本。

---

## 15. PowerShell 测试命令

### 测试 POST JSON

```powershell
$body = @{ message = "你好" } | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/chat `
  -ContentType "application/json" `
  -Body $body
```

反引号 `` ` `` 是 PowerShell 的换行符。

### 测试配置

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri http://127.0.0.1:8000/config
```

### 中文乱码

如果 PowerShell 显示：

```text
????
å·²æ¶...
```

不一定是 API 响应错误，通常是终端编码显示问题。

可以先设置：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

也可以使用浏览器的 `/docs` 查看真实 JSON 响应。

---

## 16. 面试中应该如何解释

### 16.1 为什么使用 Pydantic

可以这样回答：

> 我使用 Pydantic 定义请求和响应模型，对用户消息长度、字段类型进行校验，并让 FastAPI 自动生成 OpenAPI 文档。相比在接口函数里手动判断，模型层能够统一处理校验错误。

### 16.2 为什么使用异步接口

可以这样回答：

> AI 服务经常需要等待 LLM、向量数据库、Redis 或 MCP 工具的网络 IO。使用 `async def` 和异步客户端，可以在等待当前请求的 IO 时处理其他请求，提高并发处理能力。异步主要优化 IO 等待，不代表单个模型调用一定更快。

### 16.3 为什么使用 SSE

可以这样回答：

> LLM 生成内容通常需要一定时间。我使用异步生成器通过 `yield` 分段产生数据，再用 `StreamingResponse` 设置 `text/event-stream` 返回，让客户端可以逐步接收生成内容，而不是等待完整答案。

### 16.4 为什么使用 Settings

可以这样回答：

> 我没有在业务代码中到处直接读取环境变量，而是使用 Pydantic Settings 集中读取 `.env` 和环境变量，并进行类型转换和校验。业务服务只依赖一个配置对象，更方便测试和切换开发、测试、生产环境。

### 16.5 为什么使用 Depends

可以这样回答：

> FastAPI 的 Depends 是函数级依赖解析机制。它适合复用当前用户、数据库 Session、客户端和服务工厂等依赖。对于简单的无状态服务，我也可以在应用启动时直接实例化；并不是所有对象都必须通过 Depends 创建。

### 16.6 `Depends` 和 NestJS 依赖注入的区别

可以这样回答：

> NestJS 有完整的 IoC 容器和 Module Provider 注册机制，类实例通常由容器管理。FastAPI 的 Depends 更轻量，本质上是根据函数参数构建依赖调用链。FastAPI 不要求所有服务都注册到一个 Module 中，简单对象可以手动实例化，只有共享、请求级、需要清理或需要测试替换的依赖才适合使用 Depends。

---

## 17. 当前可以写进简历的内容

如果这些代码确实保留在项目中，可以写：

- 使用 Python 和 FastAPI 构建 AI 服务 API；
- 使用 Pydantic 定义请求/响应模型并实现参数校验；
- 实现健康检查、聊天接口和 Agent 执行接口；
- 使用异步接口处理 AI 服务中的 IO 操作；
- 使用 SSE 实现流式响应原型；
- 使用 Pydantic Settings 管理环境配置；
- 了解 FastAPI Depends 的依赖解析机制；
- 按路由层和服务层拆分简单业务逻辑。

更准确的表述应该是“实现了原型”或“搭建了基础能力”，不要夸大为生产级 Agent 平台。

---

## 18. 当前暂时不能写进简历的内容

除非你在 Python 项目中真正实现并验证，否则暂时不要写：

- Python OpenAI SDK 集成；
- Python Function Calling；
- Python MCP Client/Server；
- Python Qdrant RAG 检索链路；
- Python Redis 会话记忆；
- Python PostgreSQL 数据持久化；
- 生产级 Agent 自主循环；
- 生产级 SSE 断线重连和取消处理；
- 多 worker、限流、监控、链路追踪。

这些技术可以写在你已经真实完成的 NestJS 项目经历中，但不要把 NestJS 的实现自动算作 Python 项目经验。

---

## 19. 第二阶段进度评估

这是基于目前实际完成情况的教学估计，不是代码质量评分。

| 内容 | 状态 |
|---|---|
| Python 虚拟环境和 pip | 已完成并验证 |
| FastAPI 启动与 Uvicorn | 已完成并验证 |
| GET/POST 路由 | 已完成并验证 |
| Pydantic 请求模型 | 已完成并验证 |
| 字段长度校验和 422 | 已完成并验证 |
| Pydantic 响应模型 | 已完成并验证 |
| HTTPException 和 503 | 已完成并验证 |
| Service 层基本概念 | 已理解并实现占位服务 |
| Depends 基础概念 | 已学习，但需要后续用真实场景巩固 |
| async/await 接口 | 已完成并验证 |
| SSE 流式响应 | 已完成原型并验证 |
| `.env` 配置读取 | 已完成并验证 |
| Pydantic Settings 类型转换 | 已完成并验证 |
| 多模块/APIRouter 工程结构 | 尚未系统实践 |
| 自动化测试 | 尚未学习 |
| 真实 LLM 异步调用 | 尚未在本阶段实现 |
| 数据库 Session | 尚未学习，也暂时不需要 |

综合来看：

```text
核心知识点覆盖：约 85%
工程化熟练度：约 65%
第二阶段整体进度：约 75%～80%
```

还剩下的重点不是继续堆概念，而是：

1. 把当前 `main.py` 结构整理得更清楚；
2. 学习 `APIRouter` 和模块拆分；
3. 学习基础测试；
4. 处理更真实的异常和响应；
5. 进一步实践配置、依赖和 SSE；
6. 再进入 Python OpenAI SDK、RAG 和 Agent 核心实现。

### 当前阶段最重要的结论

你现在不需要死记：

```text
所有服务都必须放 dependencies.py
所有对象都必须使用 Depends
所有配置都必须直接 os.getenv
所有项目都必须一开始拆成很多层
```

更正确的原则是：

```text
简单对象，直接组装。
共享且复杂的对象，集中组装。
请求级对象，使用 Depends。
需要清理的资源，使用带 yield 的依赖或生命周期管理。
业务逻辑放 Service，HTTP 细节放路由。
```

---

## 20. 下一阶段建议

下一次继续时，建议先不接真实 LLM，而是做一个小的工程化整理：

```text
main.py
  ↓
APIRouter
  ↓
schemas
  ↓
AgentService
```

把 `/health`、`/chat`、`/agent/run`、`/events` 按功能拆分，同时保留当前能运行的行为。

之后再学习：

```text
Python OpenAI SDK
  ↓
真实异步调用
  ↓
Function Calling
  ↓
RAG
  ↓
Agent 循环
```

---

## 21. APIRouter 实际拆分记录

后续已经将核心接口拆分为独立路由模块：

```text
app/
├── main.py
├── core/
│   └── config.py
├── schemas/
│   └── chat.py
├── routers/
│   ├── health.py
│   ├── chat.py
│   ├── agent.py
│   └── events.py
└── services/
    └── agent_service.py
```

### `main.py` 的职责

```python
from fastapi import FastAPI

from app.routers.agent import router as agent_router
from app.routers.chat import router as chat_router
from app.routers.events import router as events_router
from app.routers.health import router as health_router


app = FastAPI(title="AI Customer Service Python Agent")

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(agent_router)
app.include_router(events_router)
```

`main.py` 不再负责承载所有业务路由，而是主要负责：

- 创建 FastAPI 应用；
- 注册路由；
- 处理应用级配置和生命周期。

### `APIRouter` 的作用

例如 `app/routers/agent.py`：

```python
from fastapi import APIRouter, Depends

from app.dependencies import get_agent_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agent_service import AgentService


router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)


@router.post("/run", response_model=ChatResponse)
async def run_agent(
    request: ChatRequest,
    service: AgentService = Depends(get_agent_service),
) -> ChatResponse:
    result = await service.run(request.message)
    return ChatResponse(**result)
```

最终路径由两部分组成：

```text
prefix="/agent"
@router.post("/run")
-------------------
POST /agent/run
```

### 拆分时遇到的导入问题

当 `ChatRequest` 和 `ChatResponse` 从 `main.py` 移动到：

```text
app/schemas/chat.py
```

`main.py` 中仍然使用 `/agent/run` 的响应模型，因此必须显式导入：

```python
from app.schemas.chat import ChatRequest, ChatResponse
```

`from app.routers.chat import router as chat_router` 只会导入 `router` 变量，不会自动把 `chat.py` 中的所有名称导入到 `main.py`。

错误：

```text
NameError: name 'ChatResponse' is not defined
```

本质是 Python 模块命名空间中没有 `ChatResponse` 这个名字。

---

## 22. 自动化测试实践记录

### 测试依赖

测试依赖单独放在：

```text
requirements-dev.txt
```

当前内容：

```text
-r requirements.txt
pytest==9.1.1
httpx2==2.13.1
```

其中：

- `pytest`：运行测试；
- `httpx2`：当前 Starlette TestClient 使用的测试 HTTP 客户端；
- `-r requirements.txt`：复用项目运行依赖。

传统的 `httpx` 在当前 Starlette 版本中会产生弃用警告，因此改为 `httpx2`。测试依赖属于开发环境，不是服务运行时必须依赖。

### `TestClient` 工作方式

```python
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)
```

`TestClient` 不需要真实启动 Uvicorn，也通常不经过 `127.0.0.1:8000` 网络连接。它直接把请求交给 FastAPI 的 ASGI 应用：

```text
client.post()
  ↓
路由匹配
  ↓
Pydantic 校验
  ↓
执行接口函数
  ↓
生成响应
```

因此异步接口可以用普通同步测试函数测试：

```python
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
```

### 当前测试文件

```text
tests/
├── test_health.py
├── test_chat.py
├── test_agent.py
├── test_dependencies.py
└── test_events.py
```

目前已经验证：

```text
/health                       正常响应
/chat                         正常响应
/chat 空消息                  返回 422
/agent/run                    正常执行
/chat simulate_error          返回 503
/config                       Settings 注入成功
/agent/context                Depends 注入成功
/events                       SSE 响应头和内容正确
```

最终测试结果：

```text
8 passed in 2.97s
```

SSE 测试耗时接近 3 秒，是因为测试等待了 5 个事件，每个事件之间有 0.5 秒延迟。当前测试验证了最终内容和响应头，不代表已经验证客户端实时断开、取消生成和断线重连。

### 测试中遇到的响应差异

接口实际返回：

```json
{
  "detail": "LLM service is unavailable"
}
```

测试如果写成：

```json
{
  "detail": "LLM service unavailable"
}
```

字符串不完全相等，因此断言失败。自动化测试比较的是实际接口契约和预期契约是否一致。

---

## 23. 当前阶段最新进度

经过路由拆分和测试实践后：

| 内容 | 最新状态 |
|---|---|
| FastAPI 启动 | 已完成 |
| 路由和 APIRouter | 已完成并验证 |
| 请求模型和响应模型 | 已完成并验证 |
| 参数校验 | 已完成并自动化测试 |
| HTTP 异常 | 已完成并自动化测试 |
| Service 层 | 已完成基础实现 |
| Depends 和 Settings | 已完成基础实践 |
| async 接口 | 已完成 |
| SSE 原型 | 已完成并测试 |
| `.env` 配置 | 已完成并验证 |
| 自动化测试 | 已完成基础部分，8 个测试通过 |
| SSE 实时断开/取消 | 尚未学习 |
| 真实 LLM 调用 | 下一阶段 |
| RAG、Function Calling、MCP | 下一阶段 |

当前第二阶段估计：

```text
FastAPI/Pydantic 核心知识：约 90%
工程化基础：约 80%
第二阶段整体：约 85%～90%
```

第二阶段还可以继续补充的内容主要是：

- 更规范地整理 `main.py` 中的诊断接口；
- 测试依赖覆盖和 Fake Service；
- 应用生命周期；
- SSE 客户端断开和取消；
- 更统一的错误响应格式。

这些属于工程强化，不影响当前 FastAPI 基础目标已经完成。

---

## 24. 第二阶段知识掌握测试记录

本阶段完成了 8 道口头理解题。测试重点不是背 API，而是判断能否解释：

- FastAPI 的启动过程；
- Pydantic 的请求和响应校验；
- Depends 的执行时机和生命周期；
- async、SSE 和流式响应；
- Settings 配置加载；
- APIRouter 的路由注册；
- TestClient 的测试原理；
- HTTP 异常处理。

最终结果：

```text
8 / 8 题完成
综合掌握度：约 85%～90%
```

### 第 1 题：FastAPI 启动命令

题目：解释下面命令的各个部分：

```powershell
python -m uvicorn app.main:app --reload
```

正确理解：

```text
python -m     使用当前 Python 解释器，以模块方式运行 Uvicorn
uvicorn       ASGI 服务器
app.main      导入 app/main.py 模块
:app          找到模块中的 app 对象
--reload      开发时监听文件变化并自动重启服务
```

需要特别记住：

```text
python -m 本身不等于虚拟环境。
```

当前激活了 `.venv` 后，`python` 恰好指向：

```text
.venv\Scripts\python.exe
```

因此运行的是虚拟环境中的 Uvicorn。

FastAPI 和 Uvicorn 的职责不同：

```text
Uvicorn 负责监听端口、接收 HTTP 请求、运行 ASGI 应用
FastAPI 负责路由、参数校验、依赖和响应
```

掌握情况：基本掌握。

### 第 2 题：Pydantic 请求和响应模型

题目涉及：

```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    message: str
    reply: str
```

如果请求是：

```json
{
  "message": ""
}
```

正确结论：

1. `chat()` 函数不会执行；
2. FastAPI 在进入接口函数前完成 Pydantic 校验；
3. 空字符串不满足 `min_length=1`，所以返回 HTTP 422；
4. `ChatRequest` 负责请求体校验；
5. `ChatResponse` 负责响应结构；
6. `response_model=ChatResponse` 负责响应校验、序列化、字段过滤和 OpenAPI 文档生成。

这相当于：

```text
Pydantic BaseModel + Field ≈ NestJS DTO + class-validator
```

掌握情况：已掌握。

### 第 3 题：Depends 和实例生命周期

题目涉及：

```python
def get_agent_service(
    settings: Settings = Depends(get_settings),
) -> AgentService:
    return AgentService(settings)


@app.post("/agent/run")
async def run_agent(
    request: ChatRequest,
    service: AgentService = Depends(get_agent_service),
):
    return await service.run(request.message)
```

正确理解：

- `Depends(get_agent_service)` 在定义路由时不会立即执行；
- 请求到达后，FastAPI 才会解析依赖；
- FastAPI 会先准备请求参数和依赖，再执行接口函数；
- `get_agent_service()` 中的 `AgentService(settings)` 会创建服务对象；
- 按普通工厂函数写法，不同请求通常不会共享同一个 `AgentService`；
- 同一个请求内，FastAPI 默认会缓存同一个依赖结果。

还要区分：

```text
@lru_cache 缓存 get_settings() 的结果
不代表 AgentService 自动变成全局单例
```

如果在模块顶部创建：

```python
settings = get_settings()
agent_service = AgentService(settings)
```

那么同一个 Python 进程中的多个请求可以共享该服务实例。这个方式适合无状态、可以安全共享的服务。

掌握情况：基本掌握，生命周期需要继续通过真实客户端和数据库场景巩固。

### 第 4 题：async 和 SSE

题目涉及：

```python
async def event_generator():
    for token in tokens:
        yield f"data: {token}\n\n"
        await asyncio.sleep(0.5)


@app.get("/events")
async def events():
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
```

正确理解：

- `events()` 只是创建并返回 `StreamingResponse`，所以可以没有 `await`；
- `event_generator()` 内部使用了 `await`，因此需要是异步生成器；
- `yield` 会产生一段数据并暂停，后续继续产生下一段；
- `text/event-stream` 告诉客户端按照 SSE 格式解析响应；
- SSE 数据通常使用 `data: 内容\n\n` 格式。

SSE 的准确定位是：

```text
基于 HTTP 的服务器单向事件流协议
```

它通常通过一个长时间保持打开的 HTTP 响应持续推送事件，但不只是普通的 HTTP 长连接。它还规定了事件格式和浏览器端的接收行为。

`TestClient.get("/events")` 通常会等待整个响应完成后再读取，而浏览器或真实 SSE 客户端可以在响应仍然打开时逐段接收。

掌握情况：基本掌握。

### 第 5 题：Settings 配置

题目涉及：

```python
class Settings(BaseSettings):
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

正确理解：

1. `Settings` 继承 `BaseSettings`，是为了获得读取环境变量、读取 `.env`、类型转换和校验能力，不是语法上的固定搭配；
2. `Settings()` 会读取配置、匹配字段、转换类型、校验并创建配置对象；
3. `env_file=".env"` 负责指定配置来源；
4. `debug: bool` 负责声明字段类型；
5. Pydantic 负责把 `.env` 中的字符串 `"false"` 转成布尔值 `False`；
6. `@lru_cache` 会缓存 `get_settings()` 的返回对象，使同一进程内通常只创建一次 Settings；
7. 修改 `.env` 后，已经创建的 Settings 对象不会自动更新，通常需要重启服务。

掌握情况：基本掌握。

### 第 6 题：APIRouter

题目涉及：

```python
router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)


@router.post("/run")
async def run_agent():
    ...


app.include_router(router)
```

正确答案：

1. 最终路径是 `POST /agent/run`；
2. `prefix` 给该 Router 下的所有路由统一增加路径前缀；
3. `tags` 用于 Swagger/OpenAPI 分组；
4. `include_router()` 把 Router 中的路由注册到 FastAPI 主应用；
5. 如果不调用 `include_router()`，该路由不会被主应用访问到。

掌握情况：已掌握。

### 第 7 题：TestClient

题目涉及：

```python
client = TestClient(app)


def test_chat():
    response = client.post(
        "/chat",
        json={"message": "hello"},
    )
```

正确理解：

- `TestClient` 不会启动一个真实的 Uvicorn 服务；
- 它不需要经过真实网络和 `127.0.0.1:8000`；
- 它会直接调用 FastAPI 的 ASGI 应用；
- 但仍然会经过路由匹配、依赖解析、Pydantic 校验和接口函数；
- `json={...}` 模拟 JSON 请求体；
- `response.status_code` 是 HTTP 状态码；
- `response.json()` 会把 JSON 响应体解析成 Python 对象；
- 测试函数可以使用普通 `def`，因为 TestClient 已经处理了异步调用。

掌握情况：基本掌握。

### 第 8 题：HTTP 异常

题目涉及：

```python
if request.message == "simulate_error":
    raise HTTPException(
        status_code=503,
        detail="LLM service is unavailable",
    )
```

正确理解：

- `raise` 会中断当前函数，把异常交给 FastAPI 的异常处理器；
- `return HTTPException(...)` 只是普通返回值，不会触发异常处理流程；
- HTTP 503 表示服务暂时不可用，常见于 LLM、数据库或其他上游服务不可用；
- HTTP 422 表示请求参数校验失败；
- 参数缺失、类型错误、长度不符合要求，都可能导致 422；
- 参数校验失败时，接口函数通常还没有开始执行。

掌握情况：基本掌握。

### 测试结论

你已经能够解释并实际验证第二阶段的主要内容。当前最需要继续强化的不是基础语法，而是工程场景中的选择：

```text
什么时候使用 Depends，什么时候直接组装对象；
什么时候使用进程级共享客户端，什么时候使用请求级资源；
如何管理数据库 Session 和外部客户端生命周期；
如何处理 SSE 断开、取消和重连。
```

这些属于下一层工程化实践，不影响第二阶段核心目标已经完成。

