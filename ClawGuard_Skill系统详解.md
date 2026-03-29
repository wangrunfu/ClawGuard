# ClawGuard Skill 系统详解

## 📖 引言

ClawGuard 是一个为 OpenClaw 等 AI 代理平台设计的安全工具集。它采用 **模块化安全解决方案**，当前包含三个核心模块：

1. **Auditor** - 安装前安全审计
2. **Checker** - 配置安全检查
3. **Detect** - 运行时威胁检测

本文档深入解析 ClawGuard Skill 系统的工作原理，解答关于 **脚本执行 vs 模型能力**、**文档与代码的"重复"** 等核心设计问题。

## 🏗️ OpenClaw Skill 系统工作原理

### 技能（Skill）的基本结构

每个 ClawGuard Skill 都遵循标准结构：

```
checker-skill/
├── SKILL.md          # 技能元数据与文档
├── cli.js            # 入口脚本
├── src/checker.js    # 核心逻辑
└── README.md         # 用户文档
```

### 三层架构设计

| 层级 | 文件 | 作用 | 使用者 |
|------|------|------|--------|
| **文档层** | SKILL.md | 描述技能功能、触发条件 | 模型 + 人类 |
| **执行层** | cli.js + src/* | 实现安全检查逻辑 | OpenClaw 运行时 |
| **元数据层** | _meta.json | 发布信息、标签等 | 技能市场 |

### 执行流程：从用户请求到结果输出

```
用户："检查我的 OpenClaw 安全状况"
    ↓
OpenClaw 模型读取 SKILL.md 的 frontmatter
    ↓
模型识别这是 "clawguard-security-checker" 技能的任务
    ↓
模型执行约定入口文件：node cli.js
    ↓
cli.js → SecurityChecker.runFullCheck()
    ↓
脚本执行所有硬编码安全检查
    ↓
返回 JSON 结果给 OpenClaw
    ↓
OpenClaw 呈现结果给用户
```

**关键洞察**：模型只负责 **路由决策**（判断是否调用该技能），不参与实际的安全检查逻辑。

## 🔧 脚本检查的"死板"与模型灵活性

### 脚本的"死板"规则

以 `checker-skill` 为例，其检查逻辑完全硬编码：

```javascript
// checker.js 中的硬编码规则
if (config.gateway.bind === '0.0.0.0') score -= 15;
if (config.tools.profile === 'full') score -= 10;
if (/sk-[a-zA-Z0-9]{20,}/.test(content)) score -= 20;
```

这些规则确实"死板"：
- 无法理解上下文（开发 vs 生产环境）
- 无法识别新的攻击模式（除非更新正则表达式）
- 无法提供人性化的解释

### 模型中本应扮演的角色

在一个理想系统中，模型应负责：

#### 1. **智能的任务分解**
```
用户："帮我全面检查一下安全状况"
模型分析：
  - 上下文：这是生产环境，有敏感数据
  - 决策：全量检查 + 重点扫描凭证
  - 参数调整：使用严格阈值，增加日志分析深度
  - 调用：checker.runCheck({mode: 'full', focus: 'credentials', strict: true})
```

#### 2. **动态的规则应用**
```javascript
// 伪代码：模型增强的检查
async function intelligentCheck(config) {
  const context = await model.analyzeContext();

  // 基础规则
  const issues = basicChecker.check(config);

  // 模型补充分析
  if (context.hasSensitiveData && config.gateway.bind !== 'localhost') {
    issues.push({
      severity: context.isProduction ? 'CRITICAL' : 'HIGH',
      reason: await model.explainRisk('外部绑定 + 敏感数据')
    });
  }

  return issues;
}
```

#### 3. **结果解释与优先级排序**
```
脚本原始输出：
  {"severity": "HIGH", "check": "gateway_bind_all"}

模型增强解释：
  "您的服务暴露在所有网络接口上。在开发环境中风险中等，
   但如果迁移到生产环境，这是高危问题。
   建议立即修改为 `localhost`。"
```

## 🔄 SKILL.md 与脚本的"重复"问题

### 看似重复的结构

对比 `SKILL.md` 描述的 7 个检查阶段和脚本实现：

```
SKILL.md 描述的阶段          checker.js 实现的方法
├── 1. 配置分析            → checkConfiguration()
├── 2. 凭证扫描            → checkCredentials()
├── 3. 权限建模            → checkPermissions()
├── 4. 运行时完整性        → checkIntegrity()
├── 5. 网络安全            → checkNetwork()
├── 6. 日志取证            → checkLogs()
└── 7. 合规检查            → checkCompliance()
```

### 为什么这种"重复"是必要的？

这实际上是 AI Skill 系统的 **设计模式**，而非冗余：

| 层面 | 文件 | 内容 | 目的 |
|------|------|------|------|
| **意图理解** | SKILL.md | 自然语言描述 | 供模型理解何时调用 |
| **逻辑实现** | checker.js | 可执行代码 | 供机器执行检查 |
| **用户沟通** | 模型输出 | 解释性文本 | 向用户传达结果 |

### 模型无法直接执行 SKILL.md 步骤的原因

```javascript
// SKILL.md 中的自然语言描述：
"Verify these security settings: gateway.bind should be 'localhost'"

// 模型无法直接执行这段文本，但脚本可以：
if (config.gateway && config.gateway.bind === '0.0.0.0') {
  issues.push({ severity: 'HIGH', message: '...' });
}
```

**自然语言 ≠ 可执行代码**：SKILL.md 是给人（和模型）读的文档，不是给机器执行的程序。

## ⚖️ 设计权衡与架构考量

### 当前设计：确定性优先

```javascript
// 安全工具需要 100% 可重复的结果
const scriptResult = checkBindAddress(config);
// 总是：{passed: false, reason: "bind is 0.0.0.0"}

// 模型可能产生幻觉：
const modelResponse = await model.evaluate("检查绑定地址");
// 可能输出："看起来没问题"（但实际是 0.0.0.0）
```

### 性能与成本对比

| 方面 | 脚本方案 | 模型方案 |
|------|----------|----------|
| **响应时间** | 毫秒级 | 秒级（API调用） |
| **执行成本** | 零成本 | 每次检查都有 token 成本 |
| **离线能力** | ✅ 完全离线 | ❌ 需要网络连接 |
| **结果一致性** | ✅ 100% 一致 | ❌ 可能不一致 |

### 安全与审计需求

安全工具有特殊要求：
- **可审计性**：代码可被安全团队审查
- **确定性**：相同输入总是产生相同输出
- **最小权限**：脚本有明确的权限边界

## 🏗️ 理想中的混合架构

### 四层混合系统

```
┌─────────────────────────────────────────────────────────┐
│                   用户交互层                              │
│  "检查我的配置安全吗？" → 模型理解意图                      │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                   模型调度层                              │
│  • 解析用户真实需求（"全面检查" vs "快速扫描"）            │
│  • 确定检查范围和深度                                     │
│  • 调用相应的脚本模块                                     │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                   脚本执行层                              │
│  ├─ 配置检查模块 ──┤ ├─ 凭证扫描模块 ──┤ ├─ 权限检查模块 ─┤  │
│  │ 确定性的规则   │ │ 正则匹配       │ │ 文件系统检查   │  │
│  └───────────────┘ └───────────────┘ └───────────────┘  │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                   结果融合层                              │
│  • 脚本原始数据 + 模型上下文分析                          │
│  • 优先级排序（基于业务影响）                             │
│  • 生成人性化报告                                         │
└─────────────────────────────────────────────────────────┘
```

### 演进路径

```
阶段1：纯脚本检查 (当前实现)
    ↓
阶段2：脚本 + 基础模型包装 (解释结果)
    ↓
阶段3：自适应检查 (模型决定检查什么、怎么检查)
    ↓
阶段4：预测性安全 (模型识别潜在风险模式)
```

## ❓ 常见问题解答

### Q1: 为什么 SKILL.md 要详细描述检查步骤，如果脚本已经实现了？

**A**: SKILL.md 有双重目的：
1. **供模型理解**：帮助模型判断何时调用该技能
2. **供人类阅读**：开发者、安全团队可以了解技能功能
3. **文档与代码分离**：可以独立更新文档而不影响代码

### Q2: 模型能直接执行 SKILL.md 中的步骤吗？

**A**: 不能。因为：
1. 自然语言步骤不是可执行代码
2. 模型无法访问文件系统执行实际检查
3. 会产生不一致的结果（模型幻觉）
4. 性能差，成本高

### Q3: 脚本的规则真的很"死板"吗？

**A**: 看 `checker.js` 源码发现有一些灵活设计：

```javascript
// 1. 严重性分级（不是一刀切）
if (config.gateway.bind === '0.0.0.0') {
  severity: 'HIGH'  // 所有接口 - 高风险
} else if (config.gateway.bind === 'lan') {
  severity: 'MEDIUM' // 仅局域网 - 中风险
}

// 2. 组合规则（考虑叠加风险）
if (process.getuid() === 0) {  // 运行在root
  if (config.tools.profile === 'full') {  // 且全权限
    score -= 25;  // 风险加倍惩罚
  }
}

// 3. 可扩展的规则集
const credentialPatterns = [
  { pattern: /sk-[a-zA-Z0-9]{20,}/g, severity: 'CRITICAL' },
  // 可以轻松添加新规则而不修改核心逻辑
];
```

### Q4: 如果我想让检查更智能，应该怎么做？

**A**: 可以在现有架构上添加智能层：

```javascript
class IntelligentChecker {
  async check(userQuery, context) {
    // 1. 模型分析用户真实需求
    const analysis = await model.analyze({
      query: userQuery,
      context: context,
      skillDocs: readSkillMd()
    });

    // 2. 动态调整检查参数
    const params = {
      focus: analysis.focusAreas,  // 例如：重点检查凭证
      depth: analysis.detailLevel, // 快速扫描 vs 深度检查
      strictness: analysis.riskTolerance // 宽松 vs 严格
    };

    // 3. 执行脚本检查（确定性部分）
    const rawResults = await scriptChecker.run(params);

    // 4. 模型增强结果（灵活性部分）
    const enhanced = await model.enhanceResults(rawResults, {
      audience: analysis.userExpertise,
      businessImpact: analysis.businessContext
    });

    return enhanced;
  }
}
```

## 🎯 总结

### 核心要点

1. **明确的分工**：
   - SKILL.md：文档层，描述"做什么"和"何时做"
   - 脚本：执行层，实现"怎么做"
   - 模型：调度层，决定"是否调用"和"如何解释"

2. **设计合理性**：
   - 脚本的"死板"保证了检查的确定性和可重复性
   - 文档的"重复"是AI Skill系统的必要设计模式
   - 当前架构在确定性、性能和安全性之间取得了平衡

3. **演进空间**：
   - 当前是MVP（最小可行产品）阶段
   - 可以在脚本基础上添加模型智能层
   - 逐步向自适应、预测性安全演进

### 设计哲学

ClawGuard 的 Skill 系统体现了 **"确定性优先，灵活性渐进"** 的设计哲学：

- **第一阶段**：先确保基本安全检查可靠执行（脚本）
- **第二阶段**：添加智能解释和上下文感知（模型包装）
- **第三阶段**：实现完全自适应的安全评估（混合系统）

这种渐进式设计既保证了当前系统的实用性和安全性，又为未来的智能化演进留下了空间。

---

**最后更新**：2026-03-29
**文档版本**：1.0
**相关文件**：
- `checker-skill/SKILL.md` - 技能文档
- `checker-skill/src/checker.js` - 核心检查逻辑
- `auditor-skill/src/auditor.js` - 审计引擎示例