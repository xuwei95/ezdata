> [简体中文](SECURITY.md) | **English**

# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| `v2.0` (active) | ✅ |
| `master` | ✅ |
| older | ❌ |

## Reporting a Vulnerability

**Please do NOT open a public issue for security problems.**

Preferred (private) channels:

1. **GitHub Private Vulnerability Reporting** — go to the repo **Security** tab → **Report a vulnerability** (submitted privately, visible only to maintainers).
2. If that is unavailable, contact a maintainer privately via their GitHub profile ([@xuwei95](https://github.com/xuwei95)).

Please include:

- Affected version / commit and deployment mode (dev / docker `my` / `pg` / non-container)
- Reproduction steps or PoC
- Impact (what an attacker can achieve, and required privileges/role)
- Suggested fix if any

We aim to acknowledge within **3 business days** and to agree on a disclosure timeline with you (coordinated disclosure). Please do not disclose details publicly before a fix is released.

## Scope

ezdata is a data platform that **executes user-provided code by design** — Python / Shell task templates, ETL "code extraction", and AI-driven code/query execution. Running such code **within the privileges a user's role (RBAC) explicitly grants** is expected behavior, not a vulnerability.

In scope (reports welcome):

- Sandbox escape / breaking out of the code-execution sandbox (isolation / egress allowlist / resource limits)
- Privilege escalation beyond the caller's granted role/permissions
- Authentication / authorization bypass, session or JWT flaws
- **Multi-tenant isolation breaks** (accessing another tenant's data/config)
- Secrets disclosure (data-source / AI credential leakage, decryption bypass)
- SSRF / injection / RCE reachable **without** the code-execution permission

Hardening guidance for operators is in [`docs/DEPLOY.md` §10](DEPLOY.en.md) (see DEPLOY §10: strong random keys, sandbox enabled by default + egress allowlist, minimized exposure surface, multi-tenant default-deny, etc.).
