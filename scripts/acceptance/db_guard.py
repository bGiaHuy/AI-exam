"""
================================================================================
PRODUCTION DATABASE FAIL-CLOSED GUARD (SPRINT 3.2B-R2)
================================================================================
Monitors cheating_system.db, cheating_system.db-wal, and cheating_system.db-shm:
- Tracks exists, size_bytes, mtime (nanosecond precision + ISO), and SHA-256
- Checkpoints before pipeline, after every step, and at finalize
- Fails immediately (exit 1) if any file appears, disappears, or changes size, mtime, or sha256
- Outputs production_db_guard.json (baseline, checkpoints, final)
- Never checkpoints, truncates, restores, or mutates WAL/SHM of main DB
================================================================================
"""

import os
import sys
import json
import argparse
import hashlib
import shutil
from datetime import datetime, timezone

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
TARGET_FILES = ["cheating_system.db", "cheating_system.db-wal", "cheating_system.db-shm"]


def inspect_files(project_root: str) -> dict:
    state = {}
    for fn in TARGET_FILES:
        p = os.path.join(project_root, fn)
        if not os.path.exists(p):
            state[fn] = {
                "exists": False,
                "size_bytes": 0,
                "mtime_ns": 0,
                "mtime_iso": None,
                "ctime_ns": 0,
                "ctime_iso": None,
                "sha256": None
            }
        else:
            st = os.stat(p)
            h = hashlib.sha256()
            with open(p, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            mtime_iso = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
            ctime_iso = datetime.fromtimestamp(st.st_ctime, tz=timezone.utc).isoformat()
            state[fn] = {
                "exists": True,
                "size_bytes": st.st_size,
                "mtime_ns": st.st_mtime_ns,
                "mtime_iso": mtime_iso,
                "ctime_ns": st.st_ctime_ns,
                "ctime_iso": ctime_iso,
                "sha256": h.hexdigest()
            }
    return state


def compare_with_baseline(baseline: dict, current: dict) -> tuple[bool, list[str]]:
    issues = []
    for fn in TARGET_FILES:
        b = baseline.get(fn, {})
        c = current.get(fn, {})
        if b.get("exists") != c.get("exists"):
            if not b.get("exists") and c.get("exists"):
                issues.append(f"{fn} appeared unexpectedly on disk")
            else:
                issues.append(f"{fn} disappeared unexpectedly from disk")
            continue

        if b.get("exists"):
            if b.get("size_bytes") != c.get("size_bytes"):
                issues.append(f"{fn} size changed: {b.get('size_bytes')} -> {c.get('size_bytes')} bytes")
            if b.get("mtime_ns") != c.get("mtime_ns"):
                diff_ns = c.get("mtime_ns", 0) - b.get("mtime_ns", 0)
                issues.append(f"{fn} mtime changed: {b.get('mtime_iso')} -> {c.get('mtime_iso')} (diff: {diff_ns} ns)")
            if b.get("sha256") != c.get("sha256"):
                issues.append(f"{fn} SHA-256 changed: {b.get('sha256')} -> {c.get('sha256')}")

    return (len(issues) == 0, issues)


def save_guard_json(data: dict, filepath: str):
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_guard_json(filepath: str) -> dict:
    if not os.path.exists(filepath):
        print(f"[FATAL GUARD] Guard file not found at {filepath}")
        sys.exit(1)
    with open(filepath, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def cmd_baseline(args):
    now_iso = datetime.now(timezone.utc).isoformat()
    files_state = inspect_files(PROJECT_ROOT)

    guard_data = {
        "run_id": os.environ.get("ACCEPTANCE_RUN_ID", "default_run"),
        "schema_version": "1.0",
        "description": "Production database immutable integrity guard (cheating_system.db, -wal, -shm)",
        "project_root": PROJECT_ROOT,
        "baseline": {
            "recorded_at": now_iso,
            "files": files_state
        },
        "checkpoints": [],
        "final": None,
        "overall_status": "BASELINE_RECORDED"
    }

    save_guard_json(guard_data, args.guard_file)
    print(f"[DB-GUARD] Baseline recorded at {now_iso}:")
    for fn, info in files_state.items():
        if info["exists"]:
            print(f"    - {fn:<24} Size: {info['size_bytes']:>8} B, SHA256: {info['sha256'][:16]}..., MTime: {info['mtime_iso']}")
        else:
            print(f"    - {fn:<24} (Does not exist)")
    print(f"[DB-GUARD] Guard file written to {args.guard_file}")
    sys.exit(0)


def cmd_check(args):
    now_iso = datetime.now(timezone.utc).isoformat()
    guard_data = load_guard_json(args.guard_file)
    baseline_files = guard_data.get("baseline", {}).get("files", {})
    current_files = inspect_files(PROJECT_ROOT)

    is_untouched, issues = compare_with_baseline(baseline_files, current_files)

    if getattr(args, "read_only", False):
        if not is_untouched:
            print("\n" + "!" * 80)
            print(f"[FATAL DB-GUARD VIOLATION] Main DB was MUTATED during {args.step}!")
            for issue in issues:
                print(f"    - {issue}")
            print("!" * 80 + "\n")
            sys.exit(1)
        print(f"[DB-GUARD-OK] {args.step:<8} Main DB files untouched (read-only verification)")
        sys.exit(0)

    step_entry = {
        "step_id": args.step,
        "timestamp": now_iso,
        "status": "UNTOUCHED" if is_untouched else "VIOLATION",
        "issues": issues
    }
    guard_data.setdefault("checkpoints", []).append(step_entry)

    if not is_untouched:
        guard_data["overall_status"] = "MUTATION_DETECTED"
        save_guard_json(guard_data, args.guard_file)
        print("\n" + "!" * 80)
        print(f"[FATAL DB-GUARD VIOLATION] Main DB was MUTATED during {args.step}!")
        for issue in issues:
            print(f"    - {issue}")
        print("!" * 80 + "\n")
        sys.exit(1)

    save_guard_json(guard_data, args.guard_file)
    print(f"[DB-GUARD-OK] {args.step:<8} Main DB files untouched (SHA-256 and mtime identical to baseline)")
    sys.exit(0)


def cmd_finalize(args):
    now_iso = datetime.now(timezone.utc).isoformat()
    guard_data = load_guard_json(args.guard_file)
    baseline_files = guard_data.get("baseline", {}).get("files", {})
    current_files = inspect_files(PROJECT_ROOT)

    is_untouched, issues = compare_with_baseline(baseline_files, current_files)
    total_checkpoints = len(guard_data.get("checkpoints", []))

    if not is_untouched:
        guard_data["final"] = {
            "timestamp": now_iso,
            "status": "VIOLATION",
            "total_checkpoints": total_checkpoints,
            "issues": issues
        }
        guard_data["overall_status"] = "FAILED_MUTATION_DETECTED"
        save_guard_json(guard_data, args.guard_file)
        print("\n" + "!" * 80)
        print("[FATAL DB-GUARD VIOLATION] Final verification failed - main DB was mutated!")
        for issue in issues:
            print(f"    - {issue}")
        print("!" * 80 + "\n")
        sys.exit(1)

    guard_data["run_id"] = os.environ.get("ACCEPTANCE_RUN_ID", guard_data.get("run_id", "default_run"))
    guard_data["final"] = {
        "timestamp": now_iso,
        "status": "UNTOUCHED",
        "total_checkpoints": total_checkpoints,
        "summary": "Các thuộc tính được guard theo dõi không thay đổi giữa baseline và final checkpoint."
    }
    guard_data["overall_status"] = "PASSED_UNTOUCHED"
    save_guard_json(guard_data, args.guard_file)

    if args.copy_to:
        save_guard_json(guard_data, args.copy_to)
        print(f"[DB-GUARD] Copied finalized guard file to {args.copy_to}")

    print("\n" + "=" * 80)
    print(f"[DB-GUARD-FINAL-OK] Các thuộc tính được guard theo dõi không thay đổi giữa baseline và final checkpoint ({total_checkpoints} checkpoints).")
    print(f"SHA-256: {baseline_files.get('cheating_system.db', {}).get('sha256')}")
    print("=" * 80)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Production Database Fail-Closed Guard")
    subparsers = parser.add_subparsers(dest="action", required=True)

    # baseline
    p_base = subparsers.add_parser("baseline", help="Record baseline state of DB files")
    p_base.add_argument("--guard-file", required=True, help="Path to production_db_guard.json")

    # check
    p_check = subparsers.add_parser("check", help="Check files against baseline after a step")
    p_check.add_argument("--step", required=True, help="Step ID (e.g. STEP-01)")
    p_check.add_argument("--guard-file", required=True, help="Path to production_db_guard.json")
    p_check.add_argument("--read-only", action="store_true", help="Perform check without modifying guard file")

    # finalize
    p_final = subparsers.add_parser("finalize", help="Final verification and finalize guard json")
    p_final.add_argument("--guard-file", required=True, help="Path to production_db_guard.json")
    p_final.add_argument("--copy-to", default=None, help="Optional destination to copy finalized json")

    args = parser.parse_args()
    if args.action == "baseline":
        cmd_baseline(args)
    elif args.action == "check":
        cmd_check(args)
    elif args.action == "finalize":
        cmd_finalize(args)


if __name__ == "__main__":
    main()
