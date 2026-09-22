"""Command-line entry point: `braindrain run|status|list|simulate`.

Not implemented. See ARCHITECTURE.md §4.2.
"""

import sys


def main(argv: list[str] | None = None) -> int:
    print("braindrain: not implemented yet; see docs/ARCHITECTURE.md", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
