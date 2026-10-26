# AegisOS threat model

## Assets
User credentials and tokens; repository source; issue text; generated patches; provider API keys; execution resources; audit records; integrity of verdicts.

## Trust boundaries and controls
- **Browser to API:** bearer JWT, schema validation, CORS allowlist, bounded request fields, generic auth failures. Add TLS, reverse-proxy rate limits, account lockout and CSRF protections if cookie auth is introduced.
- **User to repository:** workspace paths are resolved under `WORKSPACE_ROOT`; symlink directories and secret-like files are skipped; file count, per-file bytes and total indexed bytes are bounded. Git URL import is not enabled. Indexing is not a complete malware scanner.
- **Repository to model:** source is untrusted data, not instructions. Context is bounded and wrapped as data. Prompt injection can still influence model output; validate patches and require independent checks.
- **API to provider:** credentials are server-side environment variables. Logs avoid source text and secrets. Provider calls can incur cost; configure upstream quotas and timeout limits.
- **Worker to code execution:** disabled by default. If enabled, Docker is used with network disabled, read-only root, dropped capabilities, no-new-privileges, PID/memory/CPU limits, non-root UID, disposable read-only source mount and no credentials. No Docker socket is mounted in the container.
- **Verdict integrity:** LLM review is advisory. Missing evidence => inconclusive; nonzero executed check => failed; a compile-only pass does not prove acceptance criteria.

## Residual risks
Docker shares the host kernel and daemon privileges; this is not a hardened multi-tenant sandbox. Kernel exploits, container-runtime bugs, resource contention, parser vulnerabilities, malicious symlink races and unexpected language tool behavior remain possible. Use dedicated ephemeral VMs for hostile repositories, pin images by digest, enforce external quotas, run rootless Docker where possible, and keep API and sandbox hosts separate.

## Operational guidance
Use unique production secrets, TLS, private database/Redis networks, database backups, retention policies, restricted workspace permissions, image scanning, dependency scanning, audit review, and tested incident response. Do not store full source in logs. Set deletion/retention policies appropriate to the organization.
