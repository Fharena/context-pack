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

Repository configuration is treated as untrusted input. As of v0.5.1:

- manifest paths must be portable repository-relative paths without `..`, drive prefixes, UNC/absolute roots, NTFS stream syntax, or reserved device names;
- area documents must remain below the managed `AREAS/` directory;
- automatic Evidence, search scopes, and text measurement use non-ignored repository files only;
- symbolic links are not followed for automatic source reads or managed Context Pack writes;
- unsafe paths fail closed with a concise error before file contents are emitted or files are modified.

Explicit CLI destinations such as `--output` are user-authorized paths and are not derived from repository manifests.

Generated files under `.context-pack/packs/` and local notes under `.context-pack/local/` should not be committed by default.
