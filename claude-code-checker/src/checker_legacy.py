#!/usr/bin/env python3
"""
Claude Code 安全检测器
企业级安全配置分析器，用于 Claude Code 环境
"""

import os
import sys
import json
import re
import stat
import platform
import subprocess
import datetime
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional

class SecurityChecker:
    def __init__(self, config=None):
        if config is None:
            config = {}

        self.config = {
            'claude_dir': config.get('claude_dir', str(Path.home() / '.claude')),
            'workspace_dir': config.get('workspace_dir', os.getcwd()),
            **config
        }

        self.check_id = self.generate_check_id()
        self.issues = []

    def generate_check_id(self):
        """生成唯一检查ID"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        random_part = str(uuid.uuid4())[:8]
        return f"CCSC-{timestamp}-{random_part}".upper()

    async def run_full_check(self):
        """运行所有安全检查"""
        start_time = datetime.datetime.now()
        print(f"[{self.check_id}] 开始 Claude Code 安全检查")

        result = {
            'check_id': self.check_id,
            'timestamp': datetime.datetime.now().isoformat() + 'Z',
            'environment': self.get_environment_info(),
            'security_score': 100,
            'grade': 'A',
            'checks': {},
            'recommendations': []
        }

        try:
            # 运行所有检查阶段
            result['checks']['configuration'] = await self.check_configuration()
            result['checks']['credentials'] = await self.check_credentials()
            result['checks']['permissions'] = await self.check_permissions()
            result['checks']['network'] = await self.check_network()
            result['checks']['processes'] = await self.check_processes()

            # 计算安全分数
            result['security_score'] = self.calculate_score(result['checks'])
            result['grade'] = self.get_grade(result['security_score'])

            # 生成建议
            result['recommendations'] = self.generate_recommendations(result['checks'])

        except Exception as e:
            print(f"[{self.check_id}] 检查错误: {e}")
            result['error'] = str(e)

        duration = datetime.datetime.now() - start_time
        result['duration_ms'] = int(duration.total_seconds() * 1000)
        print(f"[{self.check_id}] 安全检查完成: {result['grade']} ({result['security_score']})")

        return result

    def get_environment_info(self):
        """获取 Claude Code 环境信息"""
        info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'claude_dir': self.config['claude_dir'],
            'workspace_dir': self.config['workspace_dir']
        }

        # 检查 Claude Code 是否在容器中运行
        if os.path.exists('/.dockerenv'):
            info['deployment'] = 'docker'
        elif os.path.exists('/run/.containerenv'):
            info['deployment'] = 'podman'
        else:
            info['deployment'] = 'local'

        # 如果可能，尝试获取 Claude Code 版本
        try:
            # 这是一个占位符 - 实际的版本检测需要 Claude Code 特定的逻辑
            claude_config = Path(self.config['claude_dir']) / 'settings.json'
            if claude_config.exists():
                with open(claude_config, 'r') as f:
                    settings = json.load(f)
                    if 'version' in settings:
                        info['claude_version'] = settings['version']
        except:
            pass

        return info

    async def check_configuration(self):
        """阶段 1: 配置分析"""
        issues = []
        score = 0

        claude_dir = Path(self.config['claude_dir'])

        # 检查 Claude 目录是否存在
        if not claude_dir.exists():
            issues.append({
                'severity': 'HIGH',
                'check': 'claude_dir_missing',
                'message': f'未找到 Claude Code 目录: {claude_dir}',
                'location': str(claude_dir)
            })
            return {'score': -10, 'issues': issues}

        # 检查设置文件
        settings_files = [
            claude_dir / 'settings.json',
            claude_dir / 'settings.local.json'
        ]

        for settings_file in settings_files:
            if settings_file.exists():
                try:
                    with open(settings_file, 'r') as f:
                        content = f.read()
                        settings = json.loads(content)

                        # 检查设置中的敏感数据
                        sensitive_patterns = [
                            r'api[_-]?key["\s:=]+["\'][a-zA-Z0-9]{16,}["\']',
                            r'secret["\s:=]+["\'][a-zA-Z0-9]{16,}["\']',
                            r'token["\s:=]+["\'][a-zA-Z0-9]{16,}["\']',
                            r'password["\s:=]+["\'][^"\']+["\']',
                        ]

                        for pattern in sensitive_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                issues.append({
                                    'severity': 'CRITICAL',
                                    'check': 'sensitive_data_in_config',
                                    'message': f'在 {settings_file.name} 中发现敏感数据',
                                    'location': str(settings_file)
                                })
                                score -= 20
                                break

                except json.JSONDecodeError as e:
                    issues.append({
                        'severity': 'MEDIUM',
                        'check': 'config_parse_error',
                        'message': f'解析 {settings_file.name} 失败: {e}',
                        'location': str(settings_file)
                    })
                    score -= 5

        # 检查项目特定的 .claude 目录
        project_claude_dirs = list(Path(self.config['workspace_dir']).glob('**/.claude'))
        if len(project_claude_dirs) > 5:  # 超过5个项目配置可能过多
            issues.append({
                'severity': 'MEDIUM',
                'check': 'many_project_configs',
                'message': f'发现 {len(project_claude_dirs)} 个项目特定的 .claude 目录',
                'location': self.config['workspace_dir']
            })
            score -= 5

        return {'score': score, 'issues': issues}

    async def check_credentials(self):
        """阶段 2: 凭证暴露检测"""
        issues = []
        score = 0

        credential_patterns = [
            # API 密钥
            (r'sk-[a-zA-Z0-9]{20,}', 'openai_key', 'CRITICAL'),
            (r'sk-ant-[a-zA-Z0-9_-]{20,}', 'anthropic_key', 'CRITICAL'),
            (r'AKIA[0-9A-Z]{16}', 'aws_key', 'CRITICAL'),
            (r'ghp_[a-zA-Z0-9]{36}', 'github_token', 'CRITICAL'),
            (r'gho_[a-zA-Z0-9]{36}', 'github_oauth', 'CRITICAL'),

            # 私钥
            (r'-----BEGIN.*PRIVATE KEY-----', 'private_key', 'CRITICAL'),

            # 通用密钥
            (r'api[_-]?key["\s:=]+["\'][a-zA-Z0-9]{16,}["\']', 'api_key', 'HIGH'),
            (r'secret["\s:=]+["\'][a-zA-Z0-9]{16,}["\']', 'secret', 'HIGH'),
            (r'password["\s:=]+["\'][^"\']+["\']', 'password', 'HIGH'),
        ]

        # 检查 Claude 目录
        claude_dir = Path(self.config['claude_dir'])
        if claude_dir.exists():
            for file_path in claude_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                            for pattern, key_type, severity in credential_patterns:
                                if re.search(pattern, content):
                                    issues.append({
                                        'severity': severity,
                                        'check': 'credential_exposed',
                                        'message': f'暴露的 {key_type} 在 {file_path.relative_to(claude_dir)}',
                                        'location': str(file_path)
                                    })

                                    if severity == 'CRITICAL':
                                        score -= 20
                                    elif severity == 'HIGH':
                                        score -= 10
                                    break  # Stop checking this file after first match

                    except (UnicodeDecodeError, PermissionError, OSError):
                        # Skip binary files or files we can't read
                        continue

        # Check for .env files in workspace
        env_files = list(Path(self.config['workspace_dir']).glob('**/.env*'))
        for env_file in env_files:
            issues.append({
                'severity': 'MEDIUM',
                'check': 'env_file_found',
                'message': f'.env file found in workspace: {env_file.relative_to(self.config["workspace_dir"])}',
                'location': str(env_file)
            })
            score -= 5

        return {'score': score, 'issues': issues}

    async def check_permissions(self):
        """Phase 3: Permission Modeling"""
        issues = []
        score = 0

        claude_dir = Path(self.config['claude_dir'])

        if claude_dir.exists():
            # Check Claude directory permissions
            try:
                dir_stat = os.stat(str(claude_dir))
                dir_mode = dir_stat.st_mode

                # Check if directory is world-writable
                if dir_mode & stat.S_IWOTH:
                    issues.append({
                        'severity': 'CRITICAL',
                        'check': 'claude_dir_world_writable',
                        'message': 'Claude Code directory is world-writable',
                        'location': str(claude_dir)
                    })
                    score -= 20

                # Check if directory is world-readable (less critical but still concerning)
                if dir_mode & stat.S_IROTH:
                    issues.append({
                        'severity': 'HIGH',
                        'check': 'claude_dir_world_readable',
                        'message': 'Claude Code directory is world-readable',
                        'location': str(claude_dir)
                    })
                    score -= 15

            except OSError as e:
                issues.append({
                    'severity': 'MEDIUM',
                    'check': 'permission_check_error',
                    'message': f'Failed to check directory permissions: {e}'
                })

        # Check settings files permissions
        settings_files = [
            claude_dir / 'settings.json',
            claude_dir / 'settings.local.json'
        ]

        for settings_file in settings_files:
            if settings_file.exists():
                try:
                    file_stat = os.stat(str(settings_file))
                    file_mode = file_stat.st_mode

                    # Check if file is world-readable
                    if file_mode & stat.S_IROTH:
                        issues.append({
                            'severity': 'HIGH',
                            'check': 'config_file_world_readable',
                            'message': f'Configuration file is world-readable: {settings_file.name}',
                            'location': str(settings_file)
                        })
                        score -= 15

                    # Check if file is world-writable
                    if file_mode & stat.S_IWOTH:
                        issues.append({
                            'severity': 'CRITICAL',
                            'check': 'config_file_world_writable',
                            'message': f'Configuration file is world-writable: {settings_file.name}',
                            'location': str(settings_file)
                        })
                        score -= 20

                except OSError:
                    pass

        # Check if running with excessive privileges
        if platform.system() == 'Windows':
            # On Windows, check if running as Administrator
            try:
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
                if is_admin:
                    issues.append({
                        'severity': 'CRITICAL',
                        'check': 'running_as_admin',
                        'message': 'Claude Code is running with Administrator privileges',
                        'location': 'process'
                    })
                    score -= 25
            except:
                pass
        else:
            # On Unix-like systems, check if running as root
            if os.geteuid() == 0:
                issues.append({
                    'severity': 'CRITICAL',
                    'check': 'running_as_root',
                    'message': 'Claude Code is running as root user',
                    'location': 'process'
                })
                score -= 25

        return {'score': score, 'issues': issues}

    async def check_network(self):
        """Phase 4: Network Security Analysis"""
        issues = []
        score = 0

        # Check for listening ports (simplified check)
        if platform.system() in ['Linux', 'Darwin']:  # Linux or macOS
            try:
                result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=5)
                listening_ports = []

                for line in result.stdout.split('\n'):
                    if 'LISTEN' in line and '127.0.0.1' not in line and '::1' not in line:
                        # Non-localhost listening port
                        listening_ports.append(line.strip())

                if len(listening_ports) > 3:  # More than 3 non-localhost listening ports
                    issues.append({
                        'severity': 'MEDIUM',
                        'check': 'many_listening_ports',
                        'message': f'Found {len(listening_ports)} non-localhost listening ports',
                        'location': 'network'
                    })
                    score -= 5

            except (subprocess.SubprocessError, FileNotFoundError):
                pass

        # Check for suspicious network patterns in configuration
        claude_dir = Path(self.config['claude_dir'])
        settings_file = claude_dir / 'settings.json'

        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)

                    # Check for proxy settings that might be insecure
                    if 'proxy' in settings or 'http_proxy' in str(settings):
                        issues.append({
                            'severity': 'MEDIUM',
                            'check': 'proxy_configured',
                            'message': 'Proxy configuration detected - ensure it uses HTTPS',
                            'location': str(settings_file)
                        })
                        score -= 5

            except (json.JSONDecodeError, KeyError):
                pass

        return {'score': score, 'issues': issues}

    async def check_processes(self):
        """Phase 5: Process Security Analysis"""
        issues = []
        score = 0

        # Check for suspicious processes (simplified check)
        suspicious_process_patterns = [
            'nc', 'ncat', 'socat', 'netcat',  # Network tools
            'keylogger', 'sniffer', 'packet',  # Monitoring tools
        ]

        if platform.system() in ['Linux', 'Darwin']:
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)

                for line in result.stdout.split('\n'):
                    for pattern in suspicious_process_patterns:
                        if pattern in line.lower():
                            issues.append({
                                'severity': 'HIGH',
                                'check': 'suspicious_process',
                                'message': f'Suspicious process found: {pattern}',
                                'location': 'processes'
                            })
                            score -= 10
                            break

            except (subprocess.SubprocessError, FileNotFoundError):
                pass

        return {'score': score, 'issues': issues}

    def calculate_score(self, checks):
        """Calculate security score from all checks"""
        score = 100

        for category, data in checks.items():
            score += data.get('score', 0)

        return max(0, min(100, score))

    def get_grade(self, score):
        """Get grade from score"""
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

    def generate_recommendations(self, checks):
        """Generate recommendations from issues"""
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

        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))

        return recommendations

    def print_report(self, result):
        """Print formatted security report"""
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║        🔒 CLAUDE CODE SECURITY CHECK REPORT v1.0.0          ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║ Check ID: {result['check_id']:45} ║")
        print(f"║ Environment: {result['environment']['platform']:40} ║")
        print(f"║ Time: {result['timestamp']:43} ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()

        # Print each check category
        for category, data in result['checks'].items():
            category_name = category.upper().replace('_', ' ')
            score = data.get('score', 0)

            print(f"▶ {category_name} [{score}]")

            for issue in data.get('issues', []):
                severity_icon = '⚠️' if issue['severity'] in ['CRITICAL', 'HIGH'] else '📝'
                print(f"  {severity_icon} [{issue['severity']}] {issue['message']}")

            if not data.get('issues'):
                print(f"  ✓ No issues found")

            print()

        # Print summary
        print("╔══════════════════════════════════════════════════════════════╗")
        print(f"║ SECURITY GRADE: {result['grade']} ({result['security_score']}/100){' ':>24} ║")
        print("╠══════════════════════════════════════════════════════════════╣")

        if result['recommendations']:
            print("║ RECOMMENDATIONS:                                           ║")
            for i, rec in enumerate(result['recommendations'][:5], 1):
                print(f"║ {i}. [{rec['priority']}] {rec['message'][:50]:50} ║")

        print("╚══════════════════════════════════════════════════════════════╝")

        # Also print JSON if requested
        if '--json' in sys.argv:
            print("\n" + json.dumps(result, indent=2))


async def main():
    """Main entry point"""
    import asyncio

    print("Running Claude Code Security Check...")

    checker = SecurityChecker()
    result = await checker.run_full_check()

    checker.print_report(result)

    # Also save JSON report if requested
    if '--save' in sys.argv:
        report_file = f"security-report-{checker.check_id}.json"
        with open(report_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nReport saved to: {report_file}")


if __name__ == '__main__':
    import asyncio

    # Handle command line arguments
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Claude Code Security Checker")
        print("Usage: python3 checker.py [options]")
        print("\nOptions:")
        print("  --full-check     Run all security checks (default)")
        print("  --json           Output JSON format")
        print("  --save           Save JSON report to file")
        print("  --help, -h       Show this help")
        sys.exit(0)

    asyncio.run(main())