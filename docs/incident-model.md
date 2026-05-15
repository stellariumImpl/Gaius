<!-- docs/incident-model.md -->

# Incident Model v0.1

## 1. 文档目的

本文档用于定义 CTF 运维智能体系统中的 **Incident（事件 / 故障对象）** 模型。

在本系统中：

- **Signal** 表示原始或结构化的运维线索
- **Incident** 表示对一个或多个 Signal 的归纳、聚合与问题表达

Incident 是智能体进入分析、解释、诊断和建议输出阶段时的核心对象。

本文档回答的问题包括：

- 什么情况下 Signal 应组合成 Incident
- Incident 应包含哪些字段
- Incident 如何表达影响范围
- Incident 如何与后续诊断、建议、runbook 关联

---

## 2. 核心原则

## 2.1 Incident 不是原始告警
原始告警通常是某个监控规则触发的结果。  
Incident 则是更高层的问题对象，用来表达“当前真正值得被关注和处理的事”。

例如：

- `cpu_usage_high` 是 Signal
- `platform_performance_degradation` 可能是 Incident

## 2.2 Incident 面向运维决策
Incident 不只是“有什么异常”，还要帮助回答：

- 影响了谁
- 严重程度如何
- 当前是否需要立即处理
- 应该优先从哪里排查

## 2.3 Incident 可以由多个 Signal 组成
一个 Signal 不一定构成 Incident。  
多个看似独立的 Signal，也可能共同构成同一个 Incident。

例如：
- 容器 unhealthy
- HTTP 健康检查失败
- Redis 正常
- 数据库认证失败

这些组合起来，更接近一个单一 Incident：

- `platform_startup_failure`

## 2.4 Incident 必须平台无关
Incident 类型不应写成：
- `gzctf_db_auth_error_incident`
- `ctfd_login_bug_incident`

而应写成：
- `database_authentication_failure`
- `authentication_service_degradation`
- `platform_startup_failure`

具体平台差异应放在适配器和上下文字段中。

---

## 3. Incident 顶层结构

每一个 Incident 至少应包含以下字段：

```json
{
  "incident_id": "inc_001",
  "incident_type": "platform_startup_failure",
  "title": "Platform failed to start because database authentication failed",
  "severity": "critical",
  "status": "open",
  "timestamp": "2026-05-15T15:40:00+08:00",
  "platform_id": "platform_gzctf_01",
  "affected_scope": {},
  "summary": "The platform is unavailable during startup due to database authentication failure.",
  "related_signals": [],
  "suspected_components": [],
  "hypotheses": [],
  "recommended_actions": [],
  "missing_information": []
}
```

---

## 4. 字段定义

## 4.1 incident_id
Incident 的唯一标识。

### 示例
- `inc_001`
- `inc_platform_20260515_001`

---

## 4.2 incident_type
Incident 类型，是最核心字段之一。

### 命名要求
- 平台无关
- 面向问题本质
- 尽量稳定、可枚举

### 示例
- `platform_startup_failure`
- `service_unavailable`
- `database_authentication_failure`
- `cache_dependency_failure`
- `competition_access_failure`
- `challenge_unreachable`
- `performance_degradation`
- `submission_pipeline_failure`

---

## 4.3 title
给人读的短标题。

### 示例
- `Platform startup failed due to database authentication error`
- `Competition page is unreachable during active event`
- `Challenge attachment service is unavailable`

### 说明
`title` 应足够短，适合做列表、通知、工单标题。

---

## 4.4 severity
Incident 严重程度。

### 建议枚举
- `info`
- `low`
- `medium`
- `high`
- `critical`

### 说明
Incident 的 severity 不是单个 Signal 的复制，而是综合后的结果。

### 示例
- 比赛进行中平台不可访问：`critical`
- 比赛未开始时某题附件丢失：`medium`

---

## 4.5 status
Incident 当前状态。

### 建议枚举
- `open`
- `investigating`
- `mitigating`
- `resolved`
- `closed`

### 说明
状态是产品后续管理和协作的重要字段。  
即使第一阶段不做完整工单系统，也建议保留。

---

## 4.6 timestamp
Incident 被创建或确认的时间。

### 示例
- `2026-05-15T15:40:00+08:00`

---

## 4.7 platform_id
表示该 Incident 属于哪个比赛平台实例。

### 示例
- `platform_gzctf_01`

---

## 4.8 affected_scope
表示影响范围。

这是 Incident 与普通异常提示最重要的区别之一。

### 影响范围可能包括
- 全平台
- 某个组件
- 某场比赛
- 某个题目
- 某类用户
- 某个管理功能

### 示例
```json
{
  "scope_type": "platform",
  "competition_ids": ["comp_001"],
  "challenge_ids": [],
  "user_groups": ["all_users"]
}
```

或：

```json
{
  "scope_type": "challenge",
  "competition_ids": ["comp_001"],
  "challenge_ids": ["chal_007"],
  "user_groups": ["participants"]
}
```

---

## 4.9 summary
给人读的摘要，用于快速理解问题本质。

### 示例
- `The platform is currently unavailable because the application cannot authenticate to the database.`
- `The competition is active, but participants cannot access the challenge attachment service.`

---

## 4.10 related_signals
组成该 Incident 的 Signal 列表。

### 示例
```json
[
  "sig_db_auth_fail_001",
  "sig_container_unhealthy_002",
  "sig_http_health_failed_003"
]
```

### 说明
Incident 必须保留与底层 Signal 的可追溯关系。

---

## 4.11 suspected_components
当前怀疑相关的组件列表。

### 示例
```json
[
  "web_main",
  "db_primary"
]
```

### 说明
这是智能体进行归因时的重要中间结果。

---

## 4.12 hypotheses
可能原因列表。

### 示例
```json
[
  "Database password mismatch",
  "Database user permission misconfiguration",
  "Application config file not correctly mounted"
]
```

### 说明
Hypothesis 表达的是“当前合理怀疑”，而不是已经确认的根因。

---

## 4.13 recommended_actions
建议动作列表。

### 示例
```json
[
  "Verify database connection string in appsettings.json",
  "Check whether the database container was initialized with the expected password",
  "Restart the application after correcting configuration"
]
```

### 说明
Incident 进入面向运维决策阶段时，这个字段很关键。

---

## 4.14 missing_information
当前还缺失但有助于确认问题的信息。

### 示例
```json
[
  "Database container initialization history",
  "Recent configuration changes",
  "Application startup logs before failure"
]
```

### 说明
不是所有 Incident 都能立刻下结论。  
明确缺什么信息，本身就是高质量输出的一部分。

---

## 5. Incident 生命周期

一个 Incident 通常会经历以下阶段：

1. `open`
2. `investigating`
3. `mitigating`
4. `resolved`
5. `closed`

### 示例理解

- `open`
  已经发现异常，需要关注

- `investigating`
  已开始收集更多信息和排查

- `mitigating`
  已开始采取止血动作

- `resolved`
  主要问题已恢复

- `closed`
  事件结束，进入复盘或归档

### 当前阶段建议
即使第一阶段产品不做完整状态管理，也建议内部模型保留这一生命周期。

---

## 6. Signal 到 Incident 的关系

## 6.1 一个 Signal 不一定形成 Incident
例如：
- 某次 CPU 短时升高
- 某条单独 warning 日志

这些可能只是噪声，不应立即转为 Incident。

## 6.2 多个 Signal 可以形成一个 Incident
例如：

### Signals
- `db_connection_failed`
- `container_unhealthy`
- `http_healthcheck_failed`

### Incident
- `platform_startup_failure`

---

## 6.3 一个 Incident 可以继续关联新的 Signal
Incident 不是静态对象。

例如平台不可访问时，后续又出现：
- Redis 连接失败
- 题目附件不可访问

这些新 Signal 可能：
- 作为已有 Incident 的补充线索
- 或指向新的独立 Incident

---

## 7. Incident 分类建议

当前建议先从以下几类 Incident 起步：

## 7.1 Platform Availability
平台整体可用性问题。

### 示例
- `platform_startup_failure`
- `service_unavailable`
- `platform_access_failure`

---

## 7.2 Dependency Failure
依赖组件故障。

### 示例
- `database_authentication_failure`
- `database_unreachable`
- `cache_dependency_failure`
- `storage_dependency_failure`

---

## 7.3 Performance Incident
性能类问题。

### 示例
- `performance_degradation`
- `high_latency_incident`
- `resource_pressure_incident`

---

## 7.4 Competition Incident
比赛业务相关问题。

### 示例
- `competition_access_failure`
- `competition_start_failure`
- `scoreboard_update_failure`

---

## 7.5 Challenge Incident
题目层面问题。

### 示例
- `challenge_unreachable`
- `attachment_access_failure`
- `challenge_runtime_failure`

---

## 7.6 Submission Incident
提交链路问题。

### 示例
- `submission_pipeline_failure`
- `flag_validation_failure`
- `submission_delay_incident`

---

## 8. Incident 与输出结构的关系

Incident 应成为后续智能体输出的输入对象。

智能体最终输出可以围绕 Incident 生成：

- 当前现象
- 影响范围
- 可能原因
- 建议排查步骤
- 建议处理动作
- 置信度和信息缺口

也就是说：

- Signal 更适合机器输入
- Incident 更适合进入“解释与决策支持”阶段

---

## 9. 当前实验平台中的典型 Incident 示例

### 示例 1：数据库认证失败导致平台无法启动

#### Related Signals
- `db_connection_failed`
- `container_unhealthy`
- `http_healthcheck_failed`

#### Incident
```json
{
  "incident_type": "platform_startup_failure",
  "severity": "critical",
  "suspected_components": ["web_main", "db_primary"],
  "hypotheses": [
    "Database password mismatch",
    "Database initialization state inconsistent with current configuration"
  ]
}
```

### 示例 2：比赛进行中题目附件不可访问

#### Related Signals
- `attachment_access_error_log`
- `challenge_unreachable`
- `http_404_spike`

#### Incident
```json
{
  "incident_type": "attachment_access_failure",
  "severity": "high",
  "affected_scope": {
    "scope_type": "challenge"
  }
}
```

---

## 10. 当前阶段不做的事

当前阶段不要求：
- 完整自动 Incident 聚合引擎
- 复杂规则 DSL
- 完整工单系统
- 自动根因确认

当前阶段只要求：
- 定义 Incident 结构
- 明确 Signal 和 Incident 的关系
- 为后续智能体输出和适配器设计提供边界

---

## 11. 一句话总结

Incident 是对多个运维 Signal 的结构化归纳结果，  
它是智能体从“看到线索”走向“提供诊断与建议”的关键中间对象。

Signal 面向观察，  
Incident 面向理解与决策。

