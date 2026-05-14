# Gaius

## 概况

当前项目处于 `0.1.0` 骨架阶段。

### 当前目录结构

```text
/Users/felix/Desktop/Gaius
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py
│   └── services/
│       └── __init__.py
├── .env
├── pyproject.toml
├── uv.lock
├── README.md
└── main.py
```

### 启动方式

```bash
uvicorn app.main:app --reload
```

## 当前设计原则

这一版先做单 agent，但模块边界按未来多 agent 演进的标准来设计。

- `api` 层：只收请求和回响应，不做业务判断
- `services` 层：负责编排业务流程
- `agents` 层：每个 agent 只关心自己的决策逻辑
- `core` 层：放未来不会轻易变化的基础抽象

核心原则：

- 现在先落单 agent
- 未来允许多 agent 协作
- 不硬编码业务路由
- 不把规则写死在 API 层
- 不靠特判堆行为

## 规划中的分层结构

这是下一步准备演进到的结构，不代表当前已经全部实现。

```text
app/
├── main.py
├── config.py
├── api/
│   ├── health.py
│   ├── chat.py
│   └── aiops.py
├── services/
│   ├── chat_service.py
│   ├── aiops_service.py
│   └── coordinator_service.py
├── agents/
│   ├── chat_agent.py
│   └── aiops_agent.py
├── tools/
│   ├── registry.py
│   ├── time_tool.py
│   └── knowledge_tool.py
├── core/
│   ├── llm.py
│   ├── context_builder.py
│   └── decision.py
└── models/
    ├── request.py
    └── response.py
```

## 分层说明

### API 层

`api` 层只负责：

- 接收请求
- 调用 service
- 返回响应

不负责：

- 业务决策
- agent 选择
- 工具选择

### Services 层

`services` 层负责编排业务流程。

当前计划拆成：

- `chat_service`
- `aiops_service`

分别调用：

- `chat_agent`
- `aiops_agent`

如果未来需要多 agent 协作，则把跨 agent 的流程编排放进：

- `coordinator_service`

### Agents 层

`agents` 层中的每个 agent 只负责自己的决策逻辑。

这样以后新增下面这些 agent 时，不会把原来的 service 搅乱：

- `router_agent`
- `retrieval_agent`
- `planner_agent`

### Core 层

`core` 层放稳定抽象，避免后面到处散落重复逻辑：

- `llm.py`：统一模型创建
- `context_builder.py`：统一上下文组装
- `decision.py`：统一决策对象

## 关于多 Agent

当前理解是：

- `chat/rag` 是一条线
- `aiops` 是一条线

它们现在是两套单独的 agent 逻辑，各司其职，还不是多 agent 协作系统。

只有当系统内部出现下面这些行为时，才算进入多 agent：

- 一个 agent 自动把任务交给另一个 agent
- agent 之间传递结构化中间结果
- 多个 agent 围绕同一个任务协作
- 系统内部存在 coordinator 或 router 统一调度

因此当前推荐路线是：

- 先把单 agent 做稳
- 提前把边界画对
- 后续再引入多 agent 协作
