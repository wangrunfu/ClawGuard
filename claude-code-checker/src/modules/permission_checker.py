"""
权限检查器模块
分析文件和目录权限
"""

import os
import stat
import platform
from pathlib import Path
from typing import Dict, Any


class PermissionChecker:
    """检查文件和目录权限"""

    def __init__(self, claude_dir: str):
        self.claude_dir = Path(claude_dir)

    async def check(self) -> Dict[str, Any]:
        """运行权限检查"""
        issues = []
        score = 0

        if self.claude_dir.exists():
            # Check Claude directory permissions
            try:
                dir_stat = os.stat(str(self.claude_dir))
                dir_mode = dir_stat.st_mode

                # 检查目录是否全局可写
                if dir_mode & stat.S_IWOTH:
                    issues.append({
                        'severity': 'CRITICAL',
                        'check': 'claude_dir_world_writable',
                        'message': 'Claude Code 目录全局可写',
                        'location': str(self.claude_dir)
                    })
                    score -= 20

                # 检查目录是否全局可读（不太关键但仍需关注）
                if dir_mode & stat.S_IROTH:
                    issues.append({
                        'severity': 'HIGH',
                        'check': 'claude_dir_world_readable',
                        'message': 'Claude Code 目录全局可读',
                        'location': str(self.claude_dir)
                    })
                    score -= 15

            except OSError as e:
                issues.append({
                    'severity': 'MEDIUM',
                    'check': 'permission_check_error',
                    'message': f'检查目录权限失败: {e}'
                })

        # 检查设置文件权限
        settings_files = [
            self.claude_dir / 'settings.json',
            self.claude_dir / 'settings.local.json'
        ]

        for settings_file in settings_files:
            if settings_file.exists():
                try:
                    file_stat = os.stat(str(settings_file))
                    file_mode = file_stat.st_mode

                    # 检查文件是否全局可读
                    if file_mode & stat.S_IROTH:
                        issues.append({
                            'severity': 'HIGH',
                            'check': 'config_file_world_readable',
                            'message': f'配置文件全局可读: {settings_file.name}',
                            'location': str(settings_file)
                        })
                        score -= 15

                    # 检查文件是否全局可写
                    if file_mode & stat.S_IWOTH:
                        issues.append({
                            'severity': 'CRITICAL',
                            'check': 'config_file_world_writable',
                            'message': f'配置文件全局可写: {settings_file.name}',
                            'location': str(settings_file)
                        })
                        score -= 20

                except OSError:
                    pass

        # 检查是否以过高权限运行
        if platform.system() == 'Windows':
            # 在 Windows 上，检查是否以管理员身份运行
            try:
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
                if is_admin:
                    issues.append({
                        'severity': 'CRITICAL',
                        'check': 'running_as_admin',
                        'message': 'Claude Code 正在以管理员权限运行',
                        'location': 'process'
                    })
                    score -= 25
            except:
                pass
        else:
            # 在类 Unix 系统上，检查是否以 root 用户运行
            if os.geteuid() == 0:
                issues.append({
                    'severity': 'CRITICAL',
                    'check': 'running_as_root',
                    'message': 'Claude Code is running as root user',
                    'location': 'process'
                })
                score -= 25

        return {'score': score, 'issues': issues}