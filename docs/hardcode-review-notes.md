# Hardcode Review Notes

## 1. 文档目的

本文档用于盘点当前 `Gaius` 项目中已经出现的：

- 结构性硬编码
- 数据源/环境硬编码
- 规则型硬编码
- Prompt/推理约束硬编码

本文档的目标不是简单批评“有硬编码”，而是帮助后续评审者判断：

1. 哪些硬编码是合理的产品契约
2. 哪些硬编码只是阶段性实现约束
3. 哪些硬编码已经在把系统收缩成当前样本场景的专家系统
4. 哪些模块应保留
5. 哪些模块应冻结
6. 哪些模块应重构

---

## 2. 当前诊断主线

当前 `/api/diagnosis` 的真实主线是：

1. `docker_provider.py`
2. `signal_mapper.py`
3. `log_provider.py`
4. `log_context_builder.py`
5. `llm_reasoner.py`
6. `diagnosis_service.py`
7. `api/diagnosis.py`

当前仍存在但已不应继续作为主线扩展的模块：

1. `incident_engine.py`
2. `output_formatter.py`
3. `reasoner.py`

---

## 3. 结论摘要

当前代码中的硬编码可以分成四类：

### 3.1 合理的结构约束

这类硬编码多数可以保留：

- `SignalCategory`
- `Severity`
- `IncidentStatus`
- `OutputStatus`
- `Confidence`
- `Evidence.type`
- `AgentOutput` 字段结构

这些属于：

- 领域模型约束
- 输出契约约束
- 产品词汇表约束

它们不是当前样本平台特例，不应被视为主要问题。

### 3.2 阶段性实现约束

这类硬编码当前可接受，但未来应逐步抽象：

- 诊断主线只看 Docker 状态
- 诊断主线只看 Docker 日志
- 默认 `tail=50`
- 只支持 `platform_id`
- `DiagnosisService` 固定采集顺序

这些问题的本质是：

- 当前系统仍只覆盖少量真实数据源
- 当前编排方式仍围绕当前实验平台优化

### 3.3 规则型 case 硬编码

这是当前最需要重点关注的部分：

- `signal_mapper.py`
- `incident_engine.py`
- `output_formatter.py`
- `reasoner.py`

这些模块中，已经出现了：

- `if signal_type == ...`
- `if incident_type == ...`
- 某种异常 -> 某种固定结论
- 某种 incident -> 某套固定文案

这类硬编码如果继续扩写，会把系统演进成：

**GZ::CTF + Docker + 当前样本故障集 的专家系统**

而不是平台无关的 CTF 运维智能体。

### 3.4 Prompt/推理约束硬编码

`llm_reasoner.py` 和 `log_context_builder.py` 已经摆脱了纯规则系统，但仍然存在明显的当前场景收敛：

- Prompt 明确围绕当前运维场景组织上下文
- 日志筛选关键词明显受当前故障样本影响
- evidence candidates 结构依赖当前 signal vocabulary

它们虽然优于硬规则，但还没有完全做到“平台无关 + 中立 observation 驱动”。

---

## 4. 模块级盘点

## 4.1 `app/domain/signal.py`

### 当前硬编码

- `SignalCategory` 固定为：
  - `health`
  - `metrics`
  - `logs`
  - `events`

- `Severity` 固定为：
  - `info`
  - `low`
  - `medium`
  - `high`
  - `critical`

### 硬编码性质

这是**结构性硬编码 / 领域约束**。

### 是否合理

总体合理。

### 风险

- 类别枚举未来可能需要扩展
- 当前 `Signal` 字段比较少，后面可能需要补：
  - `platform_id`
  - `component_id`
  - `raw_ref`
  - `tags`

### 建议

- 保留
- 视后续真实场景扩展字段
- 不视为主要硬编码风险

---

## 4.2 `app/domain/incident.py`

### 当前硬编码

- `IncidentStatus` 固定为：
  - `open`
  - `investigating`
  - `mitigating`
  - `resolved`
  - `closed`

### 硬编码性质

这是**结构性硬编码 / 生命周期约束**。

### 是否合理

合理。

### 风险

- 当前 `Incident` 模型较轻，未来可能需要：
  - `affected_scope`
  - `hypotheses`
  - `suspected_components`
  - `missing_information`

### 建议

- 保留
- 作为产品领域模型继续演进

---

## 4.3 `app/domain/output.py`

### 当前硬编码

- `OutputStatus`
- `Confidence`
- `Evidence.type`
- `AgentOutput` 的完整字段结构

### 硬编码性质

这是**输出契约硬编码 / 结构约束**。

### 是否合理

合理，而且应尽量稳定。

### 风险

- `Evidence.type` 未来可能不够
- 当前字段结构适合第一版，但可能需要补充：
  - `observations`
  - `recommended_next_data_sources`
  - `reasoning_notes`

### 建议

- 保留
- 继续作为标准输出层，不建议轻易推翻

---

## 4.4 `app/adapters/signals/docker_provider.py`

### 当前硬编码

- 数据源固定为 Docker CLI
- 读取方式固定为：
  - `docker ps -a -q`
  - `docker inspect`

- 当前固定提取字段：
  - `container_id`
  - `container_name`
  - `image`
  - `status`
  - `health`
  - `restart_count`

### 硬编码性质

这是**数据源/环境硬编码**，不是 case 规则。

### 是否合理

当前合理。

### 风险

- 当前只适合 Docker 部署环境
- 非 Docker 平台无法复用
- 后续如果引入 Kubernetes，这层需要新 provider

### 建议

- 保留
- 未来增加并列 provider，而不是强改当前 provider

---

## 4.5 `app/adapters/signals/log_provider.py`

### 当前硬编码

- 日志读取固定走 `docker logs`
- 固定参数：
  - 单容器读取
  - `tail=N`

### 硬编码性质

这是**数据源/环境硬编码**，不是主要 case 规则。

### 是否合理

当前合理。

### 风险

- 只适用于 Docker 容器日志
- 后续如果日志走文件、Loki、ELK，需要新增 provider

### 建议

- 保留
- 不要在 provider 层做诊断逻辑

---

## 4.6 `app/adapters/mapping/signal_mapper.py`

### 当前硬编码

当前固定规则：

1. `status != "running"` -> `container_not_running`
2. `health == "unhealthy"` -> `container_unhealthy`
3. `restart_count > 0` -> `container_restarted`

### 硬编码性质

这是**事实标准化层硬编码**。

它仍然属于规则，但更接近：

- 数据归类
- 事实标签化

而不是最终诊断结论。

### 是否合理

**部分合理，但必须冻结边界。**

### 风险

- 如果继续往下写更多映射规则，容易变成隐性专家系统
- 当前的 `signal_type` 已经不是完全中立 observation，而是带有一定结论味道

### 建议

- 允许保留当前这 3 条规则
- 不建议继续扩展为大量诊断型 signal 规则
- 这层应限制在“基础事实归类”

---

## 4.7 `app/core/log_context_builder.py`

### 当前硬编码

固定关键词列表：

- `FTL`
- `ERR`
- `WRN`
- `error`
- `failed`
- `exception`
- `shutdown`
- `authentication failed`
- `password authentication failed`
- `received fast shutdown request`

规则：

- 命中关键词 -> 保留
- 否则保留最后几行

### 硬编码性质

这是**日志筛选规则硬编码**。

### 是否合理

当前可接受，但明显带有当前样本故障偏置。

### 风险

- 当前关键词明显偏向：
  - 数据库认证失败
  - shutdown
- 对其他故障类型可能不敏感
- 容易把当前样本故障模式固化成“默认重要日志”

### 建议

- 保留当前实现作为第一版
- 明确它属于“上下文压缩策略”，不是诊断策略
- 后续考虑：
  - 配置化关键词
  - 多策略压缩
  - observation-first 组织方式

---

## 4.8 `app/core/incident_engine.py`

### 当前硬编码

固定规则：

1. `container_unhealthy` -> `service_health_degradation`
2. `container_not_running` -> `service_unavailable`
3. `只有 container_restarted` -> `container_restart_detected`

### 硬编码性质

这是**强规则诊断层硬编码**。

### 是否合理

只适合作为：

- 过渡实现
- 演示实现
- 回归测试用实现

不适合作为未来主线。

### 风险

- 已经在替模型做问题归因
- 对上下文不敏感
- 随 case 增长会快速膨胀

### 建议

- 冻结
- 不再扩展
- 从未来主线中降级

---

## 4.9 `app/core/output_formatter.py`

### 当前硬编码

按 `incident_type` 固定输出：

- 固定 `summary`
- 固定 `suspected_causes`
- 固定 `investigation_steps`
- 固定 `suggested_actions`

### 硬编码性质

这是**强规则模板硬编码**。

### 是否合理

只适合作为：

- 过渡实现
- 对照实现

不适合作为主线。

### 风险

- 输出脱离实时证据
- 极易演进为 case 模板库
- 会把系统变成规则专家系统

### 建议

- 冻结
- 不再扩展
- 不建议作为主线路径继续使用

---

## 4.10 `app/core/reasoner.py`

### 当前硬编码

固定入口逻辑：

1. 无 signal -> `failed`
2. `container_not_running` -> `_reason_service_unavailable`
3. `container_unhealthy` -> `_reason_health_degradation`
4. 只有 `container_restarted` -> `_reason_restart_observation`

### 硬编码性质

这是**收口后的规则诊断层硬编码**。

它比 `incident_engine.py + output_formatter.py` 分散规则要好，
但本质上仍然是 case 规则。

### 是否合理

当前只适合：

- smoke test
- fallback
- 演示链路

### 风险

- 容易被误认为“统一推理层已完成”
- 实际仍然是硬规则诊断

### 建议

- 冻结
- 降级为 fallback / smoke-test implementation
- 不建议继续扩展

---

## 4.11 `app/core/llm_reasoner.py`

### 当前硬编码

分成几部分：

#### A. Prompt 结构写死
- 固定“CTF 比赛平台运维”角色描述
- 固定 JSON schema
- 固定“不准编造”的规则
- 固定 `health = null` 时的表述约束

#### B. Evidence candidates 构建规则
- `container_restarted` -> `event evidence`
- `container_unhealthy` -> `health_check evidence`
- `container_not_running` -> `container_status evidence`
- 日志上下文每一行 -> `log evidence`

#### C. 输出收敛规则
- fenced code block 提取
- `evidence` 不存在则补空
- `evidence` 最多截断到 8 条

### 硬编码性质

这是**Prompt 约束 + 证据组织硬编码**。

### 是否合理

其中一部分合理：

- JSON schema
- 不编造
- evidence candidates 限制
- 最小输出后处理

其中一部分仍然偏向当前样本：

- 当前上下文组织仍围绕 Docker + 容器重启 + 日志异常
- evidence 组织强依赖当前 signal vocabulary

### 风险

- 仍然可能过拟合当前平台与当前故障样本
- 还没有做到“中立 observation bundle 驱动”
- Prompt 继续膨胀会变成新的隐性规则系统

### 建议

- 保留，作为当前主线
- 但应视为“第一版 LLM 推理层”，不是终局设计
- 后续重点改造方向应是：
  - observation bundle
  - 更中立的 evidence grouping
  - 更少预解释、更多证据驱动

---

## 4.12 `app/services/diagnosis_service.py`

### 当前硬编码

固定编排顺序：

1. 读取全部容器快照
2. 转成 `Signal`
3. 提取全部容器名
4. 读取全部容器最近日志
5. 压缩日志上下文
6. 调用 `llm_reasoner`

### 硬编码性质

这是**编排层实现硬编码**。

### 是否合理

当前合理，但显然还是第一版。

### 风险

- 默认“诊断 = Docker 状态 + 所有容器日志”
- 后续加入：
  - health check
  - Prometheus
  - 平台事件
  后，service 很容易膨胀

### 建议

- 保留当前主线
- 后续考虑引入 `observation_builder`
- 不要继续把更多 case 规则塞进 service

---

## 4.13 `app/api/diagnosis.py` / `app/models/diagnosis.py`

### 当前硬编码

- API 请求只支持 `platform_id`
- API 返回直接暴露 `AgentOutput`

### 硬编码性质

这是**接口裁剪型硬编码**，不是主要风险。

### 是否合理

当前合理。

### 风险

- 后续功能扩展时，请求模型会快速增长

### 建议

- 暂时保留
- 不视为当前主问题

---

## 5. 当前最值得重点审查的文件

如果要专门 review “硬编码是否合理”，建议重点审查：

1. [app/adapters/mapping/signal_mapper.py](/Users/felix/Desktop/Gaius/app/adapters/mapping/signal_mapper.py)
2. [app/core/log_context_builder.py](/Users/felix/Desktop/Gaius/app/core/log_context_builder.py)
3. [app/core/incident_engine.py](/Users/felix/Desktop/Gaius/app/core/incident_engine.py)
4. [app/core/output_formatter.py](/Users/felix/Desktop/Gaius/app/core/output_formatter.py)
5. [app/core/reasoner.py](/Users/felix/Desktop/Gaius/app/core/reasoner.py)
6. [app/core/llm_reasoner.py](/Users/felix/Desktop/Gaius/app/core/llm_reasoner.py)
7. [app/services/diagnosis_service.py](/Users/felix/Desktop/Gaius/app/services/diagnosis_service.py)

---

## 6. 当前建议的处理策略

### 6.1 保留

建议保留：

- `app/domain/`
- `docker_provider.py`
- `log_provider.py`
- `log_context_builder.py`
- `diagnosis_service.py`
- `/api/diagnosis`

### 6.2 冻结

建议冻结，不再继续扩展：

- `signal_mapper.py`
- `incident_engine.py`
- `output_formatter.py`
- `reasoner.py`

### 6.3 继续演进

建议继续演进：

- `llm_reasoner.py`

但演进方向不应是：
- 加更多 case
- 加更多 prompt 分支

而应是：

- 走向更中立的 observation bundle
- 减少预解释
- 让模型更多基于证据包而非预判过的 signal/incident 结论

---

## 7. 建议给其他 agent 的审查问题

可以直接把下面这些问题发给别的 agent：

### A. 哪些硬编码属于合理的结构契约？
- 哪些枚举和字段结构应该保留？

### B. 哪些硬编码只是阶段性实现约束？
- Docker-only、tail=50、只看当前容器日志，这些是否阶段性合理？

### C. 哪些模块已经在替模型做过多结论判断？
- `signal_mapper.py`
- `incident_engine.py`
- `output_formatter.py`
- `reasoner.py`

### D. 当前 `llm_reasoner.py` 是否仍然过度依赖当前样本故障和当前平台？
- Prompt
- evidence candidates
- log context 组织方式

### E. 主线是否应该进一步重构为：

`providers -> observation bundle -> llm diagnosis -> AgentOutput`

而不是继续维持：

`provider -> signal_mapper -> incident_engine -> output_formatter`

---

## 8. 一句话结论

当前 `Gaius` 的问题不是“有没有硬编码”，而是：

**哪些硬编码是合理的结构约束，哪些已经在把系统收缩成当前 Docker + GZ::CTF + 当前故障样本的专家系统。**

当前判断是：

- 结构层和采集层总体合理
- 规则诊断层已经明显 case 化
- LLM 推理层是当前主线，但仍带有当前样本偏置

因此，后续最值得评审的重点不是“删掉全部规则”，而是：

**如何让系统从 case 驱动链路，逐步演进为 observation-driven 的通用运维智能体。**
