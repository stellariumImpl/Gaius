<!-- docs/adapter-architecture.md -->

# Adapter Architecture v0.1

## 1. 文档目的

本文档用于定义 CTF 运维智能体系统中的 **适配器架构**。

在本系统中，必须明确区分以下三类职责：

- 平台接入
- 信号采集 / 提供
- 智能分析与输出

本文档的目标是避免系统在接入第一个实验平台后，逐渐演变为平台专属脚本集合。

本文档回答的问题包括：

- GZ::CTF 这样的具体平台应该接在哪一层
- Prometheus、Docker、日志、HTTP 健康检查属于哪一层
- 智能体核心逻辑应该依赖什么抽象
- 未来支持多个 CTF 平台时如何扩展

---

## 2. 核心原则

## 2.1 平台特性不能进入核心逻辑
GZ::CTF、CTFd、自研平台等的特有字段、容器名、日志格式，不应直接进入智能体核心推理逻辑。

正确做法：
- 平台特性留在适配器层
- 适配器输出统一领域对象和 Signal

错误做法：
- 在智能体里直接写 “如果容器名是 gzctf-db 就……”
- 在核心逻辑里直接解析某个平台日志文本格式

---

## 2.2 智能体只依赖通用抽象
智能体核心逻辑应该只依赖这些对象：

- Platform
- Component
- Competition
- Challenge
- Signal
- Incident
- Output Contract

而不是依赖：
- 某个 Prometheus query
- 某个平台日志路径
- 某个固定端口
- 某个容器名称

---

## 2.3 数据源和平台不是一回事
需要严格区分：

- **平台（Platform）**
  表示被管理的比赛系统

- **数据源（Signal Provider）**
  表示从哪里采集观测数据

同一个平台可以有多个数据源：
- Docker
- Prometheus
- 日志文件
- HTTP 检查
- 平台管理 API

同一种数据源也可以服务多个平台。

---

## 2.4 适配器架构必须支持扩展
第一阶段即使只接 GZ::CTF，也必须允许未来接入：
- CTFd
- 自研平台
- 其他 CTF 比赛系统

---

## 3. 总体架构分层

建议系统逻辑分为以下四层：

```text
Platform Layer
Signal Provider Layer
Domain Mapping Layer
Agent Core Layer
```

更具体地说：

```text
具体平台 / 数据源
    ↓
适配器 / Provider
    ↓
统一领域对象 / Signal
    ↓
Incident 分析 / 智能体输出
```

---

## 4. Platform Layer

Platform Layer 表示被管理的目标平台。

### 示例
- GZ::CTF
- CTFd
- 自研 CTF 平台

### 职责
- 提供平台级上下文
- 提供比赛、题目、用户、组件等业务对象信息
- 提供平台管理动作的入口（未来可能）

### 不负责
- 不直接决定 Incident
- 不直接生成最终输出
- 不直接暴露给智能体核心做特殊判断

---

## 5. Signal Provider Layer

Signal Provider Layer 表示信号来源。

它负责从不同观测渠道采集原始数据，并输出结构化 Signal 或中间原始记录。

### 典型 Provider
- `prometheus_provider`
- `docker_provider`
- `log_provider`
- `healthcheck_provider`
- `platform_event_provider`

### 说明
这些 Provider 不属于某个平台本身。  
它们是“观测数据入口”。

例如：
- Docker 状态可用于 GZ::CTF，也可用于其他平台
- Prometheus 指标也同样如此

### 典型输入
- 容器状态
- 主机资源指标
- HTTP 健康检查结果
- 日志行
- 比赛事件流

### 典型输出
- 原始记录
- 结构化 Signal
- 统一事件对象

---

## 6. Domain Mapping Layer

这是适配器架构中最关键的一层。

它负责把：
- 平台特有信息
- 数据源特有信息

映射成：
- 统一领域对象
- 统一 Signal
- 可用于 Incident 分析的标准输入

### 主要职责
1. 平台对象映射
2. 信号对象映射
3. 字段标准化
4. 平台无关化处理

### 示例
原始日志：

```text
[FTL] 数据库连接失败(28P01: password authentication failed for user "postgres")
```

Domain Mapping 后变成：

```json
{
  "signal_type": "db_connection_failed",
  "category": "logs",
  "component_type": "database",
  "summary": "Database authentication failed during startup",
  "payload": {
    "error_code": "28P01",
    "username": "postgres"
  }
}
```

### 说明
Domain Mapping Layer 是未来系统可扩展性的核心。  
没有这一层，平台差异会直接污染智能体。

---

## 7. Agent Core Layer

Agent Core Layer 是智能体核心分析与输出逻辑所在层。

它应该依赖：
- Signal Schema
- Incident Model
- Output Contract
- Domain Model

它不应该依赖：
- 某平台日志原文
- 某平台数据库字段名
- 某个具体 Prometheus 指标命名习惯
- 某个固定容器名称

### 主要职责
- 聚合 Signal
- 形成 Incident
- 生成诊断输出
- 标注置信度
- 明确缺失信息
- 调用 runbook 或建议动作

---

## 8. 推荐的模块划分

从代码结构上，未来建议划分为以下模块：

```text
app/
├── adapters/
│   ├── platform/
│   │   ├── gzctf_adapter.py
│   │   ├── ctfd_adapter.py
│   │   └── base_platform_adapter.py
│   ├── signals/
│   │   ├── docker_provider.py
│   │   ├── prometheus_provider.py
│   │   ├── log_provider.py
│   │   └── healthcheck_provider.py
│   └── mapping/
│       ├── signal_mapper.py
│       ├── incident_mapper.py
│       └── component_mapper.py
├── core/
│   ├── context_builder.py
│   ├── decision.py
│   ├── incident_engine.py
│   └── output_formatter.py
└── ...
```

### 说明
当前阶段不必一次性实现所有模块。  
但架构上建议提前认识到这些边界。

---

## 9. 当前实验平台如何落在架构中

当前实验平台：
- GZ::CTF
- 单机 Docker 部署
- Ubuntu 主机
- PostgreSQL
- Redis

在适配器架构中的位置应该是：

### Platform
- `gzctf_adapter`

### Signal Providers
- `docker_provider`
- `healthcheck_provider`
- 未来可加 `prometheus_provider`
- 未来可加 `log_provider`

### Mapping
- 把 GZ::CTF 容器日志、比赛事件、健康检查结果映射成标准 Signal

### Agent Core
- 不关心它是不是 GZ::CTF，只消费标准 Signal / Incident

---

## 10. 一个完整的数据流示例

## 10.1 原始事实
- GZCTF 容器 unhealthy
- 8080 健康检查失败
- 日志中有数据库认证错误

## 10.2 Provider 层输出
- `docker_provider` 提供容器状态记录
- `healthcheck_provider` 提供 HTTP 失败记录
- `log_provider` 提供错误日志记录

## 10.3 Mapping 层输出
```json
[
  {
    "signal_type": "container_unhealthy"
  },
  {
    "signal_type": "http_healthcheck_failed"
  },
  {
    "signal_type": "db_connection_failed"
  }
]
```

## 10.4 Agent Core 输出
形成 Incident：

- `platform_startup_failure`

生成标准输出：
- 当前现象
- 影响范围
- 可能原因
- 建议排查步骤
- 建议处理动作

---

## 11. 当前阶段推荐的实现顺序

## 第一阶段
先建立：
- Domain Model
- Signal Schema
- Incident Model
- Output Contract

## 第二阶段
先接一个平台样本：
- `gzctf_adapter`

先接两个信号来源：
- `docker_provider`
- `healthcheck_provider`

## 第三阶段
补映射层：
- `signal_mapper`

## 第四阶段
让智能体核心只消费统一 Signal，而不直接碰底层原始数据

---

## 12. 当前阶段不做的事

当前阶段不要求：
- 一次性支持多平台
- 完整平台管理 API
- 完整告警聚合引擎
- 自动修复动作
- 所有 Provider 都接齐

当前阶段只要求：
- 架构上把平台层、Provider 层、Mapping 层、Agent Core 层分开
- 保证未来不被第一个平台锁死

---

## 13. 一句话总结

适配器架构的核心目标是：

**让具体平台和具体观测数据源，先映射成统一领域对象与 Signal，再交给智能体做分析。**

这样产品才是：
- 面向 CTF 运维场景的智能体系统

而不是：
- 某个平台的定制脚本集合
