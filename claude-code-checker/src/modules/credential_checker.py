"""
凭证检查器模块
检测文件中暴露的凭证和密钥
"""

import re
from pathlib import Path
from typing import Dict, List, Any


class CredentialChecker:
    """扫描暴露的凭证和密钥"""

    def __init__(self, claude_dir: str, workspace_dir: str):
        self.claude_dir = Path(claude_dir)
        self.workspace_dir = Path(workspace_dir)
        self.credential_patterns = [
            # API Keys
            (r'sk-[a-zA-Z0-9]{20,}', 'openai_key', 'CRITICAL'),
            (r'sk-ant-[a-zA-Z0-9_-]{20,}', 'anthropic_key', 'CRITICAL'),
            (r'AKIA[0-9A-Z]{16}', 'aws_key', 'CRITICAL'),
            (r'ghp_[a-zA-Z0-9]{36}', 'github_token', 'CRITICAL'),
            (r'gho_[a-zA-Z0-9]{36}', 'github_oauth', 'CRITICAL'),
            # Private Keys
            (r'-----BEGIN.*PRIVATE KEY-----', 'private_key', 'CRITICAL'),
            # Generic Secrets
            (r'api[_-]?key["\s:=]+["\'][a-zA-Z0-9]{16,}["\']', 'api_key', 'HIGH'),
            (r'secret["\s:=]+["\'][a-zA-Z0-9]{16,}["\']', 'secret', 'HIGH'),
            (r'password["\s:=]+["\'][^"\']+["\']', 'password', 'HIGH'),
        ]

    async def check(self) -> Dict[str, Any]:
        """运行凭证检查"""
        issues = []
        score = 0

        # Check Claude directory
        if self.claude_dir.exists():
            for file_path in self.claude_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                            for pattern, key_type, severity in self.credential_patterns:
                                if re.search(pattern, content):
                                    issues.append({
                                        'severity': severity,
                                        'check': 'credential_exposed',
                                        'message': f'暴露的 {key_type} 在 {file_path.relative_to(self.claude_dir)}',
                                        'location': str(file_path)
                                    })

                                    if severity == 'CRITICAL':
                                        score -= 20
                                    elif severity == 'HIGH':
                                        score -= 10
                                    break  # Stop checking this file after first match

                    except (UnicodeDecodeError, PermissionError, OSError):
                        # 跳过二进制文件或无法读取的文件
                        continue

        # 检查工作空间中的 .env 文件
        env_files = list(self.workspace_dir.glob('**/.env*'))
        for env_file in env_files:
            issues.append({
                'severity': 'MEDIUM',
                'check': 'env_file_found',
                'message': f'在工作空间中找到 .env 文件: {env_file.relative_to(self.workspace_dir)}',
                'location': str(env_file)
            })
            score -= 5

        return {'score': score, 'issues': issues}