from modules.agent_graph import run_report_generation
from datetime import datetime
import json

# 运行工作流
final_state = run_report_generation("2024-12-09 ~ 2024-12-15", verbose=False)

# 保存输出
content = final_state.get("reviewed_content", {})
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

print("=" * 60)
print("📝 生成的文案内容")
print("=" * 60)

for key, text in content.items():
    print(f"\n## {key.upper()}\n")
    print(text)
    print("\n" + "-" * 60)

# 保存到文件
with open(f"output/content/btc_report_{timestamp}.md", 'w', encoding='utf-8') as f:
    f.write(f"# Crypto 投研周报 (含 BTC 模块)\n\n")
    f.write(f"**报告周期**: 2024-12-09 ~ 2024-12-15\n")
    f.write(f"**生成时间**: {timestamp}\n")
    f.write(f"**质量评分**: {final_state.get('quality_score', 0):.1f}/100\n\n")
    f.write("---\n\n")
    
    if "macro_analysis" in content:
        f.write("## 宏观环境分析\n\n")
        f.write(content["macro_analysis"] + "\n\n---\n\n")
    
    if "btc_analysis" in content:
        f.write("## BTC 市场分析\n\n")
        f.write(content["btc_analysis"] + "\n\n---\n\n")
    
    f.write("*本报告由 Multi-Agent 系统自动生成*\n")

print(f"\n✅ 报告已保存至: output/content/btc_report_{timestamp}.md")
