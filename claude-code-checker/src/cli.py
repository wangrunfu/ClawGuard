#!/usr/bin/env python3
"""
Claude Code 安全检测器 CLI
安全检查的命令行界面
"""

import sys
import asyncio
from security_checker import SecurityChecker


async def main():
    """主入口点"""
    print("正在运行 Claude Code 安全检查...")

    checker = SecurityChecker()
    result = await checker.run_full_check()

    checker.print_report(result)

    # 如果请求，也保存 JSON 报告
    if '--save' in sys.argv:
        report_file = checker.save_report(result)
        print(f"\n报告保存到: {report_file}")

    return result


def show_help():
    """显示帮助信息"""
    print("Claude Code 安全检测器")
    print("用法: python3 cli.py [选项]")
    print("\n选项:")
    print("  --full-check     运行所有安全检查（默认）")
    print("  --json           输出 JSON 格式")
    print("  --save           保存 JSON 报告到文件")
    print("  --help, -h       显示此帮助")
    print("\n示例:")
    print("  python3 cli.py                    # 运行完整安全检查")
    print("  python3 cli.py --save             # 运行并保存报告")
    print("  python3 cli.py --json             # 输出 JSON 格式")
    print("  python3 cli.py --help             # 显示此帮助")


if __name__ == '__main__':
    # 处理命令行参数
    if '--help' in sys.argv or '-h' in sys.argv:
        show_help()
        sys.exit(0)

    asyncio.run(main())