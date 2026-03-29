#!/usr/bin/env python3
"""
Claude Code 安全检测器 - 主模块
企业级安全配置分析器，专为 Claude Code 环境设计
"""

import datetime
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from modules.configuration_checker import ConfigurationChecker
from modules.credential_checker import CredentialChecker
# Import modules
from modules.environment_info import EnvironmentInfo
from modules.network_checker import NetworkChecker
from modules.permission_checker import PermissionChecker
from modules.process_checker import ProcessChecker
from modules.report_generator import ReportGenerator


class SecurityChecker:
    """主安全检测类，协调所有检查"""

    def __init__(self, config: Optional[Dict] = None):
        if config is None:
            config = {}

        self.config = {
            'claude_dir': config.get('claude_dir', str(Path.home() / '.claude')),
            'workspace_dir': config.get('workspace_dir', os.getcwd()),
            **config
        }

        self.check_id = self.generate_check_id()

        # Initialize modules
        self.environment_info = EnvironmentInfo(
            self.config['claude_dir'],
            self.config['workspace_dir']
        )
        self.configuration_checker = ConfigurationChecker(
            self.config['claude_dir'],
            self.config['workspace_dir']
        )
        self.credential_checker = CredentialChecker(
            self.config['claude_dir'],
            self.config['workspace_dir']
        )
        self.permission_checker = PermissionChecker(
            self.config['claude_dir']
        )
        self.network_checker = NetworkChecker(
            self.config['claude_dir']
        )
        self.process_checker = ProcessChecker()
        self.report_generator = ReportGenerator()

    def generate_check_id(self):
        """生成唯一的检查ID"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        random_part = str(uuid.uuid4())[:8]
        return f"CCSC-{timestamp}-{random_part}".upper()

    async def run_full_check(self) -> Dict[str, Any]:
        """运行所有安全检查"""
        start_time = datetime.datetime.now()
        print(f"[{self.check_id}] 开始 Claude Code 安全检查")

        result = {
            'check_id': self.check_id,
            'timestamp': datetime.datetime.now().isoformat() + 'Z',
            'environment': self.environment_info.get_info(),
            'security_score': 100,
            'grade': 'A',
            'checks': {},
            'recommendations': []
        }

        try:
            # Run all check phases
            result['checks']['configuration'] = await self.configuration_checker.check()
            result['checks']['credentials'] = await self.credential_checker.check()
            result['checks']['permissions'] = await self.permission_checker.check()
            result['checks']['network'] = await self.network_checker.check()
            result['checks']['processes'] = await self.process_checker.check()

            # Calculate security score
            result['security_score'] = self.report_generator.calculate_score(result['checks'])
            result['grade'] = self.report_generator.get_grade(result['security_score'])

            # Generate recommendations
            result['recommendations'] = self.report_generator.generate_recommendations(result['checks'])

        except Exception as e:
            print(f"[{self.check_id}] 检查错误: {e}")
            result['error'] = str(e)

        duration = datetime.datetime.now() - start_time
        result['duration_ms'] = int(duration.total_seconds() * 1000)
        print(f"[{self.check_id}] 安全检查完成: {result['grade']} ({result['security_score']})")

        return result

    def print_report(self, result: Dict[str, Any]) -> None:
        """打印格式化的安全报告"""
        self.report_generator.print_report(result)

    def save_report(self, result: Dict[str, Any], filename: Optional[str] = None) -> str:
        """保存报告到 JSON 文件"""
        if filename is None:
            filename = f"security-report-{self.check_id}.json"

        self.report_generator.save_report(result, filename)
        return filename