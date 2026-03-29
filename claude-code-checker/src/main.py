#!/usr/bin/env python3
"""
Claude Code 安全检测器 - 主入口点
此文件提供向后兼容性并方便访问安全检测器
"""

import sys
import asyncio

# Import from modular structure
from security_checker import SecurityChecker
from modules.report_generator import ReportGenerator


async def main_async():
    """主异步函数"""
    checker = SecurityChecker()
    result = await checker.run_full_check()

    # Check for JSON output flag
    if '--json' in sys.argv:
        import json
        print(json.dumps(result, indent=2))
    else:
        checker.print_report(result)

    # Save report if requested
    if '--save' in sys.argv:
        report_file = checker.save_report(result)
        print(f"\n报告保存到: {report_file}")

    return result


def main():
    """主入口点，包含参数处理"""
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Claude Code 安全检测器")
        print("用法: python3 main.py [选项]")
        print("\n选项:")
        print("  --full-check     运行所有安全检查（默认）")
        print("  --json           输出 JSON 格式")
        print("  --save           保存 JSON 报告到文件")
        print("  --help, -h       显示此帮助")
        print("\n替代方案: python3 cli.py [选项]")
        sys.exit(0)

    # Run the async main function
    asyncio.run(main_async())


if __name__ == '__main__':
    main()