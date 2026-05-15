<!-- docs/output-contract.md -->

# Output Contract v0.1

## 1. 文档目的

本文档用于定义 CTF 运维智能体系统的 **标准输出契约**。

输出契约用于约束智能体在不同场景下的回答结构，使其：

- 便于人理解
- 便于后端处理
- 便于前端展示
- 便于未来多 agent 协作
- 不依赖某一个具体平台

本文档不规定模型内部如何推理，只规定**最终输出应该表达什么**。

---

## 2. 核心原则

## 2.1 输出优先服务运维决策
输出的目标不是“看起来聪明”，而是帮助管理员或运维人员做判断。

输出必须优先回答：

- 发生了什么
- 影响范围是什么
- 可能原因是什么
- 下一步应该查什么
- 当前该不该立刻处理

## 2.2 输出必须结构化
即使最终前端展示成自然语言，内部输出仍应有明确结构。

不能只依赖一整段自由文本。

## 2.3 输出必须允许“不确定”
智能体不应被强迫给出确定结论。

当信息不足时，输出应明确表达：

- 当前只是怀疑
- 缺哪些信息
- 下一步建议补什么数据

## 2.4 输出不能平台写死
输出中不应默认假设：
- 一定是 GZ::CTF
- 一定是 Docker
- 一定有 Prometheus
- 一定有某个固定日志路径

平台特定信息只能出现在上下文字段或证据字段中。

---

## 3. 标准输出结构

标准输出建议至少包含以下部分：

```json
{
  "status": "success",
  "summary": "",
  "current_situation": "",
  "impact_scope": "",
  "suspected_causes": [],
  "investigation_steps": [],
  "suggested_actions": [],
  "confidence": "medium",
  "missing_information": [],
  "evidence": [],
  "related_incident_id": null
}
```

---

## 4. 字段定义

## 4.1 status
表示本次输出的状态。

### 建议枚举
- `success`
- `partial`
- `clarification_needed`
- `failed`

### 说明
- `success`：已形成较完整输出
- `partial`：有初步判断，但信息不完整
- `clarification_needed`：当前必须补充信息
- `failed`：本次处理失败

---

## 4.2 summary
一句话总结当前判断。

### 示例
- `平台当前不可用，初步怀疑数据库认证失败导致服务启动异常。`
- `当前比赛平台可访问，但部分题目附件服务异常。`

### 要求
- 短
- 直接
- 面向人读

---

## 4.3 current_situation
描述“当前发生了什么”。

### 示例
- `GZCTF Web 服务容器处于 unhealthy 状态，HTTP 访问失败，应用日志显示数据库认证错误。`
- `比赛正在进行中，用户可以访问首页，但提交接口错误率显著升高。`

### 说明
这一部分是对现象的结构化描述，不是原因分析。

---

## 4.4 impact_scope
描述影响范围。

### 示例
- `影响整个比赛平台，所有用户均无法正常访问。`
- `仅影响某场比赛中的附件下载功能。`
- `仅影响部分题目实例，不影响平台登录与排行榜。`

### 要求
尽量回答：
- 影响的是平台、比赛、题目还是个别用户
- 影响范围有多大
- 是否处于赛中

---

## 4.5 suspected_causes
可能原因列表。

### 示例
```json
[
  "数据库密码与应用连接串不一致",
  "数据库初始化状态与当前配置不一致"
]
```

### 说明
这是“怀疑”，不是“确认根因”。  
每项都应是可验证的技术假设。

---

## 4.6 investigation_steps
建议优先排查步骤。

### 示例
```json
[
  "检查 appsettings.json 中的数据库连接串配置",
  "确认数据库容器初始化时使用的密码是否与当前连接串一致",
  "查看 PostgreSQL 容器日志是否存在认证失败记录"
]
```

### 要求
- 可执行
- 有顺序
- 尽量从最便宜、最关键的排查动作开始

---

## 4.7 suggested_actions
建议处理动作。

### 示例
```json
[
  "修正数据库连接串或数据库用户密码",
  "如当前为测试环境，可重建数据库数据卷后重新初始化",
  "修复后重启 GZCTF 容器并重新验证健康状态"
]
```

### 说明
这部分偏“怎么处理”，而不是“怎么调查”。

---

## 4.8 confidence
表示当前结论置信度。

### 建议枚举
- `low`
- `medium`
- `high`

### 说明
- `low`：线索少，判断非常初步
- `medium`：已有较强迹象，但未完全确认
- `high`：已有直接证据支持

---

## 4.9 missing_information
当前仍缺失但能显著提升判断质量的信息。

### 示例
```json
[
  "数据库容器首次初始化时的配置",
  "最近一次配置变更记录",
  "GZCTF 容器完整启动日志"
]
```

### 说明
这部分很重要，它让智能体能诚实表达边界，而不是瞎猜。

---

## 4.10 evidence
支撑当前判断的证据列表。

### 建议结构
```json
[
  {
    "type": "log",
    "source": "gzctf",
    "content": "password authentication failed for user \"postgres\""
  }
]
```

### 证据类型示例
- `log`
- `metric`
- `event`
- `health_check`
- `container_status`

### 说明
证据不要求完整原文，但要足够支持当前判断。

---

## 4.11 related_incident_id
如果本次输出是围绕某个 Incident 生成的，可关联对应 Incident ID。

### 示例
- `inc_001`
- `null`

---

## 5. 四种典型输出模式

## 5.1 正常诊断输出
适用于已拿到较完整信息的场景。

```json
{
  "status": "success",
  "summary": "平台当前不可用，初步定位为数据库认证失败。",
  "current_situation": "Web 服务容器 unhealthy，HTTP 请求失败，应用日志显示数据库认证错误。",
  "impact_scope": "影响整个比赛平台，所有用户无法访问。",
  "suspected_causes": [
    "数据库密码与应用连接串不一致",
    "数据库数据卷保留了旧初始化状态"
  ],
  "investigation_steps": [
    "检查 appsettings.json 中的数据库连接串",
    "检查 PostgreSQL 初始化状态",
    "确认数据卷是否复用了旧配置"
  ],
  "suggested_actions": [
    "修正数据库密码配置",
    "如为测试环境，删除旧数据卷并重新初始化",
    "重启 GZCTF 容器后重新检查健康状态"
  ],
  "confidence": "high",
  "missing_information": [],
  "evidence": [
    {
      "type": "log",
      "source": "gzctf",
      "content": "password authentication failed for user \"postgres\""
    }
  ],
  "related_incident_id": "inc_001"
}
```

---

## 5.2 信息不足输出
适用于只能给出初步怀疑的场景。

```json
{
  "status": "partial",
  "summary": "当前存在性能异常，但尚无法确认根因。",
  "current_situation": "CPU 使用率持续偏高，平台响应时间上升。",
  "impact_scope": "可能影响部分用户访问体验。",
  "suspected_causes": [
    "业务流量上升",
    "应用内部高计算任务",
    "数据库查询变慢"
  ],
  "investigation_steps": [
    "查看 CPU 使用率曲线",
    "检查容器资源消耗",
    "检查数据库慢查询情况"
  ],
  "suggested_actions": [
    "先确认是否处于比赛高峰期",
    "暂时保留当前实例日志与监控数据"
  ],
  "confidence": "low",
  "missing_information": [
    "应用日志",
    "数据库查询指标",
    "近 10 分钟访问量变化"
  ],
  "evidence": [],
  "related_incident_id": null
}
```

---

## 5.3 需要澄清输出
适用于必须补充上下文才能继续判断。

```json
{
  "status": "clarification_needed",
  "summary": "当前无法判断问题范围，需要补充平台和现象信息。",
  "current_situation": "用户描述中缺少明确异常现象。",
  "impact_scope": "暂时未知。",
  "suspected_causes": [],
  "investigation_steps": [],
  "suggested_actions": [],
  "confidence": "low",
  "missing_information": [
    "具体平台名称或部署对象",
    "异常发生时间",
    "错误现象或日志片段"
  ],
  "evidence": [],
  "related_incident_id": null
}
```

---

## 5.4 处理失败输出
适用于智能体本身或依赖系统无法完成处理。

```json
{
  "status": "failed",
  "summary": "当前无法完成诊断。",
  "current_situation": "必要的信号数据获取失败。",
  "impact_scope": "未知。",
  "suspected_causes": [],
  "investigation_steps": [],
  "suggested_actions": [
    "检查数据采集链路是否可用",
    "稍后重试"
  ],
  "confidence": "low",
  "missing_information": [
    "监控数据",
    "日志数据"
  ],
  "evidence": [],
  "related_incident_id": null
}
```

---

## 6. 面向不同使用者的展示方式

同一份输出契约可以映射给不同对象：

### 6.1 管理员 / 运维人员
完整显示所有字段：
- 现象
- 影响范围
- 原因
- 排查步骤
- 处理建议
- 证据

### 6.2 前端简化展示
优先展示：
- `summary`
- `impact_scope`
- `suggested_actions`
- `confidence`

### 6.3 多 agent 协作
上层 agent 可以只消费：
- `status`
- `summary`
- `suspected_causes`
- `missing_information`
- `related_incident_id`

---

## 7. 输出风格要求

虽然内部是结构化输出，但对人展示时应遵循以下原则：

- 用中文
- 简洁直接
- 不堆术语
- 不装确定
- 不编造证据
- 不输出“看起来聪明但不可执行”的建议

### 好的风格
- `当前平台不可访问，直接原因是数据库认证失败。`
- `当前更像配置不一致，不像数据库本身宕机。`

### 不好的风格
- `根据复杂系统动力学推断，疑似存在多因素耦合异常。`
- `问题可能很多，需要进一步综合分析。`

---

## 8. 当前阶段不做的事

当前阶段不要求：
- 最终前端展示文案完全固定
- 定义完整国际化输出
- 绑定具体 API 响应格式
- 为每种 Incident 单独定制模板

当前阶段只要求：
- 明确智能体最终应该输出哪些信息
- 避免自由发挥式回答
- 为后续实现提供稳定契约

---

## 9. 与系统实现的关系

该输出契约主要服务于：

- 智能体最终回答结构
- 后端 API 响应结构设计
- 前端渲染逻辑
- 多 agent 间结果传递
- 测试与评估标准

未来无论底层使用：
- 单 agent
- 多 agent
- workflow agent
- RAG + tools
- Prompt routing

都应尽量对齐这一输出契约。

---

## 10. 一句话总结

Output Contract 定义的不是“模型说什么话”，而是：

**一个面向 CTF 运维决策的 AI 智能体，最终必须交付哪些结构化信息。**

它是产品输出层的统一边界。

