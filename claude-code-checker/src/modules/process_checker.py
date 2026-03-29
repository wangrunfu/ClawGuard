"""
进程检查器模块
分析运行进程以发现安全问题
"""

import subprocess
import platform
from typing import Dict, Any


class ProcessChecker:
    """检查可疑进程"""

    def __init__(self):
        self.suspicious_process_patterns = [
            'nc', 'ncat', 'socat', 'netcat',  # 网络工具
            'keylogger', 'sniffer', 'packet',  # 监控工具
        ]

    async def check(self) -> Dict[str, Any]:
        """运行进程检查"""
        issues = []
        score = 0

        # 检查可疑进程（简化检查）
        if platform.system() in ['Linux', 'Darwin']:
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)

                for line in result.stdout.split('\n'):
                    for pattern in self.suspicious_process_patterns:
                        if pattern in line.lower():
                            issues.append({
                                'severity': 'HIGH',
                                'check': 'suspicious_process',
                                'message': f'发现可疑进程: {pattern}',
                                'location': 'processes'
                            })
                            score -= 10
                            break

            except (subprocess.SubprocessError, FileNotFoundError):
                pass

        return {'score': score, 'issues': issues}