# Security Policy

Quality Copilot stores and uses third-party integration credentials (JIRA, Git providers, TestRail, LLM API keys) and issues JWTs for user sessions. Please treat security reports seriously and privately.

## Supported versions

Security fixes are applied on the default branch (`master` / `main`) of this repository. There are no long-term supported release lines yet.

## Reporting a vulnerability

**Do not open a public GitHub issue** for vulnerabilities that could expose tokens, account takeover, auth bypass, or injection into integration APIs.

Instead, report privately:

1. Prefer [GitHub private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) on this repository (Security → Report a vulnerability), if enabled.
2. Or email the maintainer via the contact listed on the [GitHub profile](https://github.com/amzadb) for this project.

Include, when possible:

- A clear description of the issue and impact
- Steps to reproduce (PoC preferred)
- Affected component (`backend/`, `frontend/`, deploy config)
- Whether secrets or other users’ data could be reached

## What to expect

- Acknowledgement when the report is received (aim: within a few business days)
- A follow-up with severity assessment and planned fix timeline when feasible
- Credit in the advisory or release notes if you want it (say so in the report)

We ask that you give us a reasonable window to patch before any public disclosure.

## Non-security bugs

Feature requests and non-security bugs belong in normal GitHub issues or pull requests. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Hardening notes for operators

- Always set unique `JWT_SECRET`, `CREDENTIALS_ENCRYPTION_KEY`, and frontend `STORAGE_SECRET` in any shared or production environment
- Never commit `.env` files or live API tokens
- Integration tokens are encrypted at rest (Fernet); rotating `CREDENTIALS_ENCRYPTION_KEY` without re-saving settings will make existing tokens unreadable
- Prefer per-user Settings (database) over shared `credentials.json`
- Rotate integration tokens if they may have been exposed in logs or chat
