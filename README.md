# Gaius

> 面向 CTF 比赛平台运维场景的 AI 智能体实验项目

## 概况

当前项目处于 **`0.1.x` 可运行骨架 + 产品抽象演进阶段**。

这一版已经完成：

- FastAPI 服务启动与健康检查
- `chat` HTTP 接口
- `chat agent` 最小可用链路
- `time_tool` 工具调用
- 基于 `session_id + user_id` 的会话隔离
- 基于 `InMemorySaver` 的基础多轮记忆
- `aiops` 路由与服务骨架
- 面向 CTF 运维智能体的第一版领域模型
- 基于真实 Docker 环境的容器状态采集
- 基于真实 Docker 环境的容器日志采集
- `/api/diagnosis` 真实诊断接口
- `Docker 状态 + 日志上下文 + LLM` 的第一版真实诊断闭环

当前实验平台为：

- 一台 Ubuntu 服务器
- 一个 GZ::CTF 部署实例
- Docker 运行环境

但需要强调：

**GZ::CTF 只是当前实验样本，不是产品定义本身。**

---

## 当前目录结构

```text
/Users/felix/Desktop/Gaius
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── chat.py
│   │   └── aiops.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── chat_agent.py
│   │   └── aiops_agent.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_service.py
│   │   ├── aiops_service.py
│   │   └── coordinator_service.py
│   ├── core/
│   │   ├── llm.py
│   │   ├── context_builder.py
│   │   ├── decision.py
│   │   ├── llm_reasoner.py
│   │   ├── log_context_builder.py
│   │   ├── incident_engine.py
│   │   ├── reasoner.py
│   │   └── output_formatter.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   └── time_tool.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── diagnosis.py
│   │   ├── request.py
│   │   └── response.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── signal.py
│   │   ├── incident.py
│   │   └── output.py
│   └── adapters/
│       ├── __init__.py
│       ├── mapping/
│       │   ├── __init__.py
│       │   └── signal_mapper.py
│       └── signals/
│           ├── __init__.py
│           └── docker_provider.py
│           └── log_provider.py
├── docs/
├── .env
├── pyproject.toml
├── uv.lock
├── README.md
└── test.py
```

---

## 启动方式

```bash
uvicorn app.main:app --reload
```

如果按显式端口启动：

```bash
uvicorn app.main:app --reload --port 9900
```

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

聊天测试：

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"s1","user_id":"u1","question":"现在几点？"}'
```

---

## 当前已实现

### Chat 业务线

当前 `chat` 主线已具备：

- `api/chat.py`：HTTP 入口
- `services/chat_service.py`：业务编排
- `agent/chat_agent.py`：聊天决策与执行
- `tools/registry.py`：统一工具装配
- `tools/time_tool.py`：时间工具
- `core/llm.py`：统一模型创建
- `core/context_builder.py`：统一构造 agent 输入
- `core/decision.py`：决策抽象预留

当前能力包括：

- 基础问答
- 工具调用
- 多轮记忆
- 用户隔离

### AIOps 业务线

当前 `aiops` 主线仍处于 **骨架 + 产品抽象接入阶段**：

- `api/aiops.py`
- `services/aiops_service.py`
- `agent/aiops_agent.py`

当前重点不是继续堆平台特例，而是逐步让这条线围绕统一的：

- `Signal`
- `Incident`
- `AgentOutput`

运转起来。

### Diagnosis 诊断主线

当前项目已经有一条真实可调用的诊断主线：

- `api/diagnosis.py`
- `models/diagnosis.py`
- `services/diagnosis_service.py`
- `adapters/signals/docker_provider.py`
- `adapters/signals/log_provider.py`
- `core/log_context_builder.py`
- `core/llm_reasoner.py`

这条链当前已经能直接对真实服务器上的 Docker 环境做诊断，并返回结构化 `AgentOutput`。

---

## 新增中的产品抽象主线

为了把系统从“针对单个平台写规则”演进为“面向 CTF 运维场景的智能体”，当前已新增第一批抽象。

### 1. 领域模型

- `app/domain/signal.py`
- `app/domain/incident.py`
- `app/domain/output.py`

它们分别定义：

- `Signal`：平台无关的运维线索
- `Incident`：对多个 Signal 的归纳结果
- `AgentOutput`：智能体最终交付的标准输出结构

### 2. 真实环境接入

- `app/adapters/signals/docker_provider.py`
- `app/adapters/signals/log_provider.py`

这层直接从真实 Docker 环境读取容器事实，例如：

- 容器名
- 镜像名
- 运行状态
- 健康状态
- 重启次数
- 最近日志片段

### 3. 当前主线与过渡模块

当前真实运行的诊断主线是：

- `docker_provider.py`
- `log_provider.py`
- `log_context_builder.py`
- `llm_reasoner.py`
- `diagnosis_service.py`
- `/api/diagnosis`

当前更准确的链路是：

**真实 Docker 状态 + 日志上下文 -> LLM 结构化诊断 -> `AgentOutput`**

下面这些模块目前仍保留，但更适合作为过渡实现或 fallback，而不是未来主线：

- `app/adapters/mapping/signal_mapper.py`
- `app/core/incident_engine.py`
- `app/core/output_formatter.py`
- `app/core/reasoner.py`

这些模块当前应视为：

- 冻结模块
- 过渡实现
- fallback / 对照实现

也就是说，后续不再继续往这几处追加新的 case 规则或模板逻辑。

---

## 当前设计原则

### 工程分层原则

- `api` 层：只接收请求和返回响应
- `services` 层：负责编排业务流程
- `agent` 层：负责各自的决策逻辑
- `tools` 层：统一定义与装配工具
- `models` 层：承载请求/响应模型
- `core` 层：放稳定核心能力
- `domain` 层：放产品领域模型
- `adapters` 层：负责真实环境接入与标准化映射

### 产品原则

- 样本平台不等于产品定义
- 不把 GZ::CTF 写死在核心逻辑里
- 不把当前机器环境写死成默认真相
- 真实环境数据应先转化为可供诊断消费的标准化证据
- 当前主线应以 `LLM reasoner` 为中心，而不是继续扩展规则链
- 不继续通过堆 if/else 的方式扩展诊断能力

---

## 当前系统如何推理与规划

当前项目里实际存在两套思路，但运行时主线已经不再主要依赖早期的规则链(`signal_mapper -> incident_engine -> output_formatter`)来生成诊断结果。

当前真实诊断流程大致是：

1. 从 Docker 环境采集容器状态
2. 从 Docker 容器采集最近日志
3. 对日志做有限的上下文压缩
4. 将状态、日志片段和证据候选交给 `llm_reasoner`
5. 由 LLM 输出标准化 `AgentOutput`

因此，当前系统的实际推理方式是：

**证据组织 + LLM 推理**

而不是单纯的：

**规则命中 + 模板输出**

不过需要明确的是，当前系统还没有形成完全独立的“规划层”。
现在“先采什么、看什么、缺什么、下一步做什么”这些能力，仍然分散在：

- `diagnosis_service.py` 的固定编排顺序
- `log_context_builder.py` 的日志筛选规则
- `llm_reasoner.py` 的 prompt 约束

也就是说：

- 推理主线已经存在
- 规划主线还没有被正式抽象出来

后续更合理的方向是逐步演进到：

**providers -> observation bundle -> planning / reasoning -> `AgentOutput`**

---

## 当前阶段判断

当前项目不是“从 0 开始搭 Web 服务”，而是：

**在已有 chat 工程之上，开始补一条面向 CTF 运维智能体的产品抽象主线。**

也就是说，当前最重要的事情不是继续堆：

- 平台特例
- case 规则
- prompt 模板

而是逐步完成：

1. 真实环境信号采集
2. 真实环境日志采集
3. 标准化证据组织
4. 标准化 `AgentOutput`
5. 可替换的推理与规划层

---

## 当前局限

当前这条新增主线虽然已经能跑，但仍有明显局限：

- `signal_mapper.py` 仍是规则映射
- `incident_engine.py` 仍是 case 聚合
- `output_formatter.py` 仍是模板输出
- `reasoner.py` 仍是规则版推理器
- `llm_reasoner.py` 仍然带有 prompt 约束和场景偏置
- `log_context_builder.py` 仍然依赖关键词筛选
- 目前主要只接入了 Docker 状态和 Docker 日志
- 尚未接入 Prometheus / metrics provider
- 尚未引入真正独立的 planning layer
- 尚未引入真正的平台无关 observation bundle

换句话说：

**现在已经验证“诊断主线能跑”，但还没有进入成熟的 observation-driven 智能推理阶段。**

---

## 推荐演进路线

### 第一阶段：保留已有成果
- 保留 `Signal / Incident / AgentOutput`
- 保留真实 `docker_provider` / `log_provider`
- 不再继续扩写更多 case 规则链

### 第二阶段：补充真实信号来源
- 增加健康检查 provider
- 视资源情况接入 Prometheus provider

### 第三阶段：引入推理层
- 从“规则链 + prompt 约束”逐步迁移到
- `observation bundle + planning / reasoning`

### 第四阶段：再考虑更强的智能体能力
- Runbook 匹配
- 可控推理流程
- 多 agent 协作
- 平台适配器扩展

---

## 关于多 Agent

当前理解是：

- `chat` 是一条线
- `aiops` 是一条线

它们现在仍然是两条相对独立的单 agent / 单 workflow 逻辑。  
还不是严格意义上的多 agent 协作系统。

只有当系统内部出现下面这些行为时，才算更强意义上的多 agent：

- 一个 agent 自动把任务交给另一个 agent
- agent 之间传递结构化中间结果
- 不同角色 agent 围绕同一运维任务协作
- coordinator / router 显式调度不同角色

---

## 一句话总结

当前 `Gaius` 已经具备：

- 可运行的 chat 主线
- AIOps 业务骨架
- 第一版 CTF 运维智能体领域模型
- 第一条真实环境信号采集与输出闭环

接下来的重点，不是继续围绕样本平台堆规则，而是：

**把现有骨架逐步演进为面向 CTF 比赛平台运维场景的平台无关 AI 智能体。**
