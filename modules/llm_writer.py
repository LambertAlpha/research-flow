#!/usr/bin/env python3
"""
LLM 文案生成模块
支持 GPT-4o 和 Gemini 两种模型
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Prompt 模板
PROMPTS = {
    "btc_analysis": """你是一位专业的加密货币分析师，正在撰写 BTC 周报的市场分析部分。

请基于以下数据生成 200-300 字的专业分析：

**价格数据：**
- 当前价格: ${current_price:,.2f}
- 周涨跌幅: {weekly_change:+.2f}%
- 30日最高: ${high_30d:,.2f}
- 30日最低: ${low_30d:,.2f}

**技术指标：**
{technical_indicators}

**宏观环境：**
{macro_context}

**分析要求：**
1. 简明扼要，不超过 3 段
2. 数据驱动，避免主观猜测
3. 突出关键价格水平和趋势
4. 专业术语使用准确
5. 避免过度乐观或悲观的情绪化表达

请直接输出分析文案，不要包含标题或其他格式：
""",

    "macro_analysis": """你是一位宏观经济分析师，正在撰写加密市场周报的宏观环境部分。

请基于以下数据生成 150-200 字的分析：

**美元指数 (DXY)：**
- 当前值: {dxy_current:.2f}
- 周变化: {dxy_change:+.2f}%

**美债收益率 (US10Y)：**
- 当前值: {us10y_current:.2f}%
- 周变化: {us10y_change:+.2f} bps

**股市表现：**
- 标普500: {sp500_change:+.2f}%
- NVDA: {nvda_change:+.2f}%
- COIN: {coin_change:+.2f}%

**分析要点：**
1. 聚焦宏观因素对加密市场的影响
2. 突出美元、利率、风险偏好的变化
3. 简洁专业，避免冗长

请直接输出分析文案：
""",

    "onchain_analysis": """你是一位链上数据分析师，正在撰写 BTC 链上指标分析。

请基于以下数据生成 150-200 字的分析：

**筹码分布 (URPD)：**
{urpd_summary}

**ETF 资金流向：**
{etf_summary}

**鲸鱼动向：**
{whale_summary}

**分析要求：**
1. 解读链上数据的市场含义
2. 识别关键支撑/压力位
3. 分析大户行为趋势
4. 数据优先，避免推测

请直接输出分析文案：
""",

    "summary": """你是一位资深加密货币分析师，正在撰写周报的总结部分。

请基于本周的关键数据和分析，生成 100-150 字的总结：

**关键数据点：**
{key_metrics}

**主要观察：**
{main_observations}

**总结要求：**
1. 提炼本周最重要的 2-3 个观察
2. 平衡看待市场，避免单边预测
3. 为读者提供可操作的洞察
4. 简洁有力，避免套话

请直接输出总结文案：
"""
}


class LLMWriter:
    """LLM 文案生成器"""

    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        """
        初始化 LLM Writer

        Args:
            model: 模型名称 ("gpt-4o" 或 "gemini")
            api_key: API 密钥（如果不提供则从环境变量读取）
        """
        self.model = model.lower()
        self.api_key = api_key

        if self.model.startswith("gpt"):
            self._init_openai()
        elif self.model.startswith("gemini"):
            self._init_gemini()
        else:
            raise ValueError(f"不支持的模型: {model}")

    def _init_openai(self):
        """初始化 OpenAI 客户端"""
        try:
            from openai import OpenAI

            api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("未找到 OPENAI_API_KEY")

            self.client = OpenAI(api_key=api_key)
            logger.info(f"已初始化 OpenAI 客户端，模型: {self.model}")

        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

    def _init_gemini(self):
        """初始化 Gemini 客户端"""
        try:
            import google.generativeai as genai

            api_key = self.api_key or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("未找到 GEMINI_API_KEY")

            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel('gemini-pro')
            logger.info(f"已初始化 Gemini 客户端")

        except ImportError:
            raise ImportError("请安装 google-generativeai: pip install google-generativeai")

    def generate(self, prompt_type: str, context: Dict,
                 temperature: float = 0.7, max_tokens: int = 800) -> str:
        """
        生成文案

        Args:
            prompt_type: Prompt 类型 ("btc_analysis", "macro_analysis", etc.)
            context: 上下文数据字典
            temperature: 生成温度
            max_tokens: 最大 token 数

        Returns:
            生成的文案
        """
        if prompt_type not in PROMPTS:
            raise ValueError(f"未知的 prompt 类型: {prompt_type}")

        # 格式化 prompt
        prompt = PROMPTS[prompt_type].format(**context)

        logger.info(f"正在生成文案: {prompt_type}, 模型: {self.model}")

        try:
            if self.model.startswith("gpt"):
                return self._generate_openai(prompt, temperature, max_tokens)
            else:
                return self._generate_gemini(prompt, temperature, max_tokens)
        except Exception as e:
            logger.error(f"文案生成失败: {e}")
            raise

    def _generate_openai(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """使用 OpenAI 生成"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一位专业的加密货币分析师，擅长撰写简洁、数据驱动的市场分析。"},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        content = response.choices[0].message.content.strip()
        logger.info(f"OpenAI 生成完成，token 使用: {response.usage.total_tokens}")

        return content

    def _generate_gemini(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """使用 Gemini 生成"""
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        response = self.client.generate_content(
            prompt,
            generation_config=generation_config
        )

        content = response.text.strip()
        logger.info(f"Gemini 生成完成")

        return content

    def generate_batch(self, tasks: List[Dict]) -> Dict[str, str]:
        """
        批量生成文案

        Args:
            tasks: 任务列表，每个任务包含 {"type": "...", "context": {...}}

        Returns:
            {"type1": "content1", "type2": "content2", ...}
        """
        results = {}

        for task in tasks:
            prompt_type = task["type"]
            context = task["context"]

            try:
                content = self.generate(prompt_type, context)
                results[prompt_type] = content
                logger.info(f"✅ {prompt_type} 生成成功")
            except Exception as e:
                logger.error(f"❌ {prompt_type} 生成失败: {e}")
                results[prompt_type] = f"[生成失败: {str(e)}]"

        return results


class ContentCache:
    """文案缓存管理"""

    def __init__(self, cache_dir: str = "output/content"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def save(self, content: Dict[str, str], version: Optional[str] = None) -> str:
        """
        保存文案

        Args:
            content: {"section1": "text1", ...}
            version: 版本号（不提供则自动生成时间戳版本）

        Returns:
            保存的文件路径
        """
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"draft_{version}.json"
        filepath = os.path.join(self.cache_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "version": version,
                "timestamp": datetime.now().isoformat(),
                "content": content
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"文案已保存: {filepath}")
        return filepath

    def load(self, version: str) -> Dict:
        """加载指定版本的文案"""
        filename = f"draft_{version}.json"
        filepath = os.path.join(self.cache_dir, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"文案已加载: {filepath}")
        return data

    def list_versions(self) -> List[Dict]:
        """列出所有版本"""
        import glob

        files = glob.glob(os.path.join(self.cache_dir, "draft_*.json"))
        versions = []

        for filepath in sorted(files, reverse=True):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    versions.append({
                        "version": data["version"],
                        "timestamp": data["timestamp"],
                        "filepath": filepath
                    })
            except Exception as e:
                logger.warning(f"无法读取文件 {filepath}: {e}")

        return versions


def prepare_btc_context(price_data: Dict, technical_data: Optional[Dict] = None,
                        macro_data: Optional[Dict] = None) -> Dict:
    """
    准备 BTC 分析的上下文数据

    Args:
        price_data: {"dates": [...], "close": [...]}
        technical_data: 技术指标数据
        macro_data: 宏观数据

    Returns:
        格式化的上下文字典
    """
    prices = price_data["close"]

    current_price = prices[-1]
    weekly_change = ((prices[-1] - prices[-7]) / prices[-7] * 100) if len(prices) >= 7 else 0
    high_30d = max(prices)
    low_30d = min(prices)

    # 技术指标
    if technical_data:
        tech_indicators = "\n".join([f"- {k}: {v}" for k, v in technical_data.items()])
    else:
        tech_indicators = "- MA7: 暂无数据\n- MA30: 暂无数据"

    # 宏观背景
    if macro_data:
        macro_context = f"美元指数: {macro_data.get('dxy', 'N/A')}, 美债收益率: {macro_data.get('us10y', 'N/A')}%"
    else:
        macro_context = "宏观数据暂无"

    return {
        "current_price": current_price,
        "weekly_change": weekly_change,
        "high_30d": high_30d,
        "low_30d": low_30d,
        "technical_indicators": tech_indicators,
        "macro_context": macro_context
    }


def prepare_macro_context(macro_data: Dict) -> Dict:
    """准备宏观分析的上下文数据"""

    def calc_change(data_dict):
        """计算周变化"""
        close = data_dict.get("close", [])
        if len(close) >= 7:
            return ((close[-1] - close[-7]) / close[-7] * 100)
        return 0.0

    return {
        "dxy_current": macro_data.get("dxy", {}).get("close", [0])[-1],
        "dxy_change": calc_change(macro_data.get("dxy", {})),
        "us10y_current": macro_data.get("us10y", {}).get("close", [0])[-1],
        "us10y_change": calc_change(macro_data.get("us10y", {})) * 100,  # 转换为 bps
        "sp500_change": calc_change(macro_data.get("sp500", {})),
        "nvda_change": calc_change(macro_data.get("nvda", {})),
        "coin_change": calc_change(macro_data.get("coin", {}))
    }
