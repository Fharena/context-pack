# Security Policy

## Supported Versions

Context Pack is pre-1.0. Security fixes target the latest release.

## Reporting a Vulnerability

Please report security concerns through GitHub private vulnerability reporting when available, or open an issue with a minimal description that does not expose secrets or exploit details.

Useful details:

- Context Pack version or commit
- Operating system
- Python version
- Command used
- Why the behavior may expose secrets, modify unexpected files, or trust stale context

## Security Notes

Context Pack reads git state and writes repo-local markdown files. It should not require network access for core commands.

Generated files under `.context-pack/packs/` and local notes under `.context-pack/local/` should not be committed by default.
