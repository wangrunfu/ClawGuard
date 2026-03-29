# Claude Code 安全检测器

企业级安全配置分析器和运行时完整性验证工具，专为 Claude Code 环境设计。

## 概述

Claude Code 安全检测器 (CC-SC) 是一个专为 Claude Code 环境设计的模块化安全分析工具。它提供全面的安全态势评估，包括配置分析、凭证检测、权限建模和网络安全检查。

## 功能特性

- **配置分析**: 验证 Claude Code 设置文件的安全性
- **凭证检测**: 扫描暴露的 API 密钥、密钥和凭据
- **权限建模**: 检查文件和目录权限的安全性
- **网络安全**: 分析网络设置和监听端口
- **进程监控**: 检测可疑进程
- **安全评分**: 计算安全分数 (0-100) 并给出字母等级 (A+ 到 F)
- **模块化架构**: 可扩展、可维护的模块化设计

## 安装

### 前提条件
- Python 3.8 或更高版本
- 已安装并配置 Claude Code

### 设置
```bash
# 克隆或下载检测器
cd /path/to/claude-code-checker

# 无需安装 - 直接从源代码运行
```

## 快速开始

### 基本用法
```bash
# 运行完整安全检查
python src/main.py --full-check

# 运行并输出 JSON 格式
python src/main.py --json

# 运行并保存报告
python src/main.py --save

# 显示帮助
python src/main.py --help
```

### 其他入口点
```bash
# 使用 CLI 界面
python src/cli.py --full-check

# 作为模块导入（用于编程使用）
python -c "import sys; sys.path.insert(0, 'src'); from security_checker import SecurityChecker; import asyncio; asyncio.run(SecurityChecker().run_full_check())"
```

## 模块化架构

检测器采用模块化架构，便于维护和扩展：

```
src/
├── main.py                 # 主入口点
├── cli.py                  # 命令行界面
├── security_checker.py     # 主协调器
└── modules/                # 模块化组件
    ├── configuration_checker.py    # 配置分析
    ├── credential_checker.py       # 密钥检测
    ├── permission_checker.py       # 文件权限检查
    ├── network_checker.py          # 网络安全分析
    ├── process_checker.py          # 进程监控
    ├── report_generator.py         # 报告格式化
    └── environment_info.py         # 环境信息检测
```

### 使用独立模块

您可以编程方式导入和使用独立模块：

```python
import sys
sys.path.insert(0, '/path/to/claude-code-checker/src')

from modules.credential_checker import CredentialChecker
from modules.permission_checker import PermissionChecker
import asyncio

async def run_checks():
    credential_checker = CredentialChecker(
        claude_dir="~/.claude",
        workspace_dir="."
    )

    permission_checker = PermissionChecker(
        claude_dir="~/.claude"
    )

    cred_result = await credential_checker.check()
    perm_result = await permission_checker.check()

    print(f"凭证分数: {cred_result['score']}")
    print(f"权限分数: {perm_result['score']}")

asyncio.run(run_checks())
```

## 执行的安全检查

### 1. 配置分析
- 验证 `~/.claude/settings.json` 和 `~/.claude/settings.local.json`
- 检查配置文件中的敏感数据
- 检测过多的项目特定配置

### 2. 凭证暴露检测
- 扫描 API 密钥 (OpenAI, Anthropic, AWS, GitHub)
- 检测私钥和证书
- 识别通用密钥和密码
- 检查工作空间中的 `.env` 文件

### 3. 权限建模
- 验证 Claude Code 目录权限
- 检查配置文件权限
- 检测是否以过高权限运行 (root/管理员)

### 4. 网络安全分析
- 检查非本地监听端口
- 验证代理配置安全性
- 分析配置中的网络设置

### 5. 进程安全分析
- 监控可疑进程
- 检测网络工具和监控软件

## 安全评分

### 评分公式
```
SECURITY_SCORE = 100 - CONFIG_PENALTY - CREDENTIAL_PENALTY - PERMISSION_PENALTY - NETWORK_PENALTY - PROCESS_PENALTY
```

### 等级分类
| 等级 | 分数 | 操作 |
|-------|-------|--------|
| **A+** | 95-100 | 优秀 - 继续监控 |
| **A** | 90-94 | 良好 - 可能有小的改进空间 |
| **B** | 80-89 | 满意 - 处理警告 |
| **C** | 70-79 | 一般 - 一周内修复 |
| **D** | 60-69 | 较差 - 24小时内修复 |
| **F** | 0-59 | 严重 - 立即修复 |

## 输出格式

### 终端输出
```
╔══════════════════════════════════════════════════════════════╗
║        🔒 CLAUDE CODE SECURITY CHECK REPORT v1.0.0          ║
╠══════════════════════════════════════════════════════════════╣
║ Check ID: CCSC-20260329-123456-ABCDEFGH                     ║
║ Environment: Windows                                        ║
║ Time: 2026-03-29T12:00:00Z                                 ║
╚══════════════════════════════════════════════════════════════╝

▶ CONFIGURATION [0]
  ✓ No issues found

▶ CREDENTIAL EXPOSURE [-20]
  ⚠️ [CRITICAL] Exposed aws_key in config/secrets.json
  ⚠️ [MEDIUM] .env file found in workspace

▶ PERMISSION MODELING [-5]
  ⚠️ [HIGH] Claude Code directory is world-readable
```

### JSON 报告
```json
{
  "check_id": "CCSC-20260329-123456-ABCDEFGH",
  "timestamp": "2026-03-29T12:00:00Z",
  "environment": {
    "platform": "Windows",
    "platform_release": "10",
    "python_version": "3.12.1",
    "deployment": "local"
  },
  "security_score": 75,
  "grade": "C",
  "checks": {
    "configuration": {
      "score": 0,
      "issues": []
    },
    "credentials": {
      "score": -20,
      "issues": [...]
    }
  },
  "recommendations": [...]
}
```

## 与 Claude Code 集成

### 通过 Claude Code 手动执行
由于 Claude Code 不像 OpenClaw 那样具有自动技能加载功能，您可以：

1. **阅读 SKILL.md**: 使用 Claude Code 阅读 `SKILL.md` 文件获取指导
2. **手动执行**: 通过 Claude Code 的 Bash 工具运行检测器脚本
3. **计划检查**: 设置定期安全审计的定时任务

### Claude Code 工作流程示例
```
用户: 检查我的 Claude Code 环境的安全性
Claude: 我将帮助您运行安全检查。让我先阅读 SKILL.md 文件。

[阅读 SKILL.md]
[执行: python src/main.py --full-check]
[分析并呈现结果]
```

## 平台支持

- **Windows**: 完全支持，包含 Windows 特定的权限检查
- **macOS**: 支持，需要适当的路径调整
- **Linux**: 支持，使用 Unix 权限模型

## 开发

### 添加新的检查模块
1. 在 `src/modules/` 中创建新模块
2. 实现一个带有异步 `check()` 方法的类
3. 将模块添加到 `src/modules/__init__.py`
4. 集成到 `SecurityChecker.run_full_check()`

### 测试
```bash
# 测试导入
python test_import.py

# 功能测试
python test_functional.py

# 直接运行检测器
python src/main.py --full-check
```

## 许可证

Claude Code 安全检测器 - 为您的 AI 开发环境提供主动安全防护。

## 作者

**ClawGuard 团队** - 适用于 Claude Code 环境

---

*Claude Code 安全检测器：为您的 AI 开发环境提供主动安全防护。* 🔒