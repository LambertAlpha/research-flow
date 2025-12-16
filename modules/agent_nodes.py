#!/usr/bin/env python3
"""
LangGraph Multi-Agent 节点
定义工作流中的各个 Agent 及其职责
"""

import logging
from typing import Dict
from modules.agent_state import AgentState, add_message, calculate_quality_score
from modules.data_fetcher import fetch_module_data
from modules.chart_builder import generate_module_charts
from modules.llm_writer import LLMWriter, prepare_btc_context, prepare_macro_context

logger = logging.getLogger(__name__)


# ==================== Agent 节点 ====================

def chief_editor_node(state: AgentState) -> AgentState:
    """
    总编 Agent
    职责：任务分配、质量把关、最终审批
    """
    logger.info("📝 Chief Editor 开始工作...")

    current_step = state.get("current_step", "")

    if current_step == "initialization":
        # 任务初始化：分配任务给数据工程师
        state["current_step"] = "data_collection"
        state["messages"].append({
            "from_agent": "chief_editor",
            "to_agent": "data_engineer",
            "message_type": "request",
            "content": f"请获取 {state['report_period']} 的所有数据",
            "timestamp": "",
            "metadata": {}
        })
        logger.info("✅ 任务已分配给 Data Engineer")

    elif current_step == "review":
        # 审核文案质量
        quality_score = calculate_quality_score(state)
        state["quality_score"] = quality_score

        if quality_score >= 80:
            state["approval_status"] = "approved"
            state["consensus_reached"] = True
            state["final_content"] = state.get("reviewed_content", {})
            logger.info(f"✅ 文案已通过审核，质量评分: {quality_score:.1f}")
        else:
            state["approval_status"] = "rejected"
            state["issues"].append(f"质量评分不足: {quality_score:.1f}/100")
            state["debate_rounds"] = state.get("debate_rounds", 0) + 1
            logger.warning(f"⚠️ 文案需要改进，质量评分: {quality_score:.1f}")

        state["current_step"] = "finalization"

    return state


def data_engineer_node(state: AgentState) -> AgentState:
    """
    数据工程师 Agent
    职责：数据抓取、数据清洗、数据验证
    """
    logger.info("📊 Data Engineer 开始工作...")

    try:
        # 获取所有模块数据
        modules = ["macro"]  # 只抓取不需要 API key 的模块

        raw_data = {}
        for module in modules:
            logger.info(f"正在获取 {module} 模块数据...")
            data = fetch_module_data(module, {})
            raw_data[module] = data

        state["raw_data"] = raw_data
        state["current_step"] = "chart_generation"

        logger.info(f"✅ 数据获取完成，共 {len(raw_data)} 个模块")

    except Exception as e:
        error_msg = f"数据获取失败: {str(e)}"
        state["errors"].append(error_msg)
        state["issues"].append(error_msg)
        logger.error(f"❌ {error_msg}")

    return state


def chartist_node(state: AgentState) -> AgentState:
    """
    图表师 Agent
    职责：图表生成、图表优化、视觉呈现
    """
    logger.info("📈 Chartist 开始工作...")

    try:
        raw_data = state.get("raw_data", {})
        chart_paths = {}

        for module, data in raw_data.items():
            logger.info(f"正在生成 {module} 模块图表...")
            charts = generate_module_charts(module, data)
            chart_paths[module] = charts
            logger.info(f"✅ {module} 生成了 {len(charts)} 张图表")

        state["chart_paths"] = chart_paths
        state["current_step"] = "content_generation"

    except Exception as e:
        error_msg = f"图表生成失败: {str(e)}"
        state["errors"].append(error_msg)
        state["issues"].append(error_msg)
        logger.error(f"❌ {error_msg}")

    return state


def senior_analyst_node(state: AgentState) -> AgentState:
    """
    资深分析师 Agent
    职责：LLM 文案生成、数据解读、专业分析
    """
    logger.info("✍️ Senior Analyst 开始工作...")

    try:
        # 检查是否有 LLM API key（优先使用 Gemini）
        import os
        has_gemini = os.getenv("GEMINI_API_KEY") is not None
        has_openai = os.getenv("OPENAI_API_KEY") is not None

        if not (has_openai or has_gemini):
            logger.warning("⚠️ 未配置 LLM API Key，使用 Mock 文案")
            state["draft_content"] = {
                "macro_analysis": "宏观分析文案（Mock）- 请配置 OPENAI_API_KEY 或 GEMINI_API_KEY 以使用真实 LLM 生成"
            }
            state["reviewed_content"] = state["draft_content"]
            state["current_step"] = "review"
            return state

        # 使用真实 LLM 生成文案（优先 Gemini Flash）
        model = "gemini-flash" if has_gemini else "gpt-4o"
        writer = LLMWriter(model=model)

        # 准备上下文
        raw_data = state.get("raw_data", {})
        macro_data = raw_data.get("macro", {})

        if macro_data:
            macro_context = prepare_macro_context(macro_data)
            content = writer.generate("macro_analysis", macro_context)
            state["draft_content"] = {"macro_analysis": content}
            state["reviewed_content"] = state["draft_content"]
            logger.info("✅ LLM 文案生成完成")
        else:
            state["issues"].append("缺少宏观数据，无法生成文案")

        state["current_step"] = "review"

    except Exception as e:
        error_msg = f"文案生成失败: {str(e)}"
        state["errors"].append(error_msg)
        state["issues"].append(error_msg)
        logger.error(f"❌ {error_msg}")

    return state


def debate_node(state: AgentState) -> AgentState:
    """
    辩论节点
    职责：Agent 之间的质疑、反驳、共识达成
    """
    logger.info("🎯 Debate Node 开始...")

    # 检查是否需要辩论
    issues = state.get("issues", [])
    debate_rounds = state.get("debate_rounds", 0)

    if len(issues) == 0:
        # 没有问题，直接达成共识
        state["consensus_reached"] = True
        logger.info("✅ 无问题，达成共识")
    elif debate_rounds >= 2:
        # 超过最大轮数，强制结束
        state["consensus_reached"] = True
        logger.info("⚠️ 达到最大辩论轮数，强制结束")
    else:
        # 进行辩论
        logger.info(f"🔄 开始第 {debate_rounds + 1} 轮辩论")

        # 模拟辩论：分析师回应问题
        state["messages"].append({
            "from_agent": "senior_analyst",
            "to_agent": "chief_editor",
            "message_type": "rebuttal",
            "content": f"已针对以下问题进行改进: {', '.join(issues[:3])}",
            "timestamp": "",
            "metadata": {}
        })

        # 清空问题列表，准备下一轮审核
        state["issues"] = []
        state["debate_rounds"] = debate_rounds + 1
        state["current_step"] = "review"

    return state


# ==================== 路由函数 ====================

def route_after_chief_editor(state: AgentState) -> str:
    """决定 Chief Editor 之后的路由"""
    current_step = state.get("current_step", "")

    if current_step == "data_collection":
        return "data_engineer"
    elif current_step == "finalization":
        if state.get("consensus_reached", False):
            return "end"
        else:
            return "debate"
    else:
        return "end"


def route_after_debate(state: AgentState) -> str:
    """决定 Debate 之后的路由"""
    if state.get("consensus_reached", False):
        return "chief_editor"
    else:
        return "senior_analyst"  # 返回让分析师改进


def should_continue_workflow(state: AgentState) -> bool:
    """判断工作流是否应该继续"""
    # 如果有严重错误，停止
    if len(state.get("errors", [])) > 0:
        return False

    # 如果已达成共识，停止
    if state.get("consensus_reached", False):
        return False

    # 如果超过 10 步，强制停止（防止死循环）
    if state.get("debate_rounds", 0) > 10:
        return False

    return True
