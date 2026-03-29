"""
配置检查器模块
处理 Claude Code 配置文件的分析和验证
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


class ConfigurationChecker:
    """检查 Claude Code 配置文件的安全问题"""

    def __init__(self, claude_dir: str, workspace_dir: str):
        self.claude_dir = Path(claude_dir)
        self.workspace_dir = Path(workspace_dir)

    async def check(self) -> Dict[str, Any]:
        """运行配置检查"""
        issues = []
        score = 0

        # Check if Claude directory exists
        if not self.claude_dir.exists():
            issues.append({
                'severity': 'HIGH',
                'check': 'claude_dir_missing',
                'message': f'未找到 Claude Code 目录: {self.claude_dir}',
                'location': str(self.claude_dir)
            })
            return {'score': -10, 'issues': issues}

        # Check settings files
        settings_files = [
            self.claude_dir / 'settings.json',
            self.claude_dir / 'settings.local.json'
        ]

        for settings_file in settings_files:
            if settings_file.exists():
                try:
                    with open(settings_file, 'r') as f:
                        content = f.read()
                        settings = json.loads(content)

                        # Check for sensitive data in settings
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

        # Check for project-specific .claude directories
        project_claude_dirs = list(self.workspace_dir.glob('**/.claude'))
        if len(project_claude_dirs) > 5:  # More than 5 project configs might be excessive
            issues.append({
                'severity': 'MEDIUM',
                'check': 'many_project_configs',
                'message': f'找到 {len(project_claude_dirs)} 个项目特定的 .claude 目录',
                'location': str(self.workspace_dir)
            })
            score -= 5

        return {'score': score, 'issues': issues}