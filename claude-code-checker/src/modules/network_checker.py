"""
网络检查器模块
分析网络安全和监听端口
"""

import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any


class NetworkChecker:
    """检查网络安全设置"""

    def __init__(self, claude_dir: str):
        self.claude_dir = Path(claude_dir)

    async def check(self) -> Dict[str, Any]:
        """运行网络检查"""
        issues = []
        score = 0

        # 检查监听端口（简化检查）
        if platform.system() in ['Linux', 'Darwin']:  # Linux or macOS
            try:
                result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=5)
                listening_ports = []

                for line in result.stdout.split('\n'):
                    if 'LISTEN' in line and '127.0.0.1' not in line and '::1' not in line:
                        # 非本地主机监听端口
                        listening_ports.append(line.strip())

                if len(listening_ports) > 3:  # 超过3个非本地主机监听端口
                    issues.append({
                        'severity': 'MEDIUM',
                        'check': 'many_listening_ports',
                        'message': f'发现 {len(listening_ports)} 个非本地主机监听端口',
                        'location': 'network'
                    })
                    score -= 5

            except (subprocess.SubprocessError, FileNotFoundError):
                pass

        # 检查配置中的可疑网络模式
        settings_file = self.claude_dir / 'settings.json'

        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)

                    # 检查可能不安全的代理设置
                    if 'proxy' in settings or 'http_proxy' in str(settings):
                        issues.append({
                            'severity': 'MEDIUM',
                            'check': 'proxy_configured',
                            'message': '检测到代理配置 - 确保使用 HTTPS',
                            'location': str(settings_file)
                        })
                        score -= 5

            except (json.JSONDecodeError, KeyError):
                pass

        return {'score': score, 'issues': issues}