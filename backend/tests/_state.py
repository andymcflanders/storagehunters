"""Shared mutable test state.

Kept in its own module so both conftest (which records) and the coverage
guard (which reads) reference the *same* object. pytest imports conftest.py
under a special module name, so importing COVERED from conftest elsewhere
would create a second, empty set.
"""

# (method, route-template) pairs hit by any request during the session.
COVERED: set[tuple[str, str]] = set()
