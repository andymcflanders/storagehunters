"""Coverage guard — the reason the suite is a *smoke* suite.

Fails the build if any route registered on the app was never exercised by
any test in this session. New endpoints therefore can't merge without a
test that at least hits them once.

Runs last (zz prefix) so every other test has recorded its hits first.
"""

from app.main import app
from tests._state import COVERED

# Routes intentionally not driven by the suite, with the reason. Keep this
# list short and justified — it is the explicit record of what is NOT
# smoke-tested.
EXPECTED_UNCOVERED: set[tuple[str, str]] = set()


def _all_api_routes() -> set[tuple[str, str]]:
    schema = app.openapi()
    routes = set()
    for path, ops in schema["paths"].items():
        if not (path.startswith("/api") or path == "/health"):
            continue
        for method in ops:
            m = method.upper()
            if m in ("GET", "POST", "PATCH", "PUT", "DELETE"):
                routes.add((m, path))
    return routes


def test_every_route_is_smoke_tested():
    all_routes = _all_api_routes()
    missing = all_routes - COVERED - EXPECTED_UNCOVERED

    # COVERED records concrete request paths mapped back to route templates
    # by the ASGI recorder, so the two sets use identical template strings.
    assert not missing, (
        "These API routes were never exercised by any test:\n"
        + "\n".join(f"  {m} {p}" for m, p in sorted(missing, key=lambda x: (x[1], x[0])))
        + f"\n\n({len(all_routes) - len(missing)}/{len(all_routes)} covered)"
    )
