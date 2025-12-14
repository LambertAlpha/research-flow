#!/usr/bin/env python3
"""
LangGraph Multi-Agent 工作流编排
使用 LangGraph 构建 Agent 协作的状态图
"""

import logging
from typing import Dict
from langgraph.graph import StateGraph, END
from modules.agent_state import AgentState, create_initial_state
from modules.agent_nodes import (
    chief_editor_node,
    data_engineer_node,
    chartist_node,
    senior_analyst_node,
    debate_node,
    route_after_chief_editor,
    route_after_debate
)

logger = logging.getLogger(__name__)


def create_workflow() -> StateGraph:
    """
    创建 Multi-Agent 工作流

    工作流结构：
    1. Chief Editor (初始化) → Data Engineer
    2. Data Engineer (数据抓取) → Chartist
    3. Chartist (图表生成) → Senior Analyst
    4. Senior Analyst (文案生成) → Chief Editor (审核)
    5. Chief Editor (审核) → Debate (如果有问题)
    6. Debate → Senior Analyst (改进) 或 END (达成共识)

    Returns:
        编译后的工作流
    """
    # 创建状态图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("chief_editor", chief_editor_node)
    workflow.add_node("data_engineer", data_engineer_node)
    workflow.add_node("chartist", chartist_node)
    workflow.add_node("senior_analyst", senior_analyst_node)
    workflow.add_node("debate", debate_node)

    # 设置入口点
    workflow.set_entry_point("chief_editor")

    # 添加边（定义工作流路径）

    # Chief Editor 的条件路由
    workflow.add_conditional_edges(
        "chief_editor",
        route_after_chief_editor,
        {
            "data_engineer": "data_engineer",
            "debate": "debate",
            "end": END
        }
    )

    # Data Engineer → Chartist
    workflow.add_edge("data_engineer", "chartist")

    # Chartist → Senior Analyst
    workflow.add_edge("chartist", "senior_analyst")

    # Senior Analyst → Chief Editor (审核)
    workflow.add_edge("senior_analyst", "chief_editor")

    # Debate 的条件路由
    workflow.add_conditional_edges(
        "debate",
        route_after_debate,
        {
            "chief_editor": "chief_editor",
            "senior_analyst": "senior_analyst"
        }
    )

    # 编译工作流
    app = workflow.compile()

    logger.info("✅ Multi-Agent 工作流已创建")

    return app


def run_report_generation(report_period: str, verbose: bool = True) -> AgentState:
    """
    运行完整的报告生成工作流

    Args:
        report_period: 报告周期 (e.g., "2024-12-01 ~ 2024-12-07")
        verbose: 是否打印详细日志

    Returns:
        最终状态
    """
    logger.info("=" * 60)
    logger.info("🚀 启动 Multi-Agent 报告生成工作流")
    logger.info("=" * 60)

    # 创建工作流
    app = create_workflow()

    # 创建初始状态
    initial_state = create_initial_state(report_period)

    # 运行工作流
    try:
        final_state = None
        step_count = 0

        for state in app.stream(initial_state):
            step_count += 1
            if verbose:
                current_step = list(state.keys())[0] if state else "unknown"
                logger.info(f"步骤 {step_count}: {current_step}")

            final_state = state

        logger.info("=" * 60)
        logger.info("✅ 工作流执行完成")
        logger.info("=" * 60)

        # 提取最终状态（LangGraph 返回的是 dict of states）
        if isinstance(final_state, dict):
            # 获取最后一个节点的状态
            final_node_state = list(final_state.values())[0]
        else:
            final_node_state = final_state

        return final_node_state

    except Exception as e:
        logger.error(f"❌ 工作流执行失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def get_workflow_visualization() -> str:
    """
    获取工作流的 Mermaid 可视化图

    Returns:
        Mermaid 图表语法
    """
    mermaid = """
graph TD
    Start([开始]) --> ChiefEditor[Chief Editor<br/>任务分配]
    ChiefEditor --> DataEngineer[Data Engineer<br/>数据抓取]
    DataEngineer --> Chartist[Chartist<br/>图表生成]
    Chartist --> Analyst[Senior Analyst<br/>文案生成]
    Analyst --> Review[Chief Editor<br/>质量审核]

    Review -->|质量合格| End([结束])
    Review -->|需要改进| Debate[Debate Node<br/>辩论改进]
    Debate -->|未达成共识| Analyst
    Debate -->|达成共识| End

    style ChiefEditor fill:#3498db
    style DataEngineer fill:#2ecc71
    style Chartist fill:#f39c12
    style Analyst fill:#9b59b6
    style Debate fill:#e74c3c
    """
    return mermaid


if __name__ == "__main__":
    # 测试工作流
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行报告生成
    final_state = run_report_generation("2024-12-09 ~ 2024-12-15", verbose=True)

    # 打印结果摘要
    print("\n" + "=" * 60)
    print("📊 执行结果摘要")
    print("=" * 60)
    print(f"任务 ID: {final_state.get('task_id', 'N/A')}")
    print(f"质量评分: {final_state.get('quality_score', 0):.1f}/100")
    print(f"辩论轮数: {final_state.get('debate_rounds', 0)}")
    print(f"审批状态: {final_state.get('approval_status', 'unknown')}")
    print(f"图表数量: {sum(len(charts) for charts in final_state.get('chart_paths', {}).values())}")
    print(f"文案段落: {len(final_state.get('final_content', {}))}")
    print(f"错误数量: {len(final_state.get('errors', []))}")
    print("=" * 60)
