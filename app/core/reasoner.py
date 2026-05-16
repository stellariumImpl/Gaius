"""Reasoner: 统一的运维推理入口

STATUS: FROZEN

职责:
- 接收标准化 Signal 列表
- 形成当前问题理解
- 输出标准 AgentOutput

说明:
- 当前版本仍使用最小规则,但规则被集中到唯一推理层
- provider / mapper / domain 模型保持不变
- 后续可在不改上层接口的前提下替换为更强的推理实现
- 当前不再作为未来主线继续扩展
- 后续应逐步降级为 fallback / smoke-test 实现
"""
from __future__ import annotations

from app.domain.output import AgentOutput, Confidence, OutputStatus
from app.domain.signal import Signal


def reason(signals: list[Signal]) -> AgentOutput:
    """统一推理入口
    
    当前策略:
    - 没有 signal -> failed
    - 只有 container_restarted -> 观察项
    - 存在 container_unhealthy -> 服务健康异常
    - 存在 container_not_running -> 服务不可用风险
    """
    if not signals:
        return AgentOutput(
            status=OutputStatus.FAILED,
            summary="当前没有可用于分析的运维信号",
            current_situation="未采集到有效 Signal",
            impact_scope="未知",
            confidence=Confidence.LOW,
            missing_information=["需要至少一种真实环境信号来源"],
        )

    signal_types = {signal.signal_type for signal in signals}

    if "container_not_running" in signal_types:
        return _reason_service_unavailable(signals)

    if "container_unhealthy" in signal_types:
        return _reason_health_degradation(signals)

    if signal_types == {"container_restarted"}:
        return _reason_restart_observation(signals)

    return _reason_generic(signals)


def _reason_service_unavailable(signals: list[Signal]) -> AgentOutput:
    container_names = _extract_container_names(signals, target_type="container_not_running")

    return AgentOutput(
        status=OutputStatus.SUCCESS,
        summary="检测到存在未运行容器，平台可能存在服务不可用风险",
        current_situation=f"以下容器当前未运行: {', '.join(container_names)}",
        impact_scope="可能影响平台整体可用性，或影响部分核心服务",
        suspected_causes=[
            "容器启动失败",
            "服务进程崩溃退出",
            "依赖服务异常导致容器无法保持运行",
        ],
        investigation_steps=[
            "查看对应容器最近的日志输出",
            "确认容器退出码和退出时间",
            "检查数据库、缓存、网络等依赖是否正常",
        ],
        suggested_actions=[
            "优先确认受影响容器是否属于核心路径",
            "如当前为赛时环境，应优先恢复服务可用性并保留日志现场",
        ],
        confidence=Confidence.HIGH,
        missing_information=[
            "容器退出码",
            "退出前后的应用日志",
        ],
        evidence=[],
    )


def _reason_health_degradation(signals: list[Signal]) -> AgentOutput:
    container_names = _extract_container_names(signals, target_type="container_unhealthy")

    return AgentOutput(
        status=OutputStatus.SUCCESS,
        summary="检测到服务健康状态异常，建议尽快排查对应容器",
        current_situation=f"以下容器健康检查失败: {', '.join(container_names)}",
        impact_scope="可能已经影响部分平台功能或用户访问体验",
        suspected_causes=[
            "应用内部错误导致健康检查失败",
            "服务依赖异常，例如数据库或缓存不可用",
            "容器虽然在运行，但内部进程未处于健康状态",
        ],
        investigation_steps=[
            "查看对应容器最近日志",
            "确认健康检查失败的时间与错误信息",
            "检查服务依赖是否存在异常",
        ],
        suggested_actions=[
            "优先确认该容器是否仍能提供核心服务",
            "如服务已明显异常，可考虑重启容器并保留日志现场",
        ],
        confidence=Confidence.HIGH,
        missing_information=[
            "健康检查失败时的详细错误信息",
            "对应应用日志",
        ],
        evidence=[],
    )


def _reason_restart_observation(signals: list[Signal]) -> AgentOutput:
    container_names = _extract_container_names(signals, target_type="container_restarted")

    return AgentOutput(
        status=OutputStatus.PARTIAL,
        summary="检测到部分容器发生过重启，当前更像观察项而非明确故障",
        current_situation=f"以下容器存在重启记录: {', '.join(container_names)}",
        impact_scope="当前尚未观察到明确不可用，但说明系统曾发生容器级波动",
        suspected_causes=[
            "服务启动或重启过程中出现过短暂异常",
            "宿主机或依赖组件曾发生波动",
            "发布、配置变更或人工维护触发了容器重启",
        ],
        investigation_steps=[
            "查看对应容器最近的启动日志",
            "确认重启发生的时间点",
            "检查重启前后是否存在发布、配置变更或宿主机异常",
        ],
        suggested_actions=[
            "如果当前服务运行正常，可先将本次重启作为观察事件记录",
            "如重启频繁出现，应进一步接入日志与指标进行根因分析",
        ],
        confidence=Confidence.MEDIUM,
        missing_information=[
            "容器重启发生的具体时间",
            "容器重启前后的应用日志",
            "宿主机当时的资源使用情况",
        ],
        evidence=[],
    )


def _reason_generic(signals: list[Signal]) -> AgentOutput:
    signal_names = [signal.signal_type for signal in signals]

    return AgentOutput(
        status=OutputStatus.PARTIAL,
        summary="检测到运维信号，但当前尚未形成明确故障判断",
        current_situation=f"当前观测到的信号类型包括: {', '.join(signal_names)}",
        impact_scope="影响范围待进一步确认",
        suspected_causes=[
            "当前信号不足以支持明确故障结论",
        ],
        investigation_steps=[
            "继续补充日志、指标或事件信号",
            "结合更多上下文后再做进一步判断",
        ],
        suggested_actions=[
            "先保留当前信号与现场信息",
        ],
        confidence=Confidence.LOW,
        missing_information=[
            "更完整的运行时上下文",
        ],
        evidence=[],
    )


def _extract_container_names(signals: list[Signal], target_type: str) -> list[str]:
    names: list[str] = []

    for signal in signals:
        if signal.signal_type != target_type:
            continue

        container_name = signal.payload.get("container_name")
        if isinstance(container_name, str) and container_name not in names:
            names.append(container_name)

    return names
