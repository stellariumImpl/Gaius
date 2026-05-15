<!-- docs/runbook-model.md -->

# Runbook Model v0.1

## 1. 文档目的

本文档用于定义 CTF 运维智能体系统中的 **Runbook（排障与处理知识模型）**。

在本系统中：

- **Signal** 表示原始或结构化线索
- **Incident** 表示归纳后的问题对象
- **Runbook** 表示围绕某类问题的排查步骤、确认方法、止血动作与恢复动作

Runbook 的存在，是为了让智能体不仅能“解释问题”，还能够：

- 给出更稳定的排查路径
- 输出更可执行的建议
- 沉淀运维经验
- 在未来支持半自动化处理和多 agent 协作

---

## 2. 核心原则

## 2.1 Runbook 是知识资产，不是临时回答
Runbook 不应只是某次回答中的自然语言片段，而应是可复用、可维护、可版本化的知识结构。

正确做法：
- 为常见 Incident 沉淀标准排查流程
- 让智能体输出引用或实例化 Runbook

错误做法：
- 每次都由模型即兴生成完全不同的处理路径
- 把排查经验散落在 prompt、日志和脑补里

---

## 2.2 Runbook 面向“问题类型”，不是单一平台细节
Runbook 首先应围绕通用 Incident 类型建立，例如：

- `database_authentication_failure`
- `service_unavailable`
- `performance_degradation`
- `attachment_access_failure`

而不是直接围绕：
- GZ::CTF 某个固定容器名
- 某台特定服务器的目录结构

平台特定差异应作为上下文参数进入 Runbook，而不是写死在模型中。

---

## 2.3 Runbook 优先输出步骤，不优先输出结论
在运维场景中，很多问题无法一步确认根因。  
Runbook 的价值首先在于提供“下一步如何查”，而不是强行给出最终答案。

---

## 2.4 Runbook 必须区分排查、止血、恢复、预防
很多系统会把“怎么查”“怎么先恢复”“怎么彻底修”“怎么防止再发生”混成一段话。

Runbook 必须把这些层次区分开。

---

## 3. Runbook 顶层结构

每一个 Runbook 至少应包含以下字段：

```json
{
  "runbook_id": "rb_001",
  "incident_type": "database_authentication_failure",
  "title": "数据库认证失败排查手册",
  "scope": "platform",
  "severity_hint": "critical",
  "applicability": [],
  "diagnosis_steps": [],
  "confirmation_checks": [],
  "mitigation_actions": [],
  "recovery_actions": [],
  "prevention_actions": [],
  "required_inputs": [],
  "notes": []
}
```

---

## 4. 字段定义

## 4.1 runbook_id
Runbook 唯一标识。

### 示例
- `rb_001`
- `rb_db_auth_failure_v1`

---

## 4.2 incident_type
该 Runbook 主要对应哪类 Incident。

### 示例
- `database_authentication_failure`
- `platform_startup_failure`
- `performance_degradation`
- `challenge_unreachable`

### 说明
一个 Incident 类型可以有一个主 Runbook，也可以有多个变体 Runbook。

---

## 4.3 title
Runbook 标题。

### 示例
- `数据库认证失败排查手册`
- `平台启动失败排障手册`
- `比赛进行中服务不可用应急手册`

---

## 4.4 scope
适用范围。

### 建议枚举
- `platform`
- `component`
- `competition`
- `challenge`
- `submission_pipeline`

### 说明
用于帮助系统理解这个 Runbook 更适合处理哪一层问题。

---

## 4.5 severity_hint
该类问题通常对应的严重程度提示。

### 示例
- `medium`
- `high`
- `critical`

### 说明
这不是最终 Incident 级别，只是经验性参考。

---

## 4.6 applicability
适用条件。

### 示例
```json
[
  "日志中存在数据库认证失败关键字",
  "平台启动阶段无法连接数据库",
  "Web 服务 unhealthy 且数据库容器正常运行"
]
```

### 说明
该字段用于帮助判断是否应该套用这个 Runbook。

---

## 4.7 diagnosis_steps
建议排查步骤。

这是 Runbook 的核心字段之一。

### 示例
```json
[
  "检查应用配置文件中的数据库连接串",
  "确认数据库用户、密码、数据库名是否一致",
  "检查数据库容器初始化时使用的环境变量",
  "查看数据库容器日志中的认证失败记录"
]
```

### 说明
这些步骤是“怎么查”，不是“怎么修”。

---

## 4.8 confirmation_checks
用于确认怀疑是否成立的检查项。

### 示例
```json
[
  "使用当前连接串手动连接数据库验证是否成功",
  "确认 PostgreSQL 中该用户是否存在并可登录",
  "确认数据库数据卷是否保留了旧初始化状态"
]
```

### 说明
这一层用于把“怀疑”变成“确认”或“排除”。

---

## 4.9 mitigation_actions
止血动作。

止血动作的目标不是彻底修复，而是尽快降低影响。

### 示例
```json
[
  "若为测试环境，可临时重建数据库数据卷并重新初始化",
  "在比赛未开始前优先恢复平台启动能力",
  "临时通知管理员暂停外部访问直到配置修复完成"
]
```

### 说明
止血动作通常与时间压力相关，尤其适用于赛中环境。

---

## 4.10 recovery_actions
恢复动作。

恢复动作的目标是让服务回到正常状态。

### 示例
```json
[
  "修正数据库连接配置后重启应用容器",
  "重新验证 Web 服务健康状态",
  "验证管理员登录、比赛页面和题目访问是否恢复正常"
]
```

### 说明
恢复动作通常发生在初步定位或止血之后。

---

## 4.11 prevention_actions
预防动作。

用于避免同类问题再次发生。

### 示例
```json
[
  "将数据库连接配置纳入发布前检查项",
  "初始化数据库后固化环境变量与配置文件版本",
  "为平台启动失败建立自动健康检查告警"
]
```

### 说明
这部分对产品长期价值很重要，也是智能体从“排障助手”走向“运维助手”的关键。

---

## 4.12 required_inputs
执行或应用该 Runbook 需要哪些输入。

### 示例
```json
[
  "应用配置文件",
  "数据库连接串",
  "数据库容器日志",
  "平台启动日志"
]
```

### 说明
该字段可以和 Output Contract 中的 `missing_information` 对齐。

---

## 4.13 notes
补充说明。

### 示例
```json
[
  "测试环境允许删除数据卷，正式比赛环境需谨慎操作",
  "若问题发生在赛中，应优先考虑止血与可用性恢复"
]
```

---

## 5. Runbook 的四段式结构

当前建议每个 Runbook 至少覆盖以下四个层次：

1. **排查**
2. **确认**
3. **止血**
4. **恢复**
5. **预防**

这五层虽然相关，但不应混写。

---

## 6. 示例：数据库认证失败 Runbook

```json
{
  "runbook_id": "rb_db_auth_failure_v1",
  "incident_type": "database_authentication_failure",
  "title": "数据库认证失败排查手册",
  "scope": "platform",
  "severity_hint": "critical",
  "applicability": [
    "应用日志中出现 password authentication failed",
    "平台在启动阶段无法完成数据库连接"
  ],
  "diagnosis_steps": [
    "检查 appsettings.json 中的数据库连接串",
    "确认数据库用户名、密码、数据库名是否与实际初始化配置一致",
    "查看数据库容器日志是否存在认证失败记录"
  ],
  "confirmation_checks": [
    "使用当前连接串手动连接数据库验证是否成功",
    "确认数据库数据卷是否保留旧初始化状态"
  ],
  "mitigation_actions": [
    "若当前为测试环境，可删除数据库数据卷并重新初始化",
    "若当前为赛中环境，避免直接删除数据卷，优先核对密码配置"
  ],
  "recovery_actions": [
    "修正连接配置后重启 GZCTF 应用容器",
    "验证平台首页和管理员登录功能恢复正常"
  ],
  "prevention_actions": [
    "将数据库配置纳入部署前检查表",
    "保留初始化配置记录，避免环境变量与数据卷状态不一致"
  ],
  "required_inputs": [
    "应用配置文件",
    "数据库连接串",
    "数据库容器日志"
  ],
  "notes": [
    "测试环境和正式环境的推荐动作不同",
    "数据卷删除属于高风险动作，不应默认推荐"
  ]
}
```

---

## 7. Runbook 与智能体的关系

Runbook 不等于智能体最终回答。  
Runbook 更像是智能体生成回答时可调用的知识模板和步骤资产。

### 智能体可以基于 Runbook 做什么
- 选择适合的排查路径
- 给出更稳定的建议
- 说明当前为什么建议先查某一步
- 根据上下文裁剪步骤
- 区分测试环境与赛中环境

### 智能体不应做什么
- 盲目照搬全部步骤
- 不区分当前上下文直接输出标准模板
- 忽略缺失信息和风险等级

---

## 8. Runbook 与 Incident 的关系

一个 Incident 可以：
- 对应一个主 Runbook
- 对应多个候选 Runbook
- 当前没有匹配 Runbook，只能给经验性输出

### 典型流程
1. Signal 被聚合为 Incident
2. 根据 incident_type 匹配 Runbook
3. 智能体结合当前上下文选择或裁剪 Runbook
4. 输出建议动作和排查步骤

---

## 9. Runbook 与平台适配器的关系

Runbook 不直接依赖某个平台，但可以通过上下文参数做平台特化。

例如：
- 同样是 `service_unavailable`
- 在 GZ::CTF 中可能优先看 Web 容器和数据库
- 在 CTFd 中可能优先看 Flask / Gunicorn / Redis

因此：
- 平台差异来自适配层和上下文
- Runbook 本身保持平台无关

---

## 10. 当前阶段推荐的第一批 Runbook

建议优先定义以下几类：

1. `database_authentication_failure`
2. `platform_startup_failure`
3. `service_unavailable`
4. `performance_degradation`
5. `challenge_unreachable`
6. `attachment_access_failure`
7. `submission_pipeline_failure`

这些问题既通用，又非常容易在比赛平台中出现。

---

## 11. 当前阶段不做的事

当前阶段不要求：
- 一次性写完所有 Runbook
- 构建复杂规则引擎
- 实现自动执行修复动作
- 建立完整工单闭环

当前阶段只要求：
- 明确 Runbook 是独立知识资产
- 定义其标准结构
- 为未来的 Incident -> Runbook -> Output 链路做好准备

---

## 12. 一句话总结

Runbook 是智能体系统中将“异常理解”转化为“可执行运维建议”的核心知识资产。

Signal 让系统看到问题，  
Incident 让系统理解问题，  
Runbook 让系统知道下一步怎么做。

