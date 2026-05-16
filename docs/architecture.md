<!-- docs/architecture.md -->


## 当前系统如何推理与规划

### 推理

当前项目里实际存在两套推理思路，但**运行时主线**已经不是早期的规则链，而是 **LLM 驱动的结构化诊断**。

#### 1. 旧的规则型推理链

下面这些模块代表的是早期的规则化诊断路径：

- [/Users/felix/Desktop/Gaius/app/adapters/mapping/signal_mapper.py](/Users/felix/Desktop/Gaius/app/adapters/mapping/signal_mapper.py:1)
- [/Users/felix/Desktop/Gaius/app/core/incident_engine.py](/Users/felix/Desktop/Gaius/app/core/incident_engine.py:1)
- [/Users/felix/Desktop/Gaius/app/core/output_formatter.py](/Users/felix/Desktop/Gaius/app/core/output_formatter.py:1)
- [/Users/felix/Desktop/Gaius/app/core/reasoner.py](/Users/felix/Desktop/Gaius/app/core/reasoner.py:1)

这条链的基本方式是：

1. 先把原始事实映射成固定 `signal_type`
2. 再把 `signal_type` 聚合成固定 `incident_type`
3. 再把 `incident_type` 套进固定输出模板

这条链的优点是：
- 容易验证
- 容易调试
- 适合作为最初的骨架证明

但它的问题也很明显：
- 容易逐步演变成 case-by-case 的专家系统
- 新场景需要不断补 if/else
- 推理结果高度依赖预先写死的规则和模板

因此，这条规则链现在应被视为**过渡实现**，而不是未来主线。

#### 2. 当前实际运行的 LLM 推理链

当前 `/api/diagnosis` 的真实主线是：

- [/Users/felix/Desktop/Gaius/app/adapters/signals/docker_provider.py](/Users/felix/Desktop/Gaius/app/adapters/signals/docker_provider.py:1)
- [/Users/felix/Desktop/Gaius/app/adapters/signals/log_provider.py](/Users/felix/Desktop/Gaius/app/adapters/signals/log_provider.py:1)
- [/Users/felix/Desktop/Gaius/app/core/log_context_builder.py](/Users/felix/Desktop/Gaius/app/core/log_context_builder.py:1)
- [/Users/felix/Desktop/Gaius/app/core/llm_reasoner.py](/Users/felix/Desktop/Gaius/app/core/llm_reasoner.py:1)
- [/Users/felix/Desktop/Gaius/app/services/diagnosis_service.py](/Users/felix/Desktop/Gaius/app/services/diagnosis_service.py:1)

这条链的方式是：

1. 从真实环境采集容器状态和容器日志
2. 对日志做有限的上下文压缩
3. 将状态、日志片段和 evidence candidates 组织后送入 LLM
4. 由 LLM 输出结构化 `AgentOutput`

因此，当前系统的实际推理方式可以概括为：

**“证据组织 + LLM 结构化诊断”**

而不是：

**“规则命中 + 模板输出”**

不过需要明确的是，当前这条 LLM 主线仍然没有完全摆脱规则痕迹。  
这些规则主要还残留在：

- `signal_mapper.py` 的基础信号归类
- `log_context_builder.py` 的关键词筛选
- `llm_reasoner.py` 的 prompt 约束与 evidence 组织方式

也就是说，当前系统已经从“纯规则诊断”迈向了“LLM 推理”，但输入组织仍然带有一定的样本场景偏置。

---

### 规划

与“推理”相比，当前系统的“规划”并**没有被显式抽象成独立层**。

现在系统中的规划能力主要体现在三个地方：

#### 1. Service 编排层的顺序规划

在 [/Users/felix/Desktop/Gaius/app/services/diagnosis_service.py](/Users/felix/Desktop/Gaius/app/services/diagnosis_service.py:1) 中，系统已经隐含了一条固定顺序：

1. 先采集容器状态
2. 再映射基础信号
3. 再采集容器日志
4. 再压缩日志上下文
5. 最后调用 reasoner 生成输出

这是一种**静态编排式规划**。  
它说明系统当前知道“先做什么、后做什么”，但这种顺序是写死在 service 中的，而不是动态决定的。

#### 2. Prompt 内部承担了一部分“诊断决策规划”

在 [/Users/felix/Desktop/Gaius/app/core/llm_reasoner.py](/Users/felix/Desktop/Gaius/app/core/llm_reasoner.py:1) 中，prompt 不只是要求模型“总结现象”，还在要求它：

- 判断当前证据是否足够
- 判断当前应该输出 `success`、`partial` 还是 `clarification_needed`
- 指出缺失信息
- 给出下一步排查动作

这意味着：
**当前部分规划能力实际上被折叠进了 LLM prompt 本身。**

也就是说，模型不仅在做“解释”，也在做一定程度的“下一步该怎么做”的决策。

#### 3. 日志上下文构建器承担了一部分“证据优先级规划”

在 [/Users/felix/Desktop/Gaius/app/core/log_context_builder.py](/Users/felix/Desktop/Gaius/app/core/log_context_builder.py:1) 中，系统会根据关键词决定哪些日志更值得进入 reasoner。

这本质上是一种很轻量的规划：
- 先看哪些信息
- 暂时忽略哪些噪声

虽然它不是完整的 planning layer，但它已经在做“证据选择”的前置决策。

---

### 当前状态的准确描述

因此，当前系统更准确的描述应该是：

- **有推理**
  - 当前主线是 `llm_reasoner` 驱动的结构化推理

- **没有完整独立的规划层**
  - 当前“先采什么、看什么、缺什么、下一步做什么”仍然分散在 service 编排、日志筛选和 prompt 约束中

换句话说：

**当前系统已经有了“推理主线”，但还没有真正独立的“规划主线”。**

---

### 后续演进方向

后续更合理的方向不是继续增加更多规则型 `incident_type` 和模板，而是逐步演进到：

**providers -> observation bundle -> planning / reasoning -> AgentOutput**

在这个目标结构里：

- `providers`
  只负责采集真实事实

- `observation bundle`
  只负责组织观察结果，不预先下结论

- `planning layer`
  负责决定：
  - 当前证据是否足够
  - 是否需要继续采集更多信息
  - 哪些 observation 更值得优先关注

- `reasoning layer`
  负责基于 observation bundle 生成结构化诊断输出

这样系统才会从当前的“半规则、半 LLM”状态，逐步演进为真正的 **observation-driven 运维智能体**。

---

### 一句话总结

当前系统的真实状态是：

**主推理路径已经切换到 LLM，但规划能力还没有被正式抽象成独立层，仍然分散在 service 编排、日志筛选和 prompt 约束中。**
