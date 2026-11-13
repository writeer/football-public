# -*- coding: utf-8 -*-
"""
竞彩Agent — 主入口
用法:
    python run_agent.py --input matches.json --output report.html
    python run_agent.py --demo  # 使用示例数据运行
"""

import argparse
import json
import os
import sys

# 确保可以导入lottery_agent包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lottery_agent import LotteryAgent, ReportGenerator


def load_matches(path):
    """加载比赛数据"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def demo_data():
    """示例数据 — 模拟体彩4场比赛"""
    return [
        {
            "match_id": "201",
            "league": "欧冠",
            "home_team": "巴黎圣日耳曼",
            "away_team": "曼城",
            "odds_home": 2.45,
            "odds_draw": 3.40,
            "odds_away": 2.60,
            "home_data": {
                "avg_scored": 2.1,
                "avg_conceded": 1.0,
                "fifa_rank": 5,
                "matches": 15,
                "xg_avg": 1.8
            },
            "away_data": {
                "avg_scored": 2.3,
                "avg_conceded": 0.9,
                "fifa_rank": 2,
                "matches": 15,
                "xg_avg": 2.0
            },
            "injuries": [],
            "notes": "欧冠淘汰赛"
        },
        {
            "match_id": "202",
            "league": "英超",
            "home_team": "利物浦",
            "away_team": "阿森纳",
            "odds_home": 1.95,
            "odds_draw": 3.50,
            "odds_away": 3.60,
            "home_data": {
                "avg_scored": 2.4,
                "avg_conceded": 0.8,
                "fifa_rank": 4,
                "matches": 20,
                "xg_avg": 2.2
            },
            "away_data": {
                "avg_scored": 2.0,
                "avg_conceded": 1.2,
                "fifa_rank": 8,
                "matches": 20,
                "xg_avg": 1.9
            },
            "injuries": [
                {"team": "home", "player": "萨拉赫", "position": "forward", "importance": "core"}
            ],
            "notes": "英超焦点战"
        },
        {
            "match_id": "203",
            "league": "意甲",
            "home_team": "尤文图斯",
            "away_team": "AC米兰",
            "odds_home": 2.20,
            "odds_draw": 3.10,
            "odds_away": 3.20,
            "home_data": {
                "avg_scored": 1.6,
                "avg_conceded": 0.7,
                "fifa_rank": 12,
                "matches": 18,
                "xg_avg": 1.5
            },
            "away_data": {
                "avg_scored": 1.8,
                "avg_conceded": 1.1,
                "fifa_rank": 15,
                "matches": 18,
                "xg_avg": 1.7
            },
            "injuries": [],
            "notes": "意甲强强对话"
        },
        {
            "match_id": "204",
            "league": "德甲",
            "home_team": "拜仁慕尼黑",
            "away_team": "多特蒙德",
            "odds_home": 1.55,
            "odds_draw": 4.20,
            "odds_away": 5.00,
            "home_data": {
                "avg_scored": 2.8,
                "avg_conceded": 1.0,
                "fifa_rank": 1,
                "matches": 16,
                "xg_avg": 2.5
            },
            "away_data": {
                "avg_scored": 2.1,
                "avg_conceded": 1.4,
                "fifa_rank": 10,
                "matches": 16,
                "xg_avg": 1.9
            },
            "injuries": [],
            "notes": "德甲国家德比"
        }
    ]


def main():
    parser = argparse.ArgumentParser(description='竞彩Agent — 足球比赛全方位分析系统')
    parser.add_argument('--input', '-i', type=str, help='输入JSON文件路径')
    parser.add_argument('--output', '-o', type=str, default='lottery_report.html', help='输出HTML报告路径')
    parser.add_argument('--ticket', '-t', type=str, help='彩票期号')
    parser.add_argument('--demo', action='store_true', help='使用示例数据运行')
    args = parser.parse_args()

    # 加载数据
    if args.demo:
        print("[竞彩Agent] 使用示例数据运行...")
        matches = demo_data()
    elif args.input:
        print(f"[竞彩Agent] 加载数据: {args.input}")
        matches = load_matches(args.input)
    else:
        print("[竞彩Agent] 请提供 --input 文件或使用 --demo 运行示例")
        print("示例用法:")
        print("  python run_agent.py --demo")
        print("  python run_agent.py --input my_matches.json --output report.html")
        sys.exit(1)

    # 创建Agent并分析
    ticket_id = args.ticket or "DEMO"
    agent = LotteryAgent(matches, ticket_id=ticket_id)

    # 生成报告数据
    report_data = agent.generate_report()

    # 生成HTML报告
    generator = ReportGenerator(report_data)
    output_path = args.output
    generator.generate_html(output_path)

    # 打印摘要
    summary = report_data['summary']
    print("\n" + "="*60)
    print(f"📊 竞彩分析完成 — 彩票期号: {ticket_id}")
    print("="*60)
    print(f"总场次: {summary['total_matches']}")
    print(f"高置信度: {len(summary['high_confidence'])} | 中置信度: {len(summary['medium_confidence'])} | 低置信度: {len(summary['low_confidence'])}")
    print(f"方向分布: 主胜{summary['direction_distribution'].get('主胜',0)} | 平局{summary['direction_distribution'].get('平局',0)} | 客胜{summary['direction_distribution'].get('客胜',0)}")

    if summary['divergence_alerts']:
        print(f"\n⚠️ 模型分歧预警 ({len(summary['divergence_alerts'])}场):")
        for alert in summary['divergence_alerts']:
            print(f"  [{alert['match_id']}] {alert['match']}: {alert['direction']} 分歧{alert['divergence']:+.1%}")

    parlay = report_data.get('parlay_suggestions', {})
    if parlay.get('conservative'):
        print(f"\n🔗 稳健串关建议:")
        for sug in parlay['conservative']:
            print(f"  {sug['type']} | 组合概率: {sug['combined_prob']:.1%} | 赔率: {sug['combined_odds']:.2f}")

    print(f"\n✅ 报告已保存: {output_path}")
    print("="*60)


if __name__ == '__main__':
    main()
