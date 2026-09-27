"""
================================================================================
GIT REPOSITORY STATE, DIFF & UNTRACKED EVIDENCE CAPTURE (SPRINT 3.2B-R2)
================================================================================
Extracts:
1. git status --short           -> artifacts/sprint_3_2b_r2/git_status.txt
2. git status --porcelain       -> artifacts/sprint_3_2b_r2/git_status_porcelain.txt
3. git diff --stat              -> artifacts/sprint_3_2b_r2/git_diff_stat.txt
4. git diff                     -> artifacts/sprint_3_2b_r2/git_diff.patch
5. Untracked test/script/impl   -> artifacts/sprint_3_2b_r2/untracked_files.txt
                                -> artifacts/sprint_3_2b_r2/untracked_files.json
6. Untracked Source Snapshot    -> artifacts/sprint_3_2b_r2/untracked_source_snapshot.zip
================================================================================
"""

import os
import sys
import json
import hashlib
import zipfile
import subprocess

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts", "sprint_3_2b_r2")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

RUN_ID = os.environ.get("ACCEPTANCE_RUN_ID", "r2_local")

print("=" * 80)
print(f"GIT REPOSITORY STATE & UNTRACKED EVIDENCE CAPTURE (Run ID: {RUN_ID})")
print("=" * 80)

def run_git(args, out_file):
    res = subprocess.run(["git"] + args, cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print(f"[!] Git command failed: git {' '.join(args)}\nError: {res.stderr}")
        sys.exit(res.returncode)
    
    out_path = os.path.join(ARTIFACTS_DIR, out_file)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(res.stdout)
    
    sz = os.path.getsize(out_path)
    print(f"[OK] Captured: {out_file:<25} ({sz} bytes)")
    return res.stdout

out_status = run_git(["status", "--short"], "git_status.txt")
out_porcelain = run_git(["status", "--porcelain"], "git_status_porcelain.txt")
run_git(["diff", "--stat"], "git_diff_stat.txt")
run_git(["diff"], "git_diff.patch")

# Process untracked files
untracked_candidates = []
for line in out_porcelain.splitlines():
    if line.startswith("?? "):
        raw_path = line[3:].strip().strip('"')
        full_p = os.path.join(PROJECT_ROOT, raw_path)
        if os.path.isdir(full_p):
            for root, _, files in os.walk(full_p):
                for f in files:
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, PROJECT_ROOT).replace("\\", "/")
                    untracked_candidates.append(rel)
        else:
            rel = raw_path.replace("\\", "/")
            untracked_candidates.append(rel)

# Filter out build artifacts, virtualenvs, git, and zip bundles
EXCLUDE_PREFIXES = ("artifacts/", ".venv/", "node_modules/", "data/evidence/", "data/isolated_acceptance/", ".git/", "dist/")
EXCLUDE_EXTENSIONS = (".zip", ".db", ".pyc", ".log")
EXCLUDE_ROOT_FILES = {
    "acceptance_summary.json",
    "FINAL_HANDOFF.json",
    "FINAL_ZIP_VALIDATION.log",
    "zip_validation.log",
    "SPRINT_3_2B_R2_EVIDENCE.zip",
    "handoffv2.zip",
    "SPRINT_3_2B_R2_REPORT.md",
    "test_data_contamination_audit.json",
    "production_db_guard.json",
}

untracked_files = []
for p in sorted(set(untracked_candidates)):
    if any(p.startswith(ex) for ex in EXCLUDE_PREFIXES):
        continue
    if any(p.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
        continue
    if p in EXCLUDE_ROOT_FILES or os.path.basename(p) in EXCLUDE_ROOT_FILES:
        continue
    untracked_files.append(p)

print(f"\n[*] Auditing {len(untracked_files)} untracked source/test/script files...")

untracked_records = []
txt_lines = [
    "# UNTRACKED TEST/SCRIPT/IMPLEMENTATION FILES MANIFEST",
    f"# Run ID: {RUN_ID}",
    f"# Total Files: {len(untracked_files)}",
    "# Format: SHA-256 | Size (bytes) | Category | File Path",
    "=" * 100
]

snapshot_zip_path = os.path.join(ARTIFACTS_DIR, "untracked_source_snapshot.zip")
if os.path.exists(snapshot_zip_path):
    os.remove(snapshot_zip_path)

with zipfile.ZipFile(snapshot_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z_snap:
    for rel_p in untracked_files:
        abs_p = os.path.join(PROJECT_ROOT, rel_p.replace("/", os.sep))
        sz = os.path.getsize(abs_p)
        h = hashlib.sha256()
        with open(abs_p, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        file_sha256 = h.hexdigest()

        # Categorize
        if "test" in rel_p.lower():
            category = "test_suite"
        elif rel_p.startswith("scripts/acceptance/"):
            category = "acceptance_script"
        elif rel_p.startswith("scripts/benchmark/"):
            category = "benchmark_script"
        elif rel_p.startswith("backend/"):
            category = "backend_implementation"
        elif rel_p.startswith("src/"):
            category = "frontend_implementation"
        elif rel_p.endswith(".md"):
            category = "documentation"
        else:
            category = "configuration"

        untracked_records.append({
            "path": rel_p,
            "size_bytes": sz,
            "sha256": file_sha256,
            "category": category
        })
        txt_lines.append(f"{file_sha256}  {sz:>8} B  [{category:<22}]  {rel_p}")
        z_snap.write(abs_p, rel_p)

# Write untracked_files.txt
txt_path = os.path.join(ARTIFACTS_DIR, "untracked_files.txt")
with open(txt_path, "w", encoding="utf-8") as f:
    f.write("\n".join(txt_lines) + "\n")

# Write untracked_files.json
json_path = os.path.join(ARTIFACTS_DIR, "untracked_files.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({
        "run_id": RUN_ID,
        "total_untracked_files": len(untracked_records),
        "files": untracked_records
    }, f, indent=2, ensure_ascii=False)

snap_sz = os.path.getsize(snapshot_zip_path)
print(f"[OK] Wrote untracked files manifest: untracked_files.txt ({len(untracked_records)} files)")
print(f"[OK] Wrote untracked files JSON:     untracked_files.json")
print(f"[OK] Created source snapshot zip:    untracked_source_snapshot.zip ({snap_sz} bytes)")

assert os.path.exists(os.path.join(ARTIFACTS_DIR, "git_status.txt")), "git_status.txt missing"
assert os.path.exists(os.path.join(ARTIFACTS_DIR, "git_status_porcelain.txt")), "git_status_porcelain.txt missing"
assert os.path.exists(os.path.join(ARTIFACTS_DIR, "git_diff_stat.txt")), "git_diff_stat.txt missing"
assert os.path.exists(os.path.join(ARTIFACTS_DIR, "git_diff.patch")), "git_diff.patch missing"
assert os.path.exists(txt_path), "untracked_files.txt missing"
assert os.path.exists(json_path), "untracked_files.json missing"
assert os.path.exists(snapshot_zip_path), "untracked_source_snapshot.zip missing"

print("=" * 80)
print("GIT STATE & UNTRACKED EVIDENCE CAPTURE COMPLETED SUCCESSFULLY (EXIT 0)")
print("=" * 80)
sys.exit(0)