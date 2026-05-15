<!-- docs/signal-schema.md -->

# Signal Schema v0.1

## 1. 文档目的

本文档用于定义 CTF 运维智能体系统中的 **Signal（信号）** 模型。

Signal 是产品输入抽象中的核心对象。  
它表示平台在运行过程中产生的、可被采集、观察、分析的结构化线索。

Signal 的目标不是保留所有底层原始数据，而是为后续的：

- 异常识别
- 故障归因
- 影响分析
- 诊断输出
- 智能体推理

提供统一的输入语义。

---

## 2. 设计原则

## 2.1 Signal 优先于平台实现
Signal 必须先是平台无关的抽象，再去适配不同平台来源。

例如：
- GZ::CTF 的登录失败日志
- CTFd 的认证错误日志
- Nginx 的 502 日志

都可以映射成：

- authentication_error
- upstream_unavailable
- login_failure_rate_high

而不是把某个平台的日志文本直接当作产品输入标准。

## 2.2 Signal 优先于原始日志
原始日志和指标是数据源，不是产品的最终输入模型。  
Signal 应当是从原始数据抽取、规整、归类后的结果。

## 2.3 Signal 是“线索”，不是“结论”
Signal 只能表达“发生了什么迹象”，不能直接等同于最终故障判断。  
多个 Signal 可以共同构成一个 Incident。

---

## 3. Signal 顶层结构

每一个 Signal 至少应包含以下字段：

```json
{
  "signal_id": "sig_001",
  "signal_type": "db_connection_failed",
  "category": "health",
  "severity": "high",
  "timestamp": "2026-05-15T15:30:00+08:00",
  "source": "platform_adapter",
  "platform_id": "platform_gzctf_01",
  "component_id": "db_primary",
  "component_type": "database",
  "summary": "Database connection failed during platform startup",
  "payload": {},
  "raw_ref": {},
  "tags": ["startup", "database", "authentication"]
}
```

---

## 4. 字段定义

## 4.1 signal_id
唯一标识一个 Signal。

### 要求
- 全局唯一
- 可用于 trace、日志、事件关联

### 示例
- `sig_001`
- `sig_gzctf_20260515_001`

---

## 4.2 signal_type
Signal 的类型，是最核心字段之一。

### 设计要求
- 使用稳定的、平台无关的命名
- 不直接暴露底层实现细节
- 倾向于表达“可感知问题”或“可观测状态”

### 示例
- `service_unavailable`
- `db_connection_failed`
- `redis_timeout`
- `cpu_usage_high`
- `memory_pressure`
- `login_failure_rate_high`
- `container_restarting`
- `challenge_unreachable`

---

## 4.3 category
Signal 所属类别。

### 当前建议类别
- `health`
- `metrics`
- `logs`
- `events`
- `security`
- `competition`

### 示例
- `db_connection_failed` -> `health`
- `cpu_usage_high` -> `metrics`
- `authentication_error_log` -> `logs`
- `competition_started` -> `competition`

---

## 4.4 severity
表示该 Signal 自身的重要程度，不代表最终 Incident 级别。

### 建议枚举
- `info`
- `low`
- `medium`
- `high`
- `critical`

### 说明
同一个 signal_type 在不同上下文下 severity 可能不同。  
例如：
- 比赛开始前 Web 访问失败：`medium`
- 比赛进行中 Web 访问失败：`critical`

---

## 4.5 timestamp
Signal 发生或被采集的时间。

### 要求
- 使用 ISO 8601 格式
- 包含时区

### 示例
- `2026-05-15T15:30:00+08:00`

---

## 4.6 source
表示 Signal 来源。

### 典型来源
- `platform_adapter`
- `prometheus`
- `docker`
- `log_parser`
- `health_checker`
- `competition_event_stream`
- `manual_report`

### 说明
`source` 表示“由谁产生这个 Signal”，而不是“Signal 最终指向谁”。

---

## 4.7 platform_id
表示 Signal 属于哪个比赛平台实例。

### 示例
- `platform_gzctf_01`
- `platform_ctfd_test`

---

## 4.8 component_id
表示 Signal 关联的组件。

### 示例
- `web_main`
- `db_primary`
- `redis_cache`
- `reverse_proxy`
- `challenge_service_01`

---

## 4.9 component_type
表示组件类别。

### 当前建议枚举
- `web`
- `database`
- `cache`
- `storage`
- `container_runtime`
- `challenge_runtime`
- `proxy`
- `host`
- `application`

---

## 4.10 summary
给人读的简短摘要。

### 示例
- `Platform web service returned repeated 500 responses`
- `Redis connection timeout detected`
- `Competition start event failed`

### 说明
智能体未来可以直接消费这个字段，但不能只依赖它推理。

---

## 4.11 payload
结构化细节字段。

这是 Signal 最重要的扩展位，用于携带该 Signal 特有的信息。

### 示例 1：数据库连接失败
```json
{
  "error_code": "28P01",
  "message": "password authentication failed for user 'postgres'",
  "database_name": "postgres"
}
```

### 示例 2：CPU 过高
```json
{
  "cpu_percent": 96.3,
  "duration_seconds": 420,
  "threshold": 80
}
```

### 示例 3：比赛事件
```json
{
  "competition_id": "comp_001",
  "competition_name": "Spring CTF",
  "event_name": "competition_started"
}
```

---

## 4.12 raw_ref
原始数据引用信息。

### 用途
用于回溯原始日志、指标或事件，不要求总是完整存储原文。

### 示例
```json
{
  "log_file": "/var/log/gzctf/app.log",
  "line_number": 2031
}
```

或：

```json
{
  "metric_name": "container_cpu_usage_seconds_total",
  "query": "rate(...)"
}
```

### 说明
`raw_ref` 是“原始数据位置或查询方式”的抽象，不是原始数据本体。

---

## 4.13 tags
标签数组，用于快速检索与聚类。

### 示例
- `["database", "startup", "authentication"]`
- `["competition", "availability"]`
- `["resource", "cpu", "host"]`

---

## 5. Signal 分类与示例

## 5.1 Health Signals
表示健康状态异常。

### 示例
- `service_unavailable`
- `db_connection_failed`
- `redis_unreachable`
- `container_unhealthy`
- `http_healthcheck_failed`

---

## 5.2 Metrics Signals
表示指标异常。

### 示例
- `cpu_usage_high`
- `memory_pressure`
- `disk_usage_high`
- `http_latency_high`
- `error_rate_high`
- `db_connection_count_high`

---

## 5.3 Log Signals
表示从日志中提取出的异常模式。

### 示例
- `authentication_error_log`
- `startup_config_missing`
- `upstream_timeout_log`
- `challenge_access_error_log`

---

## 5.4 Event Signals
表示平台或基础设施事件。

### 示例
- `competition_started`
- `competition_end_failed`
- `challenge_published`
- `container_restarted`
- `mass_login_failures_detected`

---

## 5.5 Competition Signals
表示和比赛本身强相关的状态信号。

### 示例
- `competition_not_started_but_access_attempted`
- `submission_spike_detected`
- `scoreboard_update_failed`
- `challenge_attachment_unavailable`

---

## 6. 从原始数据到 Signal 的映射

## 6.1 日志 -> Signal
原始日志：

```text
[FTL] 数据库连接失败(28P01: password authentication failed for user "postgres")
```

映射为：

```json
{
  "signal_type": "db_connection_failed",
  "category": "logs",
  "severity": "critical",
  "component_type": "database",
  "summary": "Database authentication failed during startup",
  "payload": {
    "error_code": "28P01",
    "username": "postgres"
  }
}
```

## 6.2 指标 -> Signal
Prometheus 指标显示 CPU 连续 10 分钟 > 90%。

映射为：

```json
{
  "signal_type": "cpu_usage_high",
  "category": "metrics",
  "severity": "high",
  "component_type": "host",
  "summary": "Host CPU usage remained above threshold",
  "payload": {
    "cpu_percent": 92.7,
    "duration_seconds": 600,
    "threshold": 80
  }
}
```

## 6.3 平台事件 -> Signal
比赛开始失败。

映射为：

```json
{
  "signal_type": "competition_start_failed",
  "category": "competition",
  "severity": "critical",
  "component_type": "application",
  "summary": "Competition failed to enter started state",
  "payload": {
    "competition_id": "comp_001"
  }
}
```

---

## 7. 当前阶段不做的事

当前阶段不要求：

- 定义所有 signal_type
- 一次性覆盖所有平台
- 设计最终数据库表结构
- 定义完整告警策略语言

当前阶段只要求：
- 明确信号结构
- 明确分类方式
- 明确未来适配器如何输出 Signal

---

## 8. 与 Incident 的关系

Signal 是输入线索。  
Incident 是对多个 Signal 的归纳结果。

### 一个 Incident 可以由多个 Signal 组成
例如：
- `container_unhealthy`
- `db_connection_failed`
- `http_healthcheck_failed`

可能共同指向：

- `platform_startup_failure`

因此：
- Signal 不应承担完整归因职责
- Incident 不应丢失 Signal 关联关系

---

## 9. 当前实验平台中的适用方式

在当前 GZ::CTF 实验平台上，可以先从以下数据源提取 Signal：

- Docker 容器状态
- GZ::CTF 日志
- PostgreSQL 状态
- Redis 状态
- 主机 CPU / 内存 / 磁盘
- 比赛开始/结束等平台操作事件

但这些数据源只是实验样本，不能定义 Signal 模型本身。

---

## 10. 一句话总结

Signal 是平台无关的、结构化的运维线索对象。

未来无论接入：
- GZ::CTF
- CTFd
- Docker
- Prometheus
- 日志系统

都应优先映射为统一的 Signal，再交给智能体做判断。
