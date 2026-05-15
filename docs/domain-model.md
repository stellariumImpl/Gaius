<!-- docs/domain-model.md -->

# CTF 运维智能体领域模型 v0.1

## 1. 文档目的

本文档用于定义「CTF 比赛服务器运维 AI 智能体」的产品级抽象边界。

它的目标不是描述某一个具体平台的实现细节，而是回答以下问题：

- 智能体面向的对象是什么
- 智能体接收哪些输入
- 智能体输出什么结果
- 哪些概念是通用的
- 哪些概念只是某个平台的特例

本文档优先服务于：

- 产品边界定义
- 架构设计
- 代码抽象
- 后续平台适配

本文档不以某个具体平台为中心。  
GZ::CTF、CTFd、自研平台等都应被视为该模型下的具体实例，而不是模型本身。

---

## 2. 产品定义

本产品是一个面向 **CTF 比赛平台运维场景** 的 AI 智能体系统。

它的核心能力不是“通用聊天”，而是围绕比赛平台的运行状态、异常行为、排障过程和管理决策，提供：

- 状态理解
- 风险识别
- 故障解释
- 排查建议
- 处理建议
- 赛时辅助

该产品的定位更接近：

- 运维 Copilot
- 比赛平台巡检助手
- 赛时异常诊断助手

而不是：

- 通用聊天机器人
- 某个平台专属脚本
- 单纯的告警转发器

---

## 3. 核心设计原则

### 3.1 平台无关
产品不能依赖单一平台的实现细节进行建模。

正确做法：
- 抽象出通用对象
- 为具体平台提供适配器

错误做法：
- 将 GZ::CTF 的字段、容器名、日志格式直接写入核心逻辑

### 3.2 信号先于平台细节
产品首先关心的是“系统发出了哪些信号”，而不是“某个系统具体怎么实现”。

例如：
- CPU 飙高
- 登录异常
- 服务不可用
- 比赛未开始但用户无法进入
- 提交接口错误率升高

这些都是通用问题信号。

### 3.3 输出必须面向运维决策
产品输出不是原始监控数据的复述，而是要支持运维或管理员做决策。

输出应回答：
- 发生了什么
- 影响了谁
- 可能是什么原因
- 下一步应该查什么
- 当前是否需要立即处理

### 3.4 实验平台不是产品边界
GZ::CTF 和当前服务器环境仅是实验样本，不应反向定义产品范围。

---

## 4. 核心领域对象

## 4.1 Platform
表示一个被管理的 CTF 比赛平台。

一个 Platform 是产品观测和分析的顶层对象。

Platform 可以是：
- GZ::CTF
- CTFd
- 自研平台
- 未来其他比赛平台

Platform 不应直接等同于某一个 Docker 容器或某一个服务进程。

### Platform 典型属性
- platform_id
- platform_type
- platform_name
- deployment_mode
- environment
- base_url

---

## 4.2 Platform Component
表示平台中的组成部分。

一个平台通常由多个组件构成，例如：
- Web 服务
- 数据库
- Redis
- 文件存储
- 容器调度服务
- 题目运行环境
- 反向代理
- 指标采集组件

### Component 典型属性
- component_id
- component_type
- component_name
- health_status
- dependency_relations

### 说明
某个具体平台的组件可能不同，但组件这个概念本身应保持稳定。

---

## 4.3 Competition
表示比赛本身。

平台承载比赛，因此比赛不是普通业务对象，而是运维上下文的重要组成部分。

### Competition 典型属性
- competition_id
- competition_name
- start_time
- end_time
- status
- participant_count
- challenge_count

### 说明
比赛状态直接影响运维判断。
例如：
- 比赛未开始时访问失败，影响等级与赛中不同
- 赛中登录故障通常比赛后维护故障更严重

---

## 4.4 Challenge
表示题目。

题目是比赛中的业务单元，不同题目类型会产生不同运维压力。

例如：
- 静态题
- 附件题
- Web 题
- 容器动态题
- 依赖外部服务的题

### Challenge 典型属性
- challenge_id
- challenge_name
- challenge_type
- deployment_type
- visibility_status
- runtime_dependency

### 说明
第一阶段即使不使用动态容器题，Challenge 仍然是业务分析的一部分。

---

## 4.5 User / Team
表示参赛用户或战队。

### User / Team 典型属性
- user_id / team_id
- role
- status
- login_state
- recent_activity

### 说明
某些异常是平台全局故障，某些异常只影响个别用户或战队。  
因此用户/战队是故障影响范围分析的重要对象。

---

## 4.6 Signal
表示平台发出的观测信号。

Signal 是产品输入建模中最重要的概念之一。

Signal 可以来自：
- metrics
- logs
- health checks
- container status
- competition events
- platform events
- user behavior patterns

### Signal 典型属性
- signal_id
- signal_type
- source
- timestamp
- severity
- payload
- related_component

### Signal 类型示例
- cpu_usage_high
- memory_pressure
- db_connection_failed
- login_error_rate_high
- challenge_unreachable
- container_restarting
- redis_timeout
- competition_start_failed

### 说明
Signal 是平台无关的抽象。  
不同平台可以通过不同适配器产生相同类型的 Signal。

---

## 4.7 Incident
表示一个需要关注或处理的异常事件。

Incident 不是原始信号，而是对多个信号或异常现象的归纳。

### Incident 典型属性
- incident_id
- incident_type
- title
- severity
- affected_scope
- related_signals
- suspected_components
- status

### Incident 示例
- 比赛平台整体不可用
- 登录功能异常
- 某题访问失败
- 数据库连接异常
- 平台响应显著变慢

### 说明
Signal 是输入，Incident 是智能体理解后的问题对象。

---

## 4.8 Runbook
表示可执行或可参考的排障流程与处理经验。

### Runbook 典型属性
- runbook_id
- incident_type
- prerequisite_signals
- diagnosis_steps
- mitigation_actions
- recovery_actions

### 说明
Runbook 是未来产品中非常重要的知识资产，既可以来自人工整理，也可以来自历史经验沉淀。

---

## 5. 输入模型

产品未来接收的输入应被抽象为以下几类，而不是直接绑定某个平台实现。

## 5.1 Health Signals
表示组件是否活着、是否可访问。

例如：
- HTTP 健康检查失败
- 容器 unhealthy
- 端口不可达
- 依赖服务连接失败

## 5.2 Metrics Signals
表示时序资源或业务指标。

例如：
- CPU
- 内存
- 磁盘
- 请求量
- 错误率
- 延迟
- 数据库连接数

## 5.3 Log Signals
表示结构化或非结构化日志中提取的异常模式。

例如：
- 数据库认证失败
- Redis 超时
- 题目访问 500
- 平台配置缺失

## 5.4 Event Signals
表示业务事件或平台事件。

例如：
- 比赛开始
- 用户大量登录失败
- 某题被下线
- 题目附件上传失败
- 容器频繁重启

---

## 6. 输出模型

产品输出必须适合赛时运维和管理者理解与决策。

标准输出建议包含以下部分：

### 6.1 Current Situation
当前发生了什么。

### 6.2 Impact Scope
影响范围是什么。

### 6.3 Suspected Causes
可能原因有哪些。

### 6.4 Investigation Steps
建议先查什么。

### 6.5 Suggested Actions
建议采取什么动作。

### 6.6 Confidence / Missing Information
当前判断的置信度如何，还缺什么信息。

---

## 7. 平台适配器原则

具体平台不应直接进入核心逻辑，而应通过适配器接入。

例如未来可以有：

- gzctf_adapter
- ctfd_adapter
- custom_platform_adapter

适配器职责：
- 从平台读取数据
- 将平台特有字段映射为通用领域对象
- 输出统一格式的 Signal / Component / Competition 信息

适配器不应负责：
- 运维决策
- 智能分析
- 输出文本生成

---

## 8. 当前实验平台的定位

当前实验平台为：
- 一台 Ubuntu 服务器
- 一个 GZ::CTF 部署实例

该实验平台的作用是：
- 验证产品抽象是否可落地
- 提供真实可观测对象
- 构造故障与赛时场景

该实验平台不应被视为：
- 产品定义本身
- 唯一支持的平台
- 核心逻辑可以写死的平台

---

## 9. 当前阶段建议

当前阶段建议优先完成：

1. 让平台稳定运行
2. 梳理平台组件与观测点
3. 识别最关键的 Signal 类型
4. 形成第一版 Incident 分类
5. 再开始设计智能体与平台适配器

---

## 10. 一句话总结

本产品不是为某个具体 CTF 平台写的专属脚本，而是一个面向 **CTF 比赛服务器运维场景** 的 AI 智能体系统。

GZ::CTF 只是当前实验平台，  
真正应该被沉淀的是：

- 通用领域对象
- 通用输入信号
- 通用故障模型
- 通用输出结构
- 通用适配器边界
