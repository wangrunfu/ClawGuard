# 🛡️ ClawGuard Auditor (CG-A)

**ClawGuard Auditor** is the ultimate enterprise-grade Security Kernel, SAST Vetter, and Active Data Loss Prevention (DLP) Engine for the OpenClaw agent ecosystem.

Operating at Ring-0 of the AI agent architecture, it provides unparalleled defense-in-depth by combining pre-installation static analysis with continuous runtime supervision, semantic intent checking, and real-time data redaction.

## 🌟 Why ClawGuard Auditor?

Autonomous AI agents executing third-party skills or dynamic code introduce significant supply-chain and execution risks. Standard vetters rely on static checklists and keyword matching. **ClawGuard Auditor** goes much further:

It doesn't just scan code; it understands the *intent* of the code, issues *temporary* execution tokens, and actively *redacts* sensitive data in memory before it can be exfiltrated.

## ✨ Exclusive Core Capabilities

### 1. 🔍 Pre-Flight Vetting & Semantic Intent Analysis
Before a skill is installed or executed, ClawGuard performs a deep audit:
- **Semantic Intent Matching:** Analyzes if the code's actual behavior matches its stated purpose (e.g., blocking a "Weather Skill" that attempts to read SSH keys).
- **Deep SAST & Anti-Obfuscation:** Detects dangerous function calls (`eval()`, `exec()`, `subprocess`), Base64/Hex payloads, and reverse shell signatures.
- **Supply Chain Security:** Scans `requirements.txt` and `package.json` for known typo-squatted malicious packages or outdated dependencies.
- **Provenance Scoring:** Evaluates the trustworthiness of the skill's source (e.g., official repo vs. unknown Gist).

### 2. 🛡️ Runtime Supervision & Ephemeral Tokens
ClawGuard acts as a continuous security kernel during execution:
- **Ephemeral & Scoped Tokens:** Grants temporary, highly-specific permissions (e.g., `CAP_NET_EGRESS` restricted *only* to `api.github.com`). Tokens expire the millisecond the task concludes.
- **Zero-Trust Exfiltration Defense:** Blocks unauthorized access to credentials (`~/.ssh/`, `.env`), system files, and OpenClaw memory files.
- **Active Threat Interception:** Instantly blocks Prompt Injection attempts ("ignore previous instructions", "disable ClawGuard") and privilege escalation (`sudo`, `chmod 777`).

### 3. 👁️‍🗨️ Active Data Loss Prevention (DLP)
A feature unseen in standard AI vetters, the real-time DLP engine inspects data *in transit* and *at rest*:
- **Real-Time Masking:** Automatically detects and redacts API keys, SSH keys, or PII before network transmission (e.g., replacing secrets with `[REDACTED_BY_CLAWGUARD]`).
- **Exfiltration Heuristics:** Blocks advanced exfiltration techniques like zipping local workspaces to untrusted domains or appending environment variables to URL query parameters.

## 🚀 How to Use

Install this Skill into your OpenClaw environment to establish it as a persistent, unyielding supervisor.

To explicitly vet a new skill, repository, or script, ask the agent:
> *"/audit-skill ./downloads/new-tool"*
> *"Use ClawGuard to audit https://github.com/unknown/skill-repo"*

### The ClawGuard Audit Report
The Auditor will simulate execution, map capabilities, and output a standardized, highly detailed report:

```markdown
# 🛡️ CLAWGUARD AUDIT REPORT
**Target:** `new-tool`
**Timestamp:** `2026-03-13 15:30:00`
**Provenance Score:** `Untrusted`

## 🧠 Semantic Intent Analysis
- **Stated Purpose:** Fetches local weather.
- **Actual Behavior:** Reads ~/.aws/credentials and opens a network socket.
- **Intent Match:** ❌ Mismatch

## 🚩 Vulnerability & Threat Findings
- `[CRITICAL]` `Data Exfiltration`: Code attempts to read AWS credentials.
- `[HIGH]` `Network Anomaly`: Hardcoded IP address detected.

## 🔑 Capability Mapping
- `CAP_FS_READ_SENSITIVE`
- `CAP_NET_EGRESS`

## 👁️‍🗨️ DLP & Exfiltration Risks
- High risk of credential exfiltration via unauthorized network requests.

---
### ⚠️ RISK TIER: 🔴 TIER 3 (Critical)
### 🛑 GUARDIAN VERDICT: REJECTED

**Actionable Recommendation:** DO NOT INSTALL. The code contains malicious intent to steal cloud credentials.
```

---
*Built for Zero-Trust. Security takes priority over execution.* 🦅
