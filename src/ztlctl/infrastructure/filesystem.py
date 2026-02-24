"""Filesystem operations for vault content management.

INVARIANT: Files are truth. The filesystem is authoritative.
The DB is a derived index. ztlctl check --rebuild must always
be able to reconstruct the DB from files alone.
"""

from __future__ import annotations
