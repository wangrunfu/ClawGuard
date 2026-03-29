"""
报告生成器模块
格式化和输出安全报告
"""

import json
import sys
from typing import Dict, Any


class ReportGenerator:
    """生成格式化的安全报告"""

    @staticmethod
    def print_report(result: Dict[str, Any]) -> None:
        """打印格式化的安全报告"""
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║        🔒 CLAUDE CODE 安全检查报告 v1.0.0          ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║ 检查ID: {result['check_id']:45} ║")
        print(f"║ 环境: {result['environment']['platform']:40} ║")
        print(f"║ 时间: {result['timestamp']:43} ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()

        # 打印每个检查类别
        for category, data in result['checks'].items():
            category_name = category.upper().replace('_', ' ')
            score = data.get('score', 0)

            print(f"▶ {category_name} [{score}]")

            for issue in data.get('issues', []):
                severity_icon = '⚠️' if issue['severity'] in ['CRITICAL', 'HIGH'] else '📝'
                print(f"  {severity_icon} [{issue['severity']}] {issue['message']}")

            if not data.get('issues'):
                print(f"  ✓ 未发现问题")

            print()

        # 打印摘要
        print("╔══════════════════════════════════════════════════════════════╗")
        print(f"║ 安全等级: {result['grade']} ({result['security_score']}/100){' ':>24} ║")
        print("╠══════════════════════════════════════════════════════════════╣")

        if result['recommendations']:
            print("║ 建议:                                           ║")
            for i, rec in enumerate(result['recommendations'][:5], 1):
                print(f"║ {i}. [{rec['priority']}] {rec['message'][:50]:50} ║")

        print("╚══════════════════════════════════════════════════════════════╝")

        # 如果请求，也打印 JSON
        if '--json' in sys.argv:
            print("\n" + json.dumps(result, indent=2))

    @staticmethod
    def save_report(result: Dict[str, Any], filename: str) -> None:
        """保存报告到 JSON 文件"""
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)

    @staticmethod
    def calculate_score(checks: Dict[str, Any]) -> int:
        """从所有检查计算安全分数"""
        score = 100

        for category, data in checks.items():
            score += data.get('score', 0)

        return max(0, min(100, score))

    @staticmethod
    def get_grade(score: int) -> str:
        """从分数获取等级"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    @staticmethod
    def generate_recommendations(checks: Dict[str, Any]) -> list:
        """从问题生成建议"""
        recommendations = []
        seen_keys = set()

        for category, data in checks.items():
            for issue in data.get('issues', []):
                key = f"{category}-{issue['check']}"
                if key not in seen_keys:
                    seen_keys.add(key)

                    if issue['severity'] in ['CRITICAL', 'HIGH']:
                        recommendations.append({
                            'priority': issue['severity'],
                            'message': issue['message'],
                            'category': category
                        })

        # 按优先级排序
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))

        return recommendations