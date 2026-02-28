# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in ztlctl, please report it through [GitHub's private vulnerability reporting](https://github.com/ThatDevStudio/ztlctl/security/advisories/new).

**Please do not open a public issue for security vulnerabilities.**

### What to Expect

- **Acknowledgment**: Within 48 hours of your report
- **Assessment**: Within 7 days, we'll provide an initial severity assessment
- **Disclosure**: We follow a 90-day coordinated disclosure timeline

### Scope

This policy covers the ztlctl CLI tool and the `ztlctl` package published on PyPI. This includes:

- CLI command execution
- SQLite database operations
- File system operations within the vault
- MCP server transport (when using `ztlctl[mcp]`)
- Plugin loading and execution
