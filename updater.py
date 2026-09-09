from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] in {"--version", "-V"}:
        from src.config import VERSION_TAG

        print(f"MCW Updater {VERSION_TAG}")
        return 0

    if len(sys.argv) != 3 or sys.argv[1] != "--apply-update":
        return 2

    from src.core.update.update_applier import run_update_applier

    return run_update_applier(Path(sys.argv[2]))


if __name__ == "__main__":
    raise SystemExit(main())
