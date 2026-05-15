"""Output Formatter: 将 Incident 转换为标准 AgentOutput"""

from __future__ import annotations

from app.domain.incident import Incident
from app.domain.output import AgentOutput, Confidence, OutputStatus


def format_incident_output(incident: Incident) -> AgentOutput:
    """将单个 Incident 格式化为标准 AgentOutput"""
    if incident.incident_type == "container_restart_detected":
        return _format_restart_detected(incident)

    if incident.incident_type == "service_health_degradation":
        return _format_health_degradation(incident)

    if incident.incident_type == "service_unavailable":
        return _format_service_unavailable(incident)

    return _format_generic_incident(incident)


def _format_restart_detected(incident: Incident) -> AgentOutput:
    return AgentOutput(
        status=OutputStatus.PARTIAL,
        summary="检测到部分容器发生过重启，建议进一步确认是否属于异常重启",
        current_situation=incident.summary,
        impact_scope="当前尚未观察到服务不可用，但说明系统曾发生过容器级波动",
        suspected_causes=[
            "服务启动或重启过程中出现过短暂异常",
            "容器所在宿主机或依赖组件曾发生波动",
            "服务发布、配置变更或人工重启导致容器重启",
        ],
        investigation_steps=[
            "查看对应容器最近的启动日志",
            "确认容器重启发生的时间点",
            "检查重启前后是否存在配置变更、镜像更新或宿主机异常",
        ],
        suggested_actions=[
            "如果当前服务运行正常，可先记录本次重启事件并继续观察",
            "如重启频繁出现，应进一步接入日志与指标进行根因分析",
        ],
        confidence=Confidence.MEDIUM,
        missing_information=[
            "容器重启发生的具体时间",
            "容器重启前后的应用日志",
            "宿主机当时的资源使用情况",
        ],
        evidence=[],
        related_incident_id=incident.incident_id,
    )


def _format_health_degradation(incident: Incident) -> AgentOutput:
    return AgentOutput(
        status=OutputStatus.SUCCESS,
        summary="检测到服务健康状态异常，建议尽快排查对应容器",
        current_situation=incident.summary,
        impact_scope="可能已经影响部分平台功能或用户访问体验",
        suspected_causes=[
            "应用内部错误导致健康检查失败",
            "服务依赖异常，例如数据库或缓存不可用",
            "容器虽然在运行，但内部进程未处于健康状态",
        ],
        investigation_steps=[
            "查看对应容器最近日志",
            "确认健康检查失败的时间与错误信息",
            "检查该服务依赖的数据库、缓存或网络连通性",
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
        related_incident_id=incident.incident_id,
    )


def _format_service_unavailable(incident: Incident) -> AgentOutput:
    return AgentOutput(
        status=OutputStatus.SUCCESS,
        summary="检测到存在未运行容器，服务可能已经不可用",
        current_situation=incident.summary,
        impact_scope="可能直接影响平台可用性或部分核心功能",
        suspected_causes=[
            "容器启动失败",
            "服务进程崩溃退出",
            "配置错误或依赖不可用导致容器无法保持运行",
        ],
        investigation_steps=[
            "查看退出容器的最近日志",
            "确认容器退出码和退出时间",
            "检查依赖服务是否可用，例如数据库、缓存、网络",
        ],
        suggested_actions=[
            "优先确认受影响服务是否属于核心路径",
            "如当前为赛时环境，应优先恢复服务可用性并保留故障现场",
        ],
        confidence=Confidence.HIGH,
        missing_information=[
            "容器退出码",
            "退出前后的应用日志",
        ],
        evidence=[],
        related_incident_id=incident.incident_id,
    )


def _format_generic_incident(incident: Incident) -> AgentOutput:
    return AgentOutput(
        status=OutputStatus.PARTIAL,
        summary=f"检测到异常事件: {incident.title}",
        current_situation=incident.summary,
        impact_scope="影响范围待进一步确认",
        suspected_causes=["当前异常类型尚未匹配专用分析模板"],
        investigation_steps=[
            "回看关联信号和原始数据",
            "补充日志、指标或事件上下文",
        ],
        suggested_actions=[
            "先收集更多证据，再进行进一步判断",
        ],
        confidence=Confidence.LOW,
        missing_information=[
            "更完整的上下文信息",
        ],
        evidence=[],
        related_incident_id=incident.incident_id,
    )
