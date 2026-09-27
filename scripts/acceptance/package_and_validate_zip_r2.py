"""
================================================================================
EVIDENCE ZIP PACKAGER & VALIDATOR (SPRINT 3.2B-R2)
================================================================================
1. Copies SPRINT_3_2B_R2_REPORT.md into artifacts/sprint_3_2b_r2/.
2. Packages all files from artifacts/sprint_3_2b_r2/ into SPRINT_3_2B_R2_EVIDENCE.zip.
3. Invokes validate_zip_r2.py to verify CRC-32, trial decompression, file list,
   and SHA-256, writing the validation log OUTSIDE the zip (PROJECT_ROOT/zip_validation.log).
================================================================================
"""

import os
import sys
import shutil
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
ZIP_PATH = os.path.join(PROJECT_ROOT, "SPRINT_3_2B_R2_EVIDENCE.zip")

print("=" * 80)
print("PACKAGING & VALIDATING SPRINT_3_2B_R2_EVIDENCE.ZIP")
print("=" * 80)

# Verify sha256_manifest.txt exists before packaging
manifest_path = os.path.join(ARTIFACTS_DIR, "sha256_manifest.txt")
assert os.path.exists(manifest_path), f"Frozen sha256_manifest.txt missing from {ARTIFACTS_DIR}!"

if os.path.exists(ZIP_PATH):
    os.remove(ZIP_PATH)

# 2. Package artifacts
print(f"[*] Packaging artifacts from {ARTIFACTS_DIR} into {ZIP_PATH}...")
file_count = 0
with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(ARTIFACTS_DIR):
        for f in files:
            full_path = os.path.join(root, f)
            arc_name = os.path.relpath(full_path, ARTIFACTS_DIR).replace("\\", "/")
            zf.write(full_path, arc_name)
            file_count += 1

zip_size = os.path.getsize(ZIP_PATH)
print(f"[OK] Created archive: {ZIP_PATH} ({file_count} files, {zip_size} bytes / {zip_size / (1024*1024):.2f} MB)")

# 3. Validate by invoking validate_zip_r2 directly (writes log outside zip)
val_script = os.path.join(CURRENT_DIR, "validate_zip_r2.py")
res = subprocess.run([sys.executable, val_script], cwd=PROJECT_ROOT)
sys.exit(res.returncode)