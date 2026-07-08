# Security Policy / 安全策略

## Supported Versions / 支持版本

| Version / 版本 | Supported / 支持 |
| --- | --- |
| `v2.0` (active / 主线) | ✅ |
| `master` | ✅ |
| older / 更早版本 | ❌ |

## Reporting a Vulnerability / 上报漏洞

**Please do NOT open a public issue for security problems.**
**请勿通过公开 issue 报告安全问题。**

Preferred (private) channels / 优先(私密)渠道:

1. **GitHub Private Vulnerability Reporting** — go to the repo **Security** tab → **Report a vulnerability**
   （仓库 **Security** 标签页 → **Report a vulnerability**,私密提交,仅维护者可见)。
2. If that is unavailable, contact a maintainer privately via their GitHub profile
   （如不可用,通过维护者 GitHub 主页私信联系:[@xuwei95](https://github.com/xuwei95))。

Please include / 请尽量包含:

- Affected version / commit and deployment mode (dev / docker `my` / `pg` / 非容器)
  （受影响版本 / commit,以及部署形态)
- Reproduction steps or PoC / 复现步骤或 PoC
- Impact (what an attacker can achieve, and required privileges/role)
  （影响面:攻击者能做到什么、需要什么权限/角色)
- Suggested fix if any / 可能的修复建议

We aim to acknowledge within **3 business days** and to agree on a disclosure timeline with you (coordinated disclosure).
我们力争 **3 个工作日**内响应,并与你商定协同披露时间线。请在修复发布前不要公开细节。

## Scope / 范围

ezdata is a data platform that **executes user-provided code by design** — Python / Shell task templates, ETL "code extraction", and AI-driven code/query execution. Running such code **within the privileges a user's role (RBAC) explicitly grants** is expected behavior, not a vulnerability.

ezdata 是数据平台,**按设计会执行用户提供的代码**(Python/Shell 任务模板、ETL「代码取数」、AI 取数/计算)。在用户角色(RBAC)**已授予的权限范围内**执行这些代码属预期行为,不算漏洞。

In scope / 属于范围内(欢迎报告):

- Sandbox escape / breaking out of the code-execution sandbox
  （沙箱逃逸:突破代码执行沙箱的隔离/出网白名单/资源限制)
- Privilege escalation beyond the caller's granted role/permissions
  （越权:超出调用者被授予的角色/权限)
- Authentication / authorization bypass, session or JWT flaws
  （认证/鉴权绕过、会话或 JWT 问题)
- **Multi-tenant isolation breaks** (accessing another tenant's data/config)
  （多租户隔离被打穿:读到其他租户的数据/配置)
- Secrets disclosure (data-source / AI credential leakage, decryption bypass)
  （密钥泄露:数据源/AI 凭据泄露、解密绕过)
- SSRF / injection / RCE reachable **without** the code-execution permission
  （无需代码执行权限即可触达的 SSRF / 注入 / RCE)

Hardening guidance for operators is in [`docs/DEPLOY.md` §10](docs/DEPLOY.md)（部署加固见 DEPLOY §10:强随机密钥、沙箱默认开启 + egress 白名单、收敛暴露面、多租户默认拒绝等)。
