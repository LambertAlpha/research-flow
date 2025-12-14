#!/usr/bin/env python3
"""
LangGraph Multi-Agent 状态管理
定义工作流的状态结构和转换逻辑
"""

from typing import TypedDict, List, Dict, Optional, Annotated
from datetime import datetime
import operator


class AgentState(TypedDict):
    """
    Multi-Agent 工作流的全局状态

    这个状态会在所有 Agent 之间传递，每个 Agent 读取并更新状态
    """

    # ========== 任务信息 ==========
    task_id: str  # 任务 ID
    report_period: str  # 报告周期 (e.g., "2024-12-01 ~ 2024-12-07")
    started_at: str  # 开始时间
    current_step: str  # 当前步骤

    # ========== 数据层 ==========
    raw_data: Dict[str, Dict]  # 原始数据 {"btc": {...}, "macro": {...}}
    processed_data: Dict[str, any]  # 处理后的数据

    # ========== 图表层 ==========
    chart_paths: Dict[str, List[str]]  # 生成的图表路径 {"btc": [...], "macro": [...]}

    # ========== 文案层 ==========
    draft_content: Dict[str, str]  # 初稿文案 {"btc_analysis": "...", ...}
    reviewed_content: Dict[str, str]  # 审核后的文案
    final_content: Dict[str, str]  # 最终文案

    # ========== Agent 协作 ==========
    messages: Annotated[List[Dict], operator.add]  # Agent 之间的消息 (append-only)
    debate_rounds: int  # 辩论轮数
    consensus_reached: bool  # 是否达成共识

    # ========== 质量控制 ==========
    quality_score: float  # 质量评分 (0-100)
    issues: List[str]  # 发现的问题列表
    approval_status: str  # 审批状态 ("pending", "approved", "rejected")

    # ========== 输出 ==========
    pdf_path: Optional[str]  # 生成的 PDF 路径
    errors: List[str]  # 错误列表


class AgentMessage(TypedDict):
    """Agent 之间传递的消息"""
    from_agent: str  # 发送者
    to_agent: str  # 接收者
    message_type: str  # 消息类型 ("request", "response", "challenge", "rebuttal")
    content: str  # 消息内容
    timestamp: str  # 时间戳
    metadata: Optional[Dict]  # 额外元数据


def create_initial_state(report_period: str) -> AgentState:
    """
    创建初始状态

    Args:
        report_period: 报告周期

    Returns:
        初始化的 AgentState
    """
    return AgentState(
        task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        report_period=report_period,
        started_at=datetime.now().isoformat(),
        current_step="initialization",
        raw_data={},
        processed_data={},
        chart_paths={},
        draft_content={},
        reviewed_content={},
        final_content={},
        messages=[],
        debate_rounds=0,
        consensus_reached=False,
        quality_score=0.0,
        issues=[],
        approval_status="pending",
        pdf_path=None,
        errors=[]
    )


def add_message(
    state: AgentState,
    from_agent: str,
    to_agent: str,
    message_type: str,
    content: str,
    metadata: Optional[Dict] = None
) -> AgentMessage:
    """
    创建并添加消息到状态

    Args:
        state: 当前状态
        from_agent: 发送者
        to_agent: 接收者
        message_type: 消息类型
        content: 消息内容
        metadata: 额外元数据

    Returns:
        创建的消息
    """
    message = AgentMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=message_type,
        content=content,
        timestamp=datetime.now().isoformat(),
        metadata=metadata or {}
    )

    # messages 字段使用 operator.add，会自动 append
    return message


def should_continue_debate(state: AgentState, max_rounds: int = 2) -> bool:
    """
    判断是否应该继续辩论

    Args:
        state: 当前状态
        max_rounds: 最大辩论轮数

    Returns:
        是否继续辩论
    """
    # 如果已达成共识，停止
    if state.get("consensus_reached", False):
        return False

    # 如果超过最大轮数，停止
    if state.get("debate_rounds", 0) >= max_rounds:
        return False

    # 如果有严重问题且未解决，继续
    critical_issues = [
        issue for issue in state.get("issues", [])
        if "critical" in issue.lower() or "error" in issue.lower()
    ]

    return len(critical_issues) > 0


def calculate_quality_score(state: AgentState) -> float:
    """
    计算质量评分

    Args:
        state: 当前状态

    Returns:
        质量评分 (0-100)
    """
    score = 100.0

    # 数据完整性检查 (-20)
    if not state.get("raw_data"):
        score -= 20
    elif len(state.get("raw_data", {})) < 2:
        score -= 10

    # 图表生成检查 (-20)
    if not state.get("chart_paths"):
        score -= 20
    elif sum(len(charts) for charts in state.get("chart_paths", {}).values()) < 2:
        score -= 10

    # 文案质量检查 (-30)
    final_content = state.get("final_content", {})
    if not final_content:
        score -= 30
    else:
        # 检查文案长度（太短说明不够详细）
        avg_length = sum(len(text) for text in final_content.values()) / max(len(final_content), 1)
        if avg_length < 100:
            score -= 20
        elif avg_length < 200:
            score -= 10

    # 问题数量检查 (-30)
    num_issues = len(state.get("issues", []))
    if num_issues > 5:
        score -= 30
    elif num_issues > 2:
        score -= 15
    elif num_issues > 0:
        score -= 5

    return max(0.0, score)
