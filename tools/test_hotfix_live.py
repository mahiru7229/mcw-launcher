"""MCW Launcher - Hotfix Live CDN Diagnostic & Verification Tool.

Usage:
    python tools/test_hotfix_live.py [--status] [--apply] [--verify] [--rollback] [--all]

Examples:
    python tools/test_hotfix_live.py --status
    python tools/test_hotfix_live.py --apply
    python tools/test_hotfix_live.py --verify
    python tools/test_hotfix_live.py --rollback
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure repository root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import VERSION_ID
from src.core.update.hotfix_manager import (
    HotfixError,
    HotfixManager,
    HotfixMetaPathFinder,
)


def get_manager() -> HotfixManager:
    return HotfixManager(root_directory=PROJECT_ROOT)


def cmd_status() -> None:
    print("=" * 60)
    print(" MCW LAUNCHER - HOTFIX SYSTEM DIAGNOSTIC")
    print("=" * 60)
    print(f"Base Launcher Version : {VERSION_ID}")
    print(f"Project Root Path     : {PROJECT_ROOT}")

    manager = get_manager()
    print(f"Hotfix Root Directory : {manager.hotfix_root}")
    print(f"Live Directory        : {manager.live_dir}")
    print(f"State File            : {manager.state_file}")
    print(f"Manifest CDN URL      : {manager.manifest_url}")
    print("-" * 60)

    # Check local state
    state = manager.load_state()
    if state is None:
        print("[Local State] No hotfix currently applied (Clean base installation).")
    else:
        print(f"[Local State] Active Hotfix ID : {state.applied_hotfix_id}")
        print(f"              Base Version     : {state.base_version}")
        print(f"              Target Version   : {state.target_version}")
        print(f"              Installed At     : {state.installed_at}")
        print(f"              Checksum (SHA256): {state.sha256[:16]}...")
        print(f"              Patched Modules  : {', '.join(state.modules) or 'None listed'}")

    effective = manager.get_effective_version(VERSION_ID)
    print(f"Effective Version     : {effective}")
    print("-" * 60)

    # Check CDN manifest
    print("[CDN Network] Checking manifest from Cloudflare Edge...")
    try:
        manifest = manager.fetch_manifest()
        print(f"  Manifest Status: OK (Found {len(manifest)} active patch entry/entries)")
        for entry in manifest:
            status_flag = "ENABLED" if entry.enabled else "DISABLED"
            print(f"  - [{status_flag}] v{entry.target_version} (Base: {entry.base_version}, ID: {entry.hotfix_id})")
            print(f"    URL:  {entry.download_url}")
            print(f"    SHA:  {entry.sha256}")
            print(f"    Size: {entry.size_bytes} bytes")
    except HotfixError as exc:
        print(f"  [ERROR] CDN Check Failed: {exc}")


def cmd_apply(target_version: str | None = None) -> bool:
    print("[Hotfix Apply] Checking for eligible patch on CDN...")
    manager = get_manager()
    entry = manager.check_for_hotfix(VERSION_ID)
    if entry is None:
        print(f"[Hotfix Apply] No eligible hotfix found for base version '{VERSION_ID}'.")
        return False

    print(f"[Hotfix Apply] Found eligible hotfix '{entry.target_version}' (ID: {entry.hotfix_id}).")
    print(f"[Hotfix Apply] Description: {entry.description}")
    print(f"[Hotfix Apply] Downloading from: {entry.download_url}")

    def on_progress(pct: int, msg: str) -> None:
        print(f"  [{pct:3d}%] {msg}")

    try:
        state = manager.apply_hotfix(entry, progress_callback=on_progress)
        print(f"[SUCCESS] Hotfix '{state.target_version}' applied successfully!")
        return True
    except HotfixError as exc:
        print(f"[FAILURE] Could not apply hotfix: {exc}")
        return False


def cmd_verify() -> bool:
    print("[Hotfix Verify] Verifying runtime path injection and module resolution...")
    manager = get_manager()
    state = manager.load_state()
    if state is None:
        print("[Hotfix Verify] No hotfix state found on disk.")
        return False

    # Simulate launcher startup bootstrap
    bootstrapped = HotfixManager.bootstrap_sys_path(
        root_directory=PROJECT_ROOT,
        current_base_version=VERSION_ID,
    )
    print(f"  bootstrap_sys_path() returned: {bootstrapped}")

    # Check meta_path finder
    has_finder = any(isinstance(f, HotfixMetaPathFinder) for f in sys.meta_path)
    print(f"  HotfixMetaPathFinder installed in sys.meta_path: {has_finder}")

    # Remove any cached imports to ensure dynamic loader is exercised
    for key in list(sys.modules.keys()):
        if "create_instance_dialog" in key:
            del sys.modules[key]

    try:
        import src.gui.dialogs.create_instance_dialog as cid

        module_path = Path(cid.__file__).resolve()
        expected_dir = manager.live_dir.resolve()
        is_patched = str(module_path).startswith(str(expected_dir))

        print(f"  Loaded module path: {module_path}")
        print(f"  Expected live root: {expected_dir}")
        if is_patched:
            print("[SUCCESS] Module successfully loaded from hotfixes/live!")
        else:
            print("[FAILURE] Module was loaded from base directory instead of hotfixes/live!")
            return False

        # Verify sibling unpatched module
        import src.gui.loader_version_options as lvo

        sibling_path = Path(lvo.__file__).resolve()
        print(f"  Sibling unpatched module path: {sibling_path}")
        if not str(sibling_path).startswith(str(expected_dir)):
            print("[SUCCESS] Unpatched sibling modules correctly fallback to base installation!")
        else:
            print("[WARNING] Sibling module unexpectedly loaded from hotfix live folder.")

        return True
    except Exception as exc:
        print(f"[FAILURE] Error verifying hotfix module: {exc}")
        return False


def cmd_rollback() -> bool:
    print("[Hotfix Rollback] Rolling back all active hotfixes...")
    manager = get_manager()
    success = manager.rollback()
    if success:
        print("[SUCCESS] Hotfix rolled back. Launcher restored to clean base state.")
    else:
        print("[NOTICE] No active hotfix was present to roll back.")
    return success


def main() -> None:
    parser = argparse.ArgumentParser(description="MCW Launcher Hotfix Diagnostic & Verification Tool")
    parser.add_argument("--status", action="store_true", help="Display hotfix and CDN status")
    parser.add_argument("--apply", action="store_true", help="Download and apply eligible hotfix from CDN")
    parser.add_argument("--verify", action="store_true", help="Verify runtime import resolution for applied hotfix")
    parser.add_argument("--rollback", action="store_true", help="Roll back installed hotfix")
    parser.add_argument("--all", action="store_true", help="Run full cycle: Status -> Apply -> Verify -> Status")

    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.apply:
        cmd_apply()
    elif args.verify:
        cmd_verify()
    elif args.rollback:
        cmd_rollback()
    elif args.all:
        print("\n>>> STEP 1: INITIAL STATUS")
        cmd_status()
        print("\n>>> STEP 2: APPLY HOTFIX FROM CDN")
        if cmd_apply():
            print("\n>>> STEP 3: VERIFY RUNTIME LOADER")
            cmd_verify()
            print("\n>>> STEP 4: FINAL STATUS")
            cmd_status()
    else:
        # Default behavior: run status and show usage hint
        cmd_status()
        print("\nHint: To test applying the hotfix from CDN, run:")
        print("  python tools/test_hotfix_live.py --apply")
        print("To verify runtime resolution:")
        print("  python tools/test_hotfix_live.py --verify")
        print("To roll back to base version:")
        print("  python tools/test_hotfix_live.py --rollback")


if __name__ == "__main__":
    main()
