"""
环境信息模块
收集 Claude Code 环境信息
"""

import os
import json
import platform
from pathlib import Path
from typing import Dict, Any


class EnvironmentInfo:
    """获取 Claude Code 环境信息"""

    def __init__(self, claude_dir: str, workspace_dir: str):
        self.claude_dir = Path(claude_dir)
        self.workspace_dir = Path(workspace_dir)

    def get_info(self) -> Dict[str, Any]:
        """获取环境信息"""
        info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'claude_dir': str(self.claude_dir),
            'workspace_dir': str(self.workspace_dir)
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
            claude_config = self.claude_dir / 'settings.json'
            if claude_config.exists():
                with open(claude_config, 'r') as f:
                    settings = json.load(f)
                    if 'version' in settings:
                        info['claude_version'] = settings['version']
        except:
            pass

        return info