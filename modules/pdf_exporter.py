#!/usr/bin/env python3
"""
PDF 导出模块
使用 Jinja2 + WeasyPrint 生成专业周报 PDF
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFExporter:
    """PDF 导出器"""

    def __init__(self, template_path: Optional[str] = None):
        """
        初始化 PDF 导出器

        Args:
            template_path: Jinja2 模板路径（不提供则使用默认模板）
        """
        from jinja2 import Environment, FileSystemLoader

        if template_path is None:
            template_dir = Path(__file__).parent.parent / "templates" / "pdf"
        else:
            template_dir = Path(template_path).parent

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template_name = "report_template.html"

        logger.info(f"PDF 导出器已初始化，模板目录: {template_dir}")

    def export(
        self,
        output_path: str,
        report_data: Dict,
        include_charts: bool = True
    ) -> str:
        """
        导出 PDF 周报

        Args:
            output_path: 输出 PDF 文件路径
            report_data: 报告数据字典
            include_charts: 是否包含图表

        Returns:
            生成的 PDF 文件路径
        """
        try:
            # 加载模板
            template = self.env.get_template(self.template_name)

            # 准备模板数据
            template_data = self._prepare_template_data(report_data, include_charts)

            # 渲染 HTML
            html_content = template.render(**template_data)

            # 生成 PDF
            from weasyprint import HTML, CSS

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 转换为 PDF
            HTML(string=html_content).write_pdf(
                output_path,
                stylesheets=None
            )

            logger.info(f"PDF 已生成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"PDF 生成失败: {e}")
            raise

    def _prepare_template_data(self, report_data: Dict, include_charts: bool) -> Dict:
        """准备模板数据"""

        # 基础信息
        template_data = {
            "report_title": report_data.get("title", "Crypto 投研周报"),
            "report_period": report_data.get("period", "本周"),
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": report_data.get("version", "v1.0"),
            "llm_model": report_data.get("llm_model", "GPT-4o")
        }

        # 概览指标
        template_data["overview_metrics"] = report_data.get("overview_metrics", [])

        # 摘要
        template_data["summary_content"] = report_data.get("summary", "")

        # BTC 部分
        if "btc" in report_data:
            btc_section = {
                "content": report_data["btc"].get("content", ""),
                "charts": []
            }

            if include_charts and "charts" in report_data["btc"]:
                for chart in report_data["btc"]["charts"]:
                    # 转换为绝对路径（WeasyPrint 需要）
                    chart_path = os.path.abspath(chart["path"])
                    btc_section["charts"].append({
                        "path": f"file://{chart_path}",
                        "title": chart.get("title", ""),
                        "caption": chart.get("caption", "")
                    })

            template_data["btc_section"] = btc_section

        # 宏观部分
        if "macro" in report_data:
            macro_section = {
                "content": report_data["macro"].get("content", ""),
                "charts": []
            }

            if include_charts and "charts" in report_data["macro"]:
                for chart in report_data["macro"]["charts"]:
                    chart_path = os.path.abspath(chart["path"])
                    macro_section["charts"].append({
                        "path": f"file://{chart_path}",
                        "title": chart.get("title", ""),
                        "caption": chart.get("caption", "")
                    })

            template_data["macro_section"] = macro_section

        # 链上部分
        if "onchain" in report_data:
            onchain_section = {
                "content": report_data["onchain"].get("content", ""),
                "charts": []
            }

            if include_charts and "charts" in report_data["onchain"]:
                for chart in report_data["onchain"]["charts"]:
                    chart_path = os.path.abspath(chart["path"])
                    onchain_section["charts"].append({
                        "path": f"file://{chart_path}",
                        "title": chart.get("title", ""),
                        "caption": chart.get("caption", "")
                    })

            template_data["onchain_section"] = onchain_section

        return template_data


def generate_report_pdf(
    chart_paths: Dict[str, List[str]],
    content: Dict[str, str],
    metrics: Optional[List[Dict]] = None,
    output_dir: str = "output/pdf"
) -> str:
    """
    快捷方法：生成完整周报 PDF

    Args:
        chart_paths: {"btc": [...], "macro": [...], "onchain": [...]}
        content: {"btc_analysis": "...", "macro_analysis": "...", ...}
        metrics: [{"label": "BTC 价格", "value": "$90,000", "delta": "+2.5%"}, ...]
        output_dir: 输出目录

    Returns:
        PDF 文件路径
    """
    # 构建报告数据
    report_data = {
        "title": "Crypto 投研周报",
        "period": f"{datetime.now().strftime('%Y年第%W周')}",
        "version": "v1.0",
        "overview_metrics": metrics or [],
        "summary": content.get("summary", ""),
    }

    # BTC 部分
    if "btc" in chart_paths:
        report_data["btc"] = {
            "content": content.get("btc_analysis", ""),
            "charts": [
                {
                    "path": path,
                    "title": os.path.basename(path),
                    "caption": f"图表: {os.path.basename(path)}"
                }
                for path in chart_paths["btc"]
            ]
        }

    # 宏观部分
    if "macro" in chart_paths:
        report_data["macro"] = {
            "content": content.get("macro_analysis", ""),
            "charts": [
                {
                    "path": path,
                    "title": os.path.basename(path),
                    "caption": f"图表: {os.path.basename(path)}"
                }
                for path in chart_paths["macro"]
            ]
        }

    # 链上部分
    if "onchain" in chart_paths:
        report_data["onchain"] = {
            "content": content.get("onchain_analysis", ""),
            "charts": [
                {
                    "path": path,
                    "title": os.path.basename(path),
                    "caption": f"图表: {os.path.basename(path)}"
                }
                for path in chart_paths.get("onchain", [])
            ]
        }

    # 生成 PDF
    exporter = PDFExporter()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"crypto_report_{timestamp}.pdf")

    return exporter.export(output_path, report_data)
