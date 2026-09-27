"""
================================================================================
EVIDENCE ZIP ARCHIVE INTEGRITY VALIDATOR (SPRINT 3.2B-R2)
================================================================================
Validates that SPRINT_3_2B_R2_EVIDENCE.zip:
1. Exists, valid ZIP header, CRC-32 integrity pass (testzip() returns None).
2. Cardinality audit:
   - Exactly 38 files total in ZIP.
   - Exactly 37 manifest-managed payload files.
   - Exactly 1 self-exclusion control file (sha256_manifest.txt).
   - 0 unmanaged files, 0 missing files.
3. Flawless trial decompression into temporary directory.
4. Cross-checks all 37 payload files bit-for-bit against sha256_manifest.txt.
5. Circular reference audit: outer ZIP SHA-256 does NOT appear inside any file.
6. Fail-Closed Invariant Verifications on extracted artifacts:
   - acceptance_summary.json arithmetic invariants (16 steps: 15 PASS, 1 NOT_CONFIGURED, 0 FAIL).
   - test_data_contamination_audit.json arithmetic invariants.
   - Cross-file RUN ID consistency across 7 metadata files.
   - SPRINT_3_2B_R2_REPORT.md facts consistency against DB guard and audit JSON.
7. External Post-Package DB Guard Checkpoint across cheating_system.db, -wal, -shm.
8. Generates FINAL_HANDOFF.json and writes FINAL_ZIP_VALIDATION.log outside ZIP.
================================================================================
"""

import os
import sys
import json
import hashlib
import zipfile
import tempfile
from datetime import datetime, timezone

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
ZIP_PATH = os.path.join(PROJECT_ROOT, "SPRINT_3_2B_R2_EVIDENCE.zip")
LOG_OUT_PATH = os.path.join(PROJECT_ROOT, "FINAL_ZIP_VALIDATION.log")
LEGACY_LOG_OUT_PATH = os.path.join(PROJECT_ROOT, "zip_validation.log")
HANDOFF_OUT_PATH = os.path.join(PROJECT_ROOT, "FINAL_HANDOFF.json")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts", "sprint_3_2b_r2")

log_lines = []


def log(msg=""):
    print(msg)
    log_lines.append(str(msg))


def flush_logs_and_exit(code=0):
    with open(LOG_OUT_PATH, "w", encoding="utf-8") as lf:
        lf.write("\n".join(log_lines) + "\n")
    with open(LEGACY_LOG_OUT_PATH, "w", encoding="utf-8") as lf:
        lf.write("\n".join(log_lines) + "\n")
    sys.exit(code)


log("=" * 80)
log("EXTERNAL EVIDENCE ZIP INTEGRITY & CROSS-VALIDATION (SPRINT 3.2B-R2)")
log("=" * 80)

if not os.path.exists(ZIP_PATH):
    log(f"[!] Error: Archive file does not exist at {ZIP_PATH}")
    flush_logs_and_exit(1)

zip_size = os.path.getsize(ZIP_PATH)
log(f"[*] Validating ZIP file: {ZIP_PATH} ({zip_size} bytes / {zip_size / (1024*1024):.2f} MB)")

# Calculate SHA-256 of the zip file
h_zip = hashlib.sha256()
with open(ZIP_PATH, "rb") as zf_raw:
    while chunk := zf_raw.read(65536):
        h_zip.update(chunk)
zip_sha256 = h_zip.hexdigest()
log(f"[*] Archive SHA-256:      {zip_sha256}")

try:
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        # 1. CRC Check
        bad_file = zf.testzip()
        if bad_file is not None:
            log(f"[!] CRC FAILURE: Corrupt file detected inside archive: {bad_file}")
            flush_logs_and_exit(1)
        log("[OK] ZIP CRC-32 checksum integrity check passed cleanly for all members.")

        # 2. File list check
        infolist = zf.infolist()
        total_uncompressed = sum(info.file_size for info in infolist)
        namelist = zf.namelist()
        norm_names = [n.replace("\\", "/") for n in namelist]

        log(f"[*] Total entries in archive: {len(norm_names)}")
        log(f"[*] Total uncompressed size:  {total_uncompressed} bytes ({total_uncompressed / (1024*1024):.2f} MB)")

        REQUIRED_IN_ZIP = [
            "run_id.txt",
            "run_info.json",
            "import_side_effect_audit.log",
            "audit_import_side_effects.json",
            "confidence_migration_audit.log",
            "confidence_migration_audit.json",
            "backend_all_tests.log",
            "preview_transport.log",
            "evaluation_tests.log",
            "tsc.log",
            "frontend_telemetry.log",
            "frontend_dual_camera.log",
            "build.log",
            "lint.log",
            "clip_audit.log",
            "clips_manifest.json",
            "benchmark_640x480.log",
            "benchmark_640x480.json",
            "benchmark_1920x1080.log",
            "benchmark_1920x1080.json",
            "git_capture.log",
            "git_status.txt",
            "git_status_porcelain.txt",
            "git_diff_stat.txt",
            "git_diff.patch",
            "untracked_files.txt",
            "untracked_files.json",
            "untracked_source_snapshot.zip",
            "secret_scan.log",
            "secret_scan_manifest.json",
            "test_data_contamination_audit.json",
            "production_db_guard.json",
            "SPRINT_3_2B_R2_REPORT.md",
            "acceptance_summary.json",
            "artifact_validation.log",
            "sha256_manifest.txt",
        ]

        missing_in_zip = []
        for req in REQUIRED_IN_ZIP:
            if not any(n.endswith(req) for n in norm_names):
                missing_in_zip.append(req)

        # Check MP4 evidence
        mp4_count = sum(1 for n in norm_names if n.endswith(".mp4"))
        log(f"[*] Found {mp4_count} evidence MP4 files in archive.")
        if mp4_count < 2:
            missing_in_zip.append("At least 2 evidence MP4 video files")

        if missing_in_zip:
            log("\n[!] MISSING REQUIRED FILES IN ZIP ARCHIVE:")
            for m in missing_in_zip:
                log(f"    - {m}")
            flush_logs_and_exit(1)

        log(f"[OK] All {len(REQUIRED_IN_ZIP)} mandatory files and {mp4_count} evidence clips confirmed present.")

        # 3. Trial Decompression into Temporary Directory and Manifest Cross-Checking
        log("\n[*] Performing trial decompression into temporary directory...")
        manifest_matches = []
        circular_leak_found = False

        with tempfile.TemporaryDirectory(prefix="zip_audit_") as tmp_dir:
            zf.extractall(tmp_dir)
            extracted_count = 0
            extracted_bytes = 0
            for root, _, files in os.walk(tmp_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    extracted_count += 1
                    extracted_bytes += os.path.getsize(fp)
            log(f"[OK] Trial decompression verified: {extracted_count} files ({extracted_bytes} bytes) cleanly extracted.")
            assert extracted_count == len(infolist), f"Extracted count {extracted_count} != infolist {len(infolist)}"

            # 4. Independent cross-verification against extracted sha256_manifest.txt
            manifest_file = os.path.join(tmp_dir, "sha256_manifest.txt")
            if not os.path.exists(manifest_file):
                log("[!] CRITICAL: sha256_manifest.txt not found in extracted archive!")
                flush_logs_and_exit(1)

            log("\n[*] Cross-checking extracted files against sha256_manifest.txt...")
            manifest_expected = {}
            with open(manifest_file, "r", encoding="utf-8") as mf:
                for line in mf:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split(maxsplit=1)
                    if len(parts) != 2:
                        continue
                    expected_hash, rel_path = parts
                    manifest_expected[rel_path.replace("\\", "/")] = expected_hash

            # Verify all manifest files exist in extraction and match sha256
            for rel_path, expected_hash in manifest_expected.items():
                extracted_file_path = os.path.join(tmp_dir, rel_path.replace("/", os.sep))
                if not os.path.exists(extracted_file_path):
                    log(f"[!] Manifest check failure: {rel_path} listed in manifest but not found in extraction!")
                    flush_logs_and_exit(1)

                h_item = hashlib.sha256()
                with open(extracted_file_path, "rb") as item_f:
                    while chunk := item_f.read(65536):
                        h_item.update(chunk)
                computed_hash = h_item.hexdigest()

                if computed_hash != expected_hash:
                    log(f"[!] Hash mismatch on {rel_path}: expected {expected_hash}, computed {computed_hash}")
                    flush_logs_and_exit(1)
                manifest_matches.append(rel_path)

            # Bi-directional check & cardinality audit
            # ZIP must have exactly 38 files.
            # sha256_manifest.txt must manage exactly 37 payload files.
            # sha256_manifest.txt is the ONLY allowed control file exception.
            unmanaged_files = []
            control_files = []
            for root, _, files in os.walk(tmp_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    rel_p = os.path.relpath(fp, tmp_dir).replace("\\", "/")
                    if rel_p == "sha256_manifest.txt":
                        control_files.append(rel_p)
                    elif rel_p not in manifest_expected:
                        unmanaged_files.append(rel_p)

            if len(control_files) != 1 or control_files[0] != "sha256_manifest.txt":
                log(f"[!] CARDINALITY ERROR: Expected exactly 1 control file 'sha256_manifest.txt', found: {control_files}")
                flush_logs_and_exit(1)

            if unmanaged_files:
                log(f"[!] UNMANAGED FILES DETECTED IN ZIP PAYLOAD ({len(unmanaged_files)} files not in sha256_manifest.txt):")
                for uf in unmanaged_files:
                    log(f"    - {uf}")
                flush_logs_and_exit(1)

            if len(norm_names) != 38:
                log(f"[!] CARDINALITY ERROR: Total files in ZIP: {len(norm_names)} (expected exactly 38)")
                flush_logs_and_exit(1)

            if len(manifest_matches) != 37:
                log(f"[!] CARDINALITY ERROR: Manifest payload files verified: {len(manifest_matches)} (expected exactly 37)")
                flush_logs_and_exit(1)

            log("[OK] Cardinality & Manifest Cross-Check PASS:")
            log("     - 37 payload files được manifest quản lý; sha256_manifest.txt là control file được miễn tự liệt kê.")
            log(f"     - Tất cả {len(manifest_matches)} tệp trong manifest khớp mã băm SHA-256 với bản giải nén, đúng 1 ngoại lệ control file cho phép, 0 tệp ngoài danh sách.")

            # 5. Circular Reference Audit: verify ZIP hash does NOT appear in any extracted file
            log("\n[*] Checking for illegal circular reference (ZIP hash inside archive files)...")
            zip_sha256_bytes = zip_sha256.encode("utf-8")
            for root, _, files in os.walk(tmp_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, "rb") as cf:
                            content = cf.read()
                            if zip_sha256_bytes in content:
                                log(f"[!] CIRCULAR REFERENCE DETECTED: {f} contains the SHA-256 of the outer ZIP archive!")
                                circular_leak_found = True
                    except Exception:
                        pass

            if circular_leak_found:
                log("[!] Circular reference check failed!")
                flush_logs_and_exit(1)
            log("[OK] Circular Reference Check PASS: 0 files inside archive contain outer ZIP SHA-256 hash.")

            # 6. FAIL-CLOSED INVARIANT VERIFICATIONS
            log("\n[*] Executing Automated Fail-Closed Invariant Verifications...")

            # 6.1 Summary Arithmetic Invariants
            acc_summary_path = os.path.join(tmp_dir, "acceptance_summary.json")
            with open(acc_summary_path, "r", encoding="utf-8-sig") as f:
                acc_summary = json.load(f)

            steps = acc_summary.get("steps", [])
            breakdown = acc_summary.get("acceptance_breakdown", {})
            total_steps = breakdown.get("total_steps")
            passed_steps = breakdown.get("passed_steps")
            not_configured_steps = breakdown.get("not_configured_steps")
            failed_steps = breakdown.get("failed_steps")

            assert total_steps == len(steps) == 16, f"Summary invariant failure: total_steps={total_steps}, len(steps)={len(steps)} (expected 16)"
            assert passed_steps == len([s for s in steps if s.get("status") == "PASS"]) == 15, f"Summary invariant failure: passed_steps={passed_steps} (expected 15)"
            assert not_configured_steps == len([s for s in steps if s.get("status") == "NOT_CONFIGURED"]) == 1, f"Summary invariant failure: not_configured_steps={not_configured_steps} (expected 1)"
            assert failed_steps == len([s for s in steps if s.get("status") == "FAIL"]) == 0, f"Summary invariant failure: failed_steps={failed_steps} (expected 0)"
            assert total_steps == passed_steps + not_configured_steps + failed_steps, "Summary invariant failure: total != pass + not_conf + fail"
            assert breakdown.get("acceptance_status") == "15 PASS, 1 NOT_CONFIGURED, 0 FAIL", "Summary status string mismatch"
            assert acc_summary.get("packaging_and_validation", {}).get("status") == "SUCCESS", "Packaging validation status must be SUCCESS"
            log("[OK] Summary Arithmetic Invariants PASS (16 steps: 15 PASS, 1 NOT_CONFIGURED, 0 FAIL, packaging: SUCCESS)")

            # 6.2 Contamination Arithmetic Invariants
            contam_path = os.path.join(tmp_dir, "test_data_contamination_audit.json")
            with open(contam_path, "r", encoding="utf-8-sig") as f:
                contam_data = json.load(f)

            curr_count = contam_data["current_db"]["record_count"]
            backup_count = contam_data["backup_db"]["record_count"]
            accumulated_count = contam_data["diff_summary"]["accumulated_records_count"]
            records_len = len(contam_data.get("accumulated_records", []))
            breakdown_sum = sum(contam_data["diff_summary"]["breakdown_by_classification"].values())

            assert curr_count - backup_count == accumulated_count, f"Contamination invariant: {curr_count} - {backup_count} != {accumulated_count}"
            assert accumulated_count == records_len, f"Contamination invariant: accumulated_count {accumulated_count} != records_len {records_len}"
            assert accumulated_count == breakdown_sum, f"Contamination invariant: accumulated_count {accumulated_count} != breakdown_sum {breakdown_sum}"
            
            stmt = contam_data["diff_summary"]["classification_statement"]
            assert f"{breakdown_sum}/{accumulated_count}" in stmt or str(accumulated_count) in stmt, f"Dynamic classification statement mismatch: {stmt}"

            test_acct = contam_data.get("test_run_accounting", {})
            init_prod = test_acct.get("production_snapshot_initial_count")
            init_iso = test_acct.get("isolated_initial_count")
            assert init_prod == init_iso == curr_count, f"Accounting invariant: init_prod {init_prod} != init_iso {init_iso}"

            final_iso = test_acct.get("isolated_final_count")
            test_delta = test_acct.get("isolated_test_delta", 0)
            gen_recs = test_acct.get("test_run_generated_records", [])
            if final_iso is not None:
                assert test_delta == final_iso - init_iso == len(gen_recs), f"Accounting invariant: test_delta {test_delta} != {final_iso - init_iso}"
            log(f"[OK] Contamination Arithmetic Invariants PASS ({curr_count} - {backup_count} == {accumulated_count} == {breakdown_sum}, test_delta={test_delta})")

            # 6.3 Cross-File RUN ID Consistency Check
            run_id_path = os.path.join(tmp_dir, "run_id.txt")
            with open(run_id_path, "r", encoding="utf-8-sig") as f:
                expected_run_id = f.read().strip().lstrip("\ufeff")
            log(f"[*] Expected Master RUN ID: '{expected_run_id}'")

            run_info_path = os.path.join(tmp_dir, "run_info.json")
            with open(run_info_path, "r", encoding="utf-8-sig") as f:
                r_info_id = json.load(f).get("run_id")
            assert r_info_id == expected_run_id, f"run_info.json run_id mismatch: {r_info_id} != {expected_run_id}"

            r_acc_id = acc_summary.get("run_id")
            assert r_acc_id == expected_run_id, f"acceptance_summary.json run_id mismatch: {r_acc_id} != {expected_run_id}"

            guard_path = os.path.join(tmp_dir, "production_db_guard.json")
            with open(guard_path, "r", encoding="utf-8-sig") as f:
                guard_data = json.load(f)
            r_guard_id = guard_data.get("run_id")
            assert r_guard_id == expected_run_id, f"production_db_guard.json run_id mismatch: {r_guard_id} != {expected_run_id}"

            clips_path = os.path.join(tmp_dir, "clips_manifest.json")
            with open(clips_path, "r", encoding="utf-8-sig") as f:
                r_clips_id = json.load(f).get("run_id")
            assert r_clips_id == expected_run_id, f"clips_manifest.json run_id mismatch: {r_clips_id} != {expected_run_id}"

            secrets_path = os.path.join(tmp_dir, "secret_scan_manifest.json")
            with open(secrets_path, "r", encoding="utf-8-sig") as f:
                r_sec_id = json.load(f).get("run_id")
            assert r_sec_id == expected_run_id, f"secret_scan_manifest.json run_id mismatch: {r_sec_id} != {expected_run_id}"

            r_contam_id = contam_data.get("run_id")
            assert r_contam_id == expected_run_id, f"test_data_contamination_audit.json run_id mismatch: {r_contam_id} != {expected_run_id}"

            log(f"[OK] Cross-File RUN ID Consistency PASS: '{expected_run_id}' identical across run_info.json, acceptance_summary.json, production_db_guard.json, clips_manifest.json, secret_scan_manifest.json, test_data_contamination_audit.json, run_id.txt.")

            # Compute SHA-256 of production_db_guard.json for handoff binding
            h_guard = hashlib.sha256()
            with open(guard_path, "rb") as gf:
                while chunk := gf.read(65536):
                    h_guard.update(chunk)
            guard_sha256 = h_guard.hexdigest()

            # 6.4 Report DB Facts Consistency Check
            report_path = os.path.join(tmp_dir, "SPRINT_3_2B_R2_REPORT.md")
            with open(report_path, "r", encoding="utf-8") as f:
                report_text = f.read()

            prod_db_baseline = guard_data.get("baseline", {}).get("files", {}).get("cheating_system.db", {})
            baseline_sha = prod_db_baseline.get("sha256")
            baseline_size = prod_db_baseline.get("size_bytes")

            assert baseline_sha in report_text, f"Report does not contain production DB baseline SHA-256 ({baseline_sha})!"
            assert f"{baseline_size:,}" in report_text or str(baseline_size) in report_text, f"Report does not contain production DB size ({baseline_size})!"
            assert str(curr_count) in report_text, f"Report does not contain production snapshot record count ({curr_count})!"
            log(f"[OK] Report DB Facts Consistency PASS: SPRINT_3_2B_R2_REPORT.md matches single structured source (SHA256: {baseline_sha[:16]}..., size: {baseline_size} bytes, count: {curr_count}).")

        # 7. External Post-Package DB Guard Checkpoint (Monitors DB/WAL/SHM after STEP-17)
        log("\n[*] Executing External Post-Package DB Guard Checkpoint across 3 DB files...")
        sys.path.insert(0, PROJECT_ROOT)
        from scripts.acceptance.db_guard import inspect_files, compare_with_baseline
        current_db_files = inspect_files(PROJECT_ROOT)
        baseline_files = guard_data.get("baseline", {}).get("files", {})
        is_untouched, guard_issues = compare_with_baseline(baseline_files, current_db_files)

        if not is_untouched:
            log("[!] FATAL POST-PACKAGE DB GUARD VIOLATION: Main DB files mutated during packaging!")
            for issue in guard_issues:
                log(f"    - {issue}")
            flush_logs_and_exit(1)

        external_db_guard_files = {}
        for fname in ["cheating_system.db", "cheating_system.db-wal", "cheating_system.db-shm"]:
            f_info = current_db_files.get(fname, {})
            b_info = baseline_files.get(fname, {})
            match = (
                f_info.get("exists") == b_info.get("exists") and
                f_info.get("size_bytes") == b_info.get("size_bytes") and
                f_info.get("mtime_ns") == b_info.get("mtime_ns") and
                f_info.get("sha256") == b_info.get("sha256")
            )
            external_db_guard_files[fname] = {
                "exists": f_info.get("exists"),
                "size_bytes": f_info.get("size_bytes"),
                "mtime_ns": f_info.get("mtime_ns"),
                "ctime_ns": f_info.get("ctime_ns"),
                "sha256": f_info.get("sha256"),
                "baseline_match": match
            }
            assert match, f"Post-package mismatch on {fname}: current={f_info} vs baseline={b_info}"
            log(f"[OK] DB Guard checked: {fname:<24} exists={f_info.get('exists')}, size={f_info.get('size_bytes')}, SHA256={str(f_info.get('sha256'))[:16]}... (MATCH)")

        post_package_guard_summary = "Trong phạm vi exists, size, mtime_ns, ctime_ns và SHA-256 được Production DB Guard theo dõi, không ghi nhận khác biệt giữa baseline và final checkpoint."
        log(f"[OK] External Post-Package DB Guard Checkpoint: PASS")
        log(f"     {post_package_guard_summary}")

    log("=" * 80)
    log("SUMMARY OF EXTERNAL EVIDENCE ZIP VALIDATION:")
    log(f"  RUN ID:                         {expected_run_id}")
    log(f"  Archive Path:                   {ZIP_PATH}")
    log(f"  File Size:                      {zip_size} bytes ({zip_size / (1024*1024):.2f} MB)")
    log(f"  Total Files in Zip:             {len(norm_names)} (expected 38)")
    log(f"  Manifest Payload Files:         {len(manifest_matches)} (37 payload files được manifest quản lý; sha256_manifest.txt là control file được miễn tự liệt kê)")
    log(f"  Manifest Self-Exclusion:        1 (sha256_manifest.txt)")
    log(f"  SHA-256:                        {zip_sha256}")
    log("  CRC-32 Check:                   PASS (0 corrupted members)")
    log("  Decompression Test:             PASS (all members cleanly extracted)")
    log(f"  Manifest Cross-Check:           PASS ({len(manifest_matches)} files verified against sha256_manifest.txt, 0 unmanaged)")
    log("  Circular Reference Check:       PASS (zero self-reference inside archive)")
    log("  Summary Invariants:             PASS (16 steps: 15 PASS, 1 NOT_CONFIGURED, 0 FAIL, packaging: SUCCESS)")
    log("  Contamination Invariants:       PASS (mathematical equations strictly asserted)")
    log(f"  Cross-File RUN ID Consistency:  PASS ('{expected_run_id}')")
    log("  Report DB Facts Consistency:    PASS (single structured source verified)")
    log(f"  External Post-Package DB Guard: PASS ({post_package_guard_summary})")
    log("  Candidate Verdict:              PASS WITH RESIDUAL RISKS — SOFTWARE/SYNTHETIC ACCEPTANCE")
    log("  Final PM Verdict:               PENDING INDEPENDENT ARTIFACT AUDIT")
    log("=" * 80)
    log("ZIP ARCHIVE INTEGRITY VALIDATION PASSED CLEANLY (EXIT 0)")
    log("=" * 80)

    # Generate FINAL_HANDOFF.json outside zip
    handoff_data = {
        "run_id": expected_run_id,
        "delivery_package": "SPRINT_3_2B_R2_EVIDENCE.zip",
        "zip_sha256": zip_sha256,
        "zip_size_bytes": zip_size,
        "zip_size_mb": round(zip_size / (1024 * 1024), 2),
        "production_db_guard_sha256": guard_sha256,
        "production_db_sha256": current_db_files.get("cheating_system.db", {}).get("sha256"),
        "external_post_package_db_guard": {
            "status": "PASS",
            "summary": post_package_guard_summary,
            "files": external_db_guard_files
        },
        "total_files_in_zip": len(norm_names),
        "manifest_managed_payload_files": len(manifest_matches),
        "manifest_control_file_exempted": "sha256_manifest.txt (exactly 1 control file)",
        "crc32_check": "PASS",
        "trial_extraction": "PASS",
        "sha256_manifest_check": "PASS",
        "manifest_verified_files_count": len(manifest_matches),
        "unmanaged_files_count": len(unmanaged_files),
        "circular_reference_check": "PASS",
        "candidate_verdict": "PASS WITH RESIDUAL RISKS — SOFTWARE/SYNTHETIC ACCEPTANCE",
        "final_pm_verdict": "PENDING INDEPENDENT ARTIFACT AUDIT",
        "verdict": "CANDIDATE VERDICT: PASS WITH RESIDUAL RISKS — SOFTWARE/SYNTHETIC ACCEPTANCE | FINAL PM VERDICT: PENDING INDEPENDENT ARTIFACT AUDIT",
        "acceptance_breakdown": {
            "total_steps": 16,
            "passed_steps": 15,
            "not_configured_steps": 1,
            "failed_steps": 0,
            "acceptance_status": "15 PASS, 1 NOT_CONFIGURED, 0 FAIL",
            "packaging_validation_status": "SUCCESS"
        },
        "hardware_status": "HARDWARE_ACCEPTANCE: PENDING (đã đặt mua 2 webcam EYD PC02, chờ nhận thiết bị và kiểm thử đồng thời)",
        "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        "validation_log_path": "FINAL_ZIP_VALIDATION.log"
    }

    with open(HANDOFF_OUT_PATH, "w", encoding="utf-8") as hf:
        json.dump(handoff_data, hf, indent=2, ensure_ascii=False)

    print(f"Validation log written to external path: {LOG_OUT_PATH}")
    print(f"Handoff JSON written to external path:   {HANDOFF_OUT_PATH}")
    flush_logs_and_exit(0)

except Exception as e:
    log(f"[!] Archive validation exception: {e}")
    import traceback
    log(traceback.format_exc())
    flush_logs_and_exit(1)