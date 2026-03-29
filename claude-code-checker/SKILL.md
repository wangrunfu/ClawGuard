---
name: claude-code-security-checker
version: 1.0.0
description: Claude Code 安全检测器 - 针对 Claude Code 环境的配置分析、凭证检测和安全态势评估
author: ClawGuard 团队 (适用于 Claude Code)
homepage: https://github.com/clawguard/security-checker
metadata:
  category: security
  risk: safe
  requires:
    bins: [python3, node, grep, find, stat, ls]
    python: []
---

# Claude Code 安全检测器 (CC-SC)

Claude Code 环境的安全配置分析器和运行时完整性验证工具。提供全面的安全态势评估，包括配置分析、凭证检测和权限建模。

## 使用时机

在以下情况下激活 Claude Code 安全检测器：
- 您想要检查 Claude Code 环境的安全状态
- 需要定期安全审查
- 配置更改或安装新工具后

## 架构概述

Claude Code 安全检测器采用模块化架构，便于维护和扩展：

```
claude-code-checker/
├── SKILL.md                    # 技能定义和文档
├── src/
│   ├── main.py                 # 主入口点（向后兼容）
│   ├── cli.py                  # 命令行界面
│   ├── security_checker.py     # 主检测类（协调器）
│   ├── checker_legacy.py       # 遗留单体检测器（已弃用）
│   └── modules/                # 模块化检查组件
│       ├── __init__.py         # 模块导出
│       ├── configuration_checker.py    # 配置分析
│       ├── credential_checker.py       # 密钥检测
│       ├── permission_checker.py       # 文件权限检查
│       ├── network_checker.py          # 网络安全分析
│       ├── process_checker.py          # 进程监控
│       ├── report_generator.py         # 报告格式化
│       └── environment_info.py         # 环境信息检测
```

### 模块职责
- **SecurityChecker**: 主协调器，协调所有检查
- **ConfigurationChecker**: 分析 Claude Code 配置文件
- **CredentialChecker**: 检测暴露的密钥和 API 密钥
- **PermissionChecker**: 验证文件/目录权限
- **NetworkChecker**: 检查网络安全设置
- **ProcessChecker**: 监控可疑进程
- **ReportGenerator**: 格式化和输出安全报告
- **EnvironmentInfo**: 收集系统和 Claude Code 环境信息

## 如何执行

### 方法 1：手动执行（推荐）
```bash
# 导航到检测器目录
cd /path/to/claude-code-checker

# 运行 Python 检测器（模块化版本）
python3 src/main.py --full-check

# 其他入口点
python3 src/cli.py --full-check      # CLI interface
python3 -m src.security_checker      # Direct module import

# 输出 JSON 格式
python3 src/main.py --json --save

# 显示帮助
python3 src/main.py --help
```

### 方法 2：通过 Claude Code（手动步骤）
1. 阅读此 SKILL.md 以理解检查流程
2. 按照以下描述手动执行每个检查步骤
3. 汇总结果并计算安全分数

## 安全检查工作流程

### 阶段 1：Claude Code 配置分析

#### 检查配置文件
- 查找并分析 Claude Code 配置文件：
  - `~/.claude/settings.json`（用户设置）
  - `~/.claude/settings.local.json`（本地覆盖）
  - 项目特定的 `.claude` 目录

#### Configuration Security Checks
| 检查项                         | 严重程度 | 检测规则                        |
|-------------------------------|----------|---------------------------------------|
| 配置中的 API 密钥             | CRITICAL | 正则表达式：`sk-*[a-zA-Z0-9]`              |
| 敏感路径暴露       | HIGH     | 文件访问 `~/.ssh/`、`~/.aws/`   |
| 网络权限过宽 | MEDIUM   | 无限制的网络访问           |
| 工具权限过高    | HIGH     | `tools.profile === "full"` 等效 |

### 阶段 2：凭证暴露检测

#### 凭证模式
在以下位置搜索暴露的密钥：
- 配置文件
- 环境文件 (.env, .env.local)
- 日志文件
- 内存和进程环境

#### 检测模式
```python
CREDENTIAL_PATTERNS = [
    # API 密钥
    r'sk-[a-zA-Z0-9]{20,}',  # OpenAI
    r'sk-ant-[a-zA-Z0-9_-]{20,}',  # Anthropic
    r'AKIA[0-9A-Z]{16}',  # AWS
    r'ghp_[a-zA-Z0-9]{36}',  # GitHub

    # 私钥
    r'-----BEGIN.*PRIVATE KEY-----',

    # 通用密钥
    r'api[_-]?key["\s:=]+["\'][a-zA-Z0-9]{16,}["\']',
    r'secret["\s:=]+["\'][a-zA-Z0-9]{16,}["\']',
    r'password["\s:=]+["\'][^"\']+["\']',
]
```

### 阶段 3：权限建模

#### 文件系统权限分析
检查关键路径的权限：
- `~/.claude/` 目录权限（应为 700）
- 配置文件权限（应为 600）
- Workspace directory permissions
- Check if running with excessive privileges

#### Permission Check Matrix
| 检查项                           | 严重程度 | 分数 | 规则                  |
|---------------------------------|----------|--------|-----------------------|
| 配置文件全局可读      | CRITICAL | -20    | Mode & 004 ≠ 0        |
| 配置目录全局可写 | HIGH     | -15    | Mode & 002 ≠ 0        |
| 以 root/管理员身份运行   | CRITICAL | -25    | UID === 0 或是管理员 |

### 阶段 4：运行时完整性验证

#### 完整性检查
- 验证 Claude Code 二进制文件/文件未被修改
- 检查意外的进程或服务
- 验证数字签名（如果可用）
- 监控异常行为模式

### 阶段 5：网络安全分析

#### 网络检查
- 检查暴露的网络服务
- 验证防火墙设置
- 审查出站网络连接
- 检查反向 shell 模式

### 阶段 6：日志分析

#### Log Checks
- 审查 Claude Code 日志中的安全事件
- 检查身份验证失败
- 寻找权限提升尝试
- 检测数据泄露模式

## 安全评分系统

### Scoring Formula
```
SECURITY_SCORE = 100 - CONFIG_PENALTY - CREDENTIAL_PENALTY - PERMISSION_PENALTY - NETWORK_PENALTY - LOG_PENALTY
```

### Score Classification
| 等级  | 分数  | 颜色 | 操作                             |
|--------|--------|-------|------------------------------------|
| **A+** | 95-100 | 🟢    | 优秀 - 继续监控    |
| **A**  | 90-94  | 🟢    | 良好 - 可能有小的改进空间 |
| **B**  | 80-89  | 🟢    | 满意 - 处理警告    |
| **C**  | 70-79  | 🟡    | 一般 - 一周内修复           |
| **D**  | 60-69  | 🟠    | 较差 - 24小时内修复         |
| **F**  | 0-59   | 🔴    | 严重 - 立即修复         |

## 输出格式

### JSON Report Example
```json
{
  "report_id": "CCSC-2026-0001",
  "timestamp": "2026-03-29T12:00:00Z",
  "environment": "claude-code-windows",
  "security_score": 85,
  "grade": "B",
  "checks": {
    "configuration": {
      "score": -10,
      "issues": [
        {
          "severity": "MEDIUM",
          "check": "config_permission",
          "message": "Configuration directory is group-readable"
        }
      ]
    },
    "credentials": {
      "score": 0,
      "issues": []
    },
    "permissions": {
      "score": -5,
      "issues": []
    }
  },
  "recommendations": [
    "Set .claude directory permissions to 700",
    "Review network access settings"
  ]
}
```

### Terminal Output Example
```
╔══════════════════════════════════════════════════════════════╗
║        🔒 CLAUDE CODE SECURITY CHECK REPORT v1.0.0          ║
╠══════════════════════════════════════════════════════════════╣
║ Environment: claude-code-windows                           ║
║ Time: 2026-03-29 12:00:00 UTC                             ║
╚══════════════════════════════════════════════════════════════╝

▶ CONFIGURATION SECURITY [-10]
  ⚠️ [MEDIUM] Configuration directory permissions: 750 (recommend: 700)
  ✓ No API keys in config files
  ✓ Network settings appropriate

▶ CREDENTIAL EXPOSURE [0]
  ✓ No exposed credentials detected
  ✓ No secrets in environment files
  ✓ No credentials in logs

▶ PERMISSION MODELING [-5]
  ⚠️ [LOW] Some workspace files world-readable
  ✓ Not running as administrator
  ✓ Config files properly protected

╔══════════════════════════════════════════════════════════════╗
║ SECURITY GRADE: B (85/100)                                ║
╠══════════════════════════════════════════════════════════════╣
║ RECOMMENDATIONS:                                           ║
║ 1. Change .claude directory permissions to 700             ║
║ 2. Review workspace file permissions                       ║
╚══════════════════════════════════════════════════════════════╝
```

## 实现说明

### 针对 Claude Code 环境
此技能设计用于在 Claude Code 的限制下工作：
1. **无自动技能加载**: 与 OpenClaw 不同，Claude Code 不会自动从目录检测和加载技能
2. **手动执行**: 检测器必须手动运行或通过现有的 Claude Code 工具集成
3. **文档驱动**: SKILL.md 作为主要文档和指南

### 执行选项
1. **直接脚本执行**: 使用模块化架构直接运行 Python 检测器
2. **模块导入**: 编程方式导入和使用特定的检查模块
3. **Claude Code 辅助**: 使用 Claude Code 阅读此 SKILL.md 并指导手动检查
4. **计划检查**: 设置 cron 作业或定时任务进行定期安全检查

### 模块化架构优势
- **可维护性**: 每个安全检查都在自己的模块中
- **可扩展性**: 易于添加新的检查模块
- **可测试性**: 各个模块可以独立测试
- **可重用性**: 模块可以单独导入和使用

## 集成考虑

### 与现有 ClawGuard 模块集成
此检测器可以补充现有的 ClawGuard 模块：
- **审计器**: Claude Code 技能的预安装检查
- **检测器**: 此模块 - 配置和运行时检查
- **检测**: 实时监控（未来扩展）

### 平台支持
- **Windows**: Claude Code 的主要平台
- **macOS**: 支持，需要适当的路径调整
- **Linux**: 支持，需要权限模型调整

## 作者

**ClawGuard 团队** - 适用于 Claude Code 环境

---

*Claude Code 安全检测器：为您的 AI 开发环境提供主动安全防护。* 🔒

## 附录：手动检查步骤

如果无法运行自动检测器，请按照以下手动步骤操作：

1. **检查配置文件**：
   ```bash
   ls -la ~/.claude/
   stat ~/.claude/settings.json
   ```

2. **搜索凭证**：
   ```bash
   grep -r "sk-" ~/.claude/ 2>/dev/null
   grep -r "AKIA" ~/.claude/ 2>/dev/null
   ```

3. **检查权限**：
   ```bash
   stat -c "%a %n" ~/.claude/settings.json
   stat -c "%a %n" ~/.claude/
   ```

4. **审查网络设置**：
   ```bash
   # 检查监听端口
   netstat -an | grep LISTEN
   ```

5. **计算您的分数**：
   - 从 100 分开始
   - 根据发现的问题扣分
   - 参考上面的评分表