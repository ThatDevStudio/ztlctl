"""Extension layer — plugin system via pluggy.

Discovery: entry_points (pip-installed) + .ztlctl/plugins/ (local).
INVARIANT: Plugin failures are warnings, never errors.
"""
