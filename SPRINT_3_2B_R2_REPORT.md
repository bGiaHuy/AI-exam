# BÁO CÁO NGHIỆM THU SPRINT 3.2B-R2 (EVIDENCE CLOSURE)

---

## A. KẾT LUẬN NGHIỆM THU (VERDICT)

```text
CANDIDATE VERDICT: PASS WITH RESIDUAL RISKS — SOFTWARE/SYNTHETIC ACCEPTANCE
FINAL PM VERDICT: PENDING INDEPENDENT ARTIFACT AUDIT
ACCEPTANCE STATUS: 15 PASS, 1 NOT_CONFIGURED, 0 FAIL
PACKAGING & VALIDATION: SUCCESS
HARDWARE STATUS: HARDWARE_ACCEPTANCE: PENDING — đã đặt mua 2 webcam EYD PC02, chờ nhận thiết bị và kiểm thử đồng thời.
RUN ID: sprint32b_r2_20260917_001625
DELIVERABLES: SPRINT_3_2B_R2_EVIDENCE.zip, FINAL_HANDOFF.json, FINAL_ZIP_VALIDATION.log
CARDINALITY: 38 files trong ZIP (37 payload files được manifest quản lý; sha256_manifest.txt là control file được miễn tự liệt kê).
MAIN DATABASE INTEGRITY: Trong phạm vi exists, size, mtime_ns, ctime_ns và SHA-256 được Production DB Guard theo dõi, không ghi nhận khác biệt giữa baseline và final checkpoint (SHA-256 trước và sau giống nhau).
GIT & MODEL STATUS: Git không ghi nhận thay đổi trong model/ tại thời điểm kiểm tra; Runner không thực hiện commit, tag hoặc push.
```

Các bước kiểm thử phần mềm được cấu hình trong phạm vi sprint đã pass các bước tuần tự với exit code `0` thông qua bộ điều phối tự động `scripts/acceptance/run_sprint32b_r2.ps1` trên thư mục artifact sạch và cơ sở dữ liệu snapshot tạo bởi SQLite Online Backup API (kết nối read-only). Cơ sở dữ liệu chính `cheating_system.db` cùng các tệp liên quan (`-wal`, `-shm`) được bảo vệ bằng chốt chặn fail-closed `production_db_guard.json`, xác nhận trong phạm vi exists, size, mtime_ns, ctime_ns và SHA-256 được Production DB Guard theo dõi, không ghi nhận khác biệt giữa baseline và final checkpoint.

---

## B. XÁC NHẬN CHẨN ĐOÁN VÀ NGUYÊN TẮC TRUNG THỰC

> **Xác nhận trung thực:**
> - Các lượt chẩn đoán ban đầu từng bị gián đoạn hoặc dừng thủ công trong quá trình phân tích và sửa lỗi deadlock / test runner; kết quả nghiệm thu dưới đây được chạy mới độc lập trong một phiên duy nhất trên thư mục artifact sạch, mỗi bước có raw log tương ứng và tự kết thúc với exit code `0`.
> - Không tái sử dụng bất kỳ log thô, JSON hoặc video MP4 nào của lần chạy trước.
> - Thời lượng benchmark nội bộ (`elapsed_seconds`) được phân biệt tường minh với thời gian thực thi lệnh từ bộ runner (`duration_seconds`).
> - Phân loại linter trung thực: Repository không cấu hình standalone linter (ESLint/Biome); lệnh `npm run lint` trong `package.json` thực chất là alias gọi `tsc --noEmit`. Trạng thái linter được ghi nhận chính xác là `NOT_CONFIGURED`, trong khi toàn bộ kiểm tra kiểu TypeScript được xác thực độc lập tại STEP-06 (`tsc --noEmit`).
> - Giới hạn phạm vi mô hình: Git status/diff không ghi nhận thay đổi trong model/ ở phạm vi bằng chứng hiện có.
> - Không sử dụng các tuyên bố phóng đại; kết luận được giới hạn chuẩn mực là **'không quan sát thấy các side effect bị cấm tại checkpoint được liệt kê'**.

---

## C. BẢNG TỔNG HỢP CÁC BƯỚC NGHIỆM THU ĐỘC LẬP

| Step ID | Hạng mục kiểm thử | Lệnh thực thi | Mục tiêu đo lường / kiểm chứng | Trạng thái | Log File |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **STEP-01** | Import Side-Effect & Metadata Audit (3 Checkpoints) | `python scripts/acceptance/audit_import_side_effects.py` | Đo 7 tham số tại Checkpoint A, B, C; không quan sát thấy side effect bị cấm | **PASS** | `import_side_effect_audit.log` |
| **STEP-02** | Read-Only SQLite Confidence Migration Audit | `python scripts/acceptance/audit_db_migration.py` | Kiểm tra PRAGMA integrity, phân bổ canonical [0,1], kiểm tra idempotency | **PASS** | `confidence_migration_audit.log` |
| **STEP-03** | Backend Aggregate Test Suite (83 tests) | `python -m unittest backend.tests.test_refactored_system backend.tests.test_dual_camera_pipeline backend.tests.test_sprint32b backend.tests.test_preview_transport backend.tests.test_confidence_contract -v` | 83 tests passed (bao gồm confidence contract strict fail-closed) | **PASS** | `backend_all_tests.log` |
| **STEP-04** | Preview WebSocket Invariants & Deep Integration (8 tests) | `python -m unittest backend.tests.test_preview_transport -v` | 8 tests passed (bao gồm slow client & graceful cleanup) | **PASS** | `preview_transport.log` |
| **STEP-05** | Evaluation Harness Mathematical Contract Tests (22 tests) | `python -m unittest scripts.evaluation.tests.test_evaluation_harness -v` | 22 tests passed (độ chính xác thống kê F1/Recall) | **PASS** | `evaluation_tests.log` |
| **STEP-06** | Frontend TypeScript Strict Type Check | `npx tsc --noEmit` | 0 type errors (toàn bộ codebase đạt type check nghiêm ngặt) | **PASS** | `tsc.log` |
| **STEP-07** | Frontend Telemetry Contract Verification | `npx tsx src/services/__tests__/test_telemetry_contract.ts` | 7 telemetry fields asserted đúng cấu trúc | **PASS** | `frontend_telemetry.log` |
| **STEP-08** | Frontend Dual-Camera Protocol Contract (15 tests) | `npx tsx src/services/__tests__/test_frontend_dual_camera.ts` | 15 tests passed | **PASS** | `frontend_dual_camera.log` |
| **STEP-09** | Vite Production Bundle Build | `npm run build` | dist/ bundle production generated thành công | **PASS** | `build.log` |
| **STEP-10** | Frontend lint configuration audit — NOT_CONFIGURED | `npm run lint` | Ghi nhận: npm run lint trỏ alias `tsc --noEmit` (typechecker, không phải linter); linter độc lập chưa được cấu hình | **NOT_CONFIGURED** | `lint.log` |
| **STEP-11** | Dual-Camera Clip Pre/Post-Roll Generation & Audit | `python scripts/acceptance/generate_evidence_clips_r2.py` | Phân tách rõ ràng ~5s pre-roll, trigger, ~10s post-roll, 0 nhiễm chéo | **PASS** | `clip_audit.log` |
| **STEP-12** | 62s Memory Benchmark Scenario A (640x480 @ 15 FPS) | `python scripts/benchmark/benchmark_dual_camera.py --scenario A --duration 62.0` | `elapsed_seconds` = 62.08s >= 60s, RAM slope = +0.0059 MB/s | **PASS** | `benchmark_640x480.log` |
| **STEP-13** | 62s Memory Benchmark Scenario B (1920x1080 @ 15 FPS) | `python scripts/benchmark/benchmark_dual_camera.py --scenario B --duration 62.0` | `elapsed_seconds` = 62.08s >= 60s, RAM slope = +0.0236 MB/s | **PASS** | `benchmark_1920x1080.log` |
| **STEP-14** | Git Repository Status, Diff & Untracked Evidence Capture | `python scripts/acceptance/capture_git_state_r2.py` | Trích xuất status, diff.patch, untracked manifest & snapshot (loại trừ root artifacts) | **PASS** | `git_capture.log` |
| **STEP-15** | Secret & Credential Leakage Scanner (Fail-Closed) | `python scripts/acceptance/secret_scan_r2.py` | Quét cấu hình root, patch, untracked snapshot, SQLite; line-level allowlist | **PASS** | `secret_scan.log` |
| **STEP-16** | Artifact Integrity & SHA-256 Manifest Generation | `python scripts/acceptance/validate_artifacts_r2.py` | Đóng băng thư mục artifact và sinh `sha256_manifest.txt` | **PASS** | `artifact_validation.log` |

### Thống kê bước kiểm thử:
- **Tổng số bước thực thi:** 16 bước
- **passed_steps:** 15
- **not_configured_steps:** 1 (STEP-10: Frontend lint configuration audit — NOT_CONFIGURED)
- **failed_steps:** 0
- **Kết luận:** 15 PASS, 1 NOT_CONFIGURED, 0 FAIL.

---

## D. KIỂM TOÁN CSDL, CHUẨN HÓA ĐỘ TIN CẬY VÀ ĐIỀU TRA NHIỄM DỮ LIỆU

### 1. Kiểm toán độ tin cậy CSDL (Confidence Normalization Audit)
Script kiểm toán chỉ đọc `scripts/acceptance/audit_db_migration.py` đã thực thi trên cơ sở dữ liệu snapshot cô lập (tạo từ `cheating_system.db` qua SQLite Online Backup API) và tệp sao lưu kiểm chứng `cheating_system_backup_20260916_004041_0d9a80.db`:

- **Tệp sao lưu kiểm chứng:** `cheating_system_backup_20260916_004041_0d9a80.db` (baseline backup 66 record, 65,536 bytes, SHA-256: `029788dda6212a81...`) — Kết quả toàn vẹn SQLite: `ok`.
- **Tệp CSDL snapshot cô lập:** `isolated_acceptance.db` (97 bản ghi, 77,824 bytes) — Kết quả toàn vẹn SQLite: `ok`.
- **Tổng số bản ghi sự cố (incidents):** **97** bản ghi.
- **Số bản ghi canonical trong đoạn [0.0, 1.0]:** **97 / 97 (100.0%)**.
- **Số bản ghi legacy trong khoảng (1.0, 100.0]:** **0** (đã được chuẩn hóa canonical).
- **Số bản ghi lỗi / vi phạm (< 0, > 100, NaN, NULL):** **0**.
- **Phổ độ tin cậy thực tế trong DB:** Min = `0.8800`, Max = `1.0000`, Mean = `0.9423`.
- **Kiểm tra tính bất biến (Idempotency Check):** Sao chép CSDL sang thư mục tạm thời, chạy lại hàm chuẩn hóa trên toàn bộ bản ghi; kết quả **0 bản ghi bị thay đổi thêm**, xác nhận tính idempotent.

### 2. Điều tra và làm rõ việc ghi dữ liệu vào `cheating_system.db` (Test Data Contamination Audit)
Thực hiện chỉ thị của PM, kiểm toán chỉ đọc đối chiếu CSDL ban đầu với baseline backup 66 record (`cheating_system_backup_20260916_004041_0d9a80.db`):

- **Tệp sao lưu kiểm chứng:** `cheating_system_backup_20260916_004041_0d9a80.db` (baseline backup 66 record, 65,536 bytes, SHA-256: `029788dda6212a81b669b65c73e88180d823e85f38e13774c3d616d507e0b338`).
- **Tệp CSDL chính tại thời điểm snapshot:** `cheating_system.db` (97 bản ghi, 77,824 bytes, SHA-256: `dca92ac7ea0be816ca41fb00b25af73dce18a632e6756b53fb3a519ecd30c499`).
- **Chênh lệch bản ghi tích lũy:** **+31 bản ghi** (tăng từ 66 lên 97 bản ghi trước khi chạy acceptance).
- **Kết luận phân loại:** **31/31 record được phân loại likely_test_data theo evidence đã liệt kê**.
  - `likely_test_data`: **31 / 31 bản ghi**.
  - **Phân định mốc 26 bản ghi:**
    - **26 bản ghi chuẩn:** thuộc phạm vi quyết định hoãn xử lý của PM (giữ nguyên không xóa, không restore).
    - **5 bản ghi phát sinh sau mốc 26:** được phân loại rõ ràng theo bằng chứng (ID/Session metadata test) và tách riêng hồ sơ.
- **Kế toán chạy kiểm thử cô lập (Isolated Test Run Accounting):**
  - `production_snapshot_initial_count`: **97** bản ghi.
  - `isolated_initial_count`: **97** bản ghi (khớp 100% với CSDL chính tại thời điểm snapshot).
  - `isolated_final_count`: **103** bản ghi.
  - `isolated_test_delta`: **+6** bản ghi phát sinh do các test suites ghi vào DB cô lập.
  - `cheating_system.db` (CSDL chính): **delta = 0**, không ghi nhận bất kỳ đột biến nào.
- **Cơ chế phát sinh lịch sử:** Trước khi áp dụng snapshot cô lập, các test suite và script sinh clip import trực tiếp `DB_PATH` tĩnh từ `backend/database.py`, do đó worker nền ghi vào CSDL chính. Toàn bộ chênh lệch là dữ liệu từ test runner.
- **Cơ chế cô lập CSDL đã được thiết lập:**
  - Tạo isolated acceptance DB theo SQLite Online Backup API (`sqlite3.Connection.backup()`) tới `data/isolated_acceptance/<run_id>/isolated_acceptance.db`, verify `PRAGMA integrity_check = 'ok'`.
  - Cập nhật `backend/database.py`, `backend/migrate_db.py`, `scripts/acceptance/generate_evidence_clips_r2.py`, `audit_db_migration.py`, `audit_import_side_effects.py` để phân giải động `DB_PATH` và `DATABASE_URL` theo biến môi trường `AIEXAM_ISOLATED_DB`.
  - Bổ sung bước preflight fail-closed (`scripts/acceptance/preflight_db_isolation.py`) xác nhận `DB_PATH` là đường dẫn absolute tới CSDL cô lập, SQLAlchemy engine kết nối đúng và khác `cheating_system.db`.
- **Quyết định xử lý CSDL từ PM (DB Cleanup Decision):**
  - Giữ nguyên tạm thời `cheating_system.db` hiện tại.
  - Không xóa 26 record.
  - Không restore bản backup 66 record.
  - Trong phạm vi exists, size, mtime_ns, ctime_ns và SHA-256 được Production DB Guard theo dõi, không ghi nhận khác biệt giữa baseline và final checkpoint.
  - Giữ `test_data_contamination_audit.json` làm hồ sơ để xử lý cleanup ở work item riêng.
  - Lưu ý: Quyết định trước đó của PM áp dụng cho 26 record đã biết; các record sinh mới sau này không mặc nhiên thuộc quyết định đó. Không xóa hoặc restore bất kỳ record nào.

### 3. Kiểm toán chốt chặn CSDL chính (Production DB Guard)
Chốt chặn fail-closed `scripts/acceptance/db_guard.py` giám sát chặt chẽ `cheating_system.db`, `cheating_system.db-wal`, `cheating_system.db-shm` qua các thông số: `exists`, `size_bytes`, `mtime` (độ chính xác nano giây), `SHA-256` và `ctime_ns` (telemetry):
- **Baseline recorded:** `2026-09-17T00:02:30.287202+00:00`.
- **Số lượng checkpoint kiểm tra (sau mỗi bước):** **16 checkpoints**.
- **Trạng thái kết thúc:** `PASSED_UNTOUCHED`.
- **Xác nhận bảo toàn:** Trong phạm vi exists, size, mtime_ns, ctime_ns và SHA-256 được Production DB Guard theo dõi, không ghi nhận khác biệt giữa baseline và final checkpoint (SHA-256, kích thước, timestamp bảo toàn; không checkpoint, không truncate, không restore lên CSDL chính).

---

## E. KIỂM TOÁN SIDE-EFFECT IMPORT & METADATA OVERHEAD

Script `audit_import_side_effects.py` đã đo đạc độc lập tại 3 checkpoint:
- **Baseline:** `threads=1` (`['MainThread']`), SQLite size = 77824 bytes.
- **Checkpoint A (import services.ring_buffer):** Thời gian `4.44 ms`, delta thread = `0`, SQLite untouched, DB worker started = `False`, model calls = `0`, VideoCapture calls = `0`.
- **Checkpoint B (from main import app):** Thời gian `8.23 ms`, delta thread = `0`, SQLite untouched, DB worker started = `False`, model calls = `0`, VideoCapture calls = `0`, camera manager initialized = `False`.
- **Checkpoint C (GET /api/camera/sources):** Thời gian `21.97 ms`, status = `200`, delta thread = `0`, SQLite untouched, DB worker started = `False`, model calls = `0`, VideoCapture calls = `0`.
- **Kết luận chốt chặn:** 'Xác nhận thành công: không quan sát thấy các side effect bị cấm tại checkpoint được liệt kê'.

---

## F. PHÂN TÁCH MINH BẠCH PRE-ROLL VÀ POST-ROLL CHO 2 CAMERA

Phương pháp kiểm chứng quang học độc lập tạo 2 luồng video synthetic riêng biệt với marker màu và chuỗi nhị phân:
- **Cam 1 (Góc trước - Green signature):** Nền xanh lá cây thuần túy (`G > 180, B < 40`), văn bản `[CAM1_FRONT]`.
- **Cam 2 (Góc bên - Blue signature):** Nền xanh dương thuần túy (`B > 180, G < 40`), văn bản `[CAM2_SIDE]`.

### 1. Cam 1 Clip (`inc_cam1_1789604230_4e07c3.mp4`):
- **Pre-roll frames:** **73 frames** (~4.87s, tiệm cận 5.0s lý thuyết)
- **Event trigger frames:** **3 frames**
- **Post-roll frames:** **149 frames** (~9.93s, tiệm cận 10.0s lý thuyết)
- **Tổng frame giải mã:** **225 frames** (15.0s @ 15.0 FPS)
- **Nhiễm chéo từ Cam 2:** **0 frames (0.00%)**
- **SHA-256:** `bbb30dcfcd41bf55ca15df1118a9f013e75c66b49e89dfc9f95a0bb8154bb37a`

### 2. Cam 2 Clip (`inc_cam2_1789604230_581831.mp4`):
- **Pre-roll frames:** **73 frames** (~4.87s, tiệm cận 5.0s lý thuyết)
- **Event trigger frames:** **3 frames**
- **Post-roll frames:** **149 frames** (~9.93s, tiệm cận 10.0s lý thuyết)
- **Tổng frame giải mã:** **225 frames** (15.0s @ 15.0 FPS)
- **Nhiễm chéo từ Cam 1:** **0 frames (0.00%)**
- **SHA-256:** `d0a4d1244ae3dda11957ce7fea199a44b2d004e40e77565ea9fb4f568ace9bbd`

---

## G. KẾT QUẢ BENCHMARK BỘ NHỚ VÀ ĐỘ DỐC ỔN ĐỊNH

> **Phân loại kiểm thử:** `[synthetic source, stub detector, backend integration]`
> - Đo đạc sử dụng frame synthetic và stub detector có độ trễ mô phỏng 45ms nhằm kiểm tra tính ổn định bộ nhớ của RingBuffer JPEG và thuật toán luân phiên công bằng.
> - KHÔNG dùng để tuyên bố tốc độ mô hình AI thật.

### 1. Scenario A (640x480 @ 15 FPS)
- **Thời lượng đo lường thực tế (`elapsed_seconds`):** **62.08s** (đáp ứng mandate >= 60s)
- **RAM Profile:** Start = `202.25 MB`, Warmup (T=20s) = `213.73 MB`, Peak = `214.01 MB`, End = `214.00 MB`
- **Hệ số góc RAM sau warmup (Slope T >= 20s):** `+0.0059 MB/s` (mặt bằng ổn định, không quan sát thấy tăng trưởng không bị chặn)
- **Tỷ lệ công bằng xử lý (Fairness Ratio):** Cam 1 = `50.0%`, Cam 2 = `50.0%`
- **Dung lượng RingBuffer đo lường (JPEG synthetic):** `1.55 MB/cam`

### 2. Scenario B (1920x1080 @ 15 FPS)
- **Thời lượng đo lường thực tế (`elapsed_seconds`):** **62.08s** (đáp ứng mandate >= 60s)
- **RAM Profile:** Start = `202.42 MB`, Warmup (T=20s) = `247.89 MB`, Peak = `248.88 MB`, End = `237.04 MB`
- **Hệ số góc RAM sau warmup (Slope T >= 20s):** `+0.0236 MB/s` (mặt bằng ổn định)
- **Tỷ lệ công bằng xử lý (Fairness Ratio):** Cam 1 = `50.0%`, Cam 2 = `50.0%`
- **Dung lượng RingBuffer đo lường (JPEG synthetic):** `9.55 MB/cam`

---

## H. BẰNG CHỨNG CÁC TỆP UNTRACKED VÀ SOURCE SNAPSHOT AUDIT

Theo quy tắc zero-git-commit trong quá trình nghiệm thu, toàn bộ 49 tệp mã nguồn mới (test suites, acceptance scripts, benchmark scripts, implementation files) được kiểm toán trong `untracked_files.txt` và được đóng gói trong `untracked_source_snapshot.zip`:

> **Tuyên bố về thư mục `model/`:** Git status/diff không ghi nhận thay đổi trong model/ ở phạm vi bằng chứng hiện có.

| STT | Phân loại | Kích thước | SHA-256 (rút gọn) | Đường dẫn tệp |
| :---: | :--- | :---: | :--- | :--- |
| 1 | Configuration | 1,223 B | `fb77af34d54e...` | `.vercelignore` |
| 2 | Documentation | 5,247 B | `9a875403e99b...` | `DEMO_ACCESS_RUNBOOK.md` |
| 3 | Documentation | 12,040 B | `d5b913d13de6...` | `DUAL_CAMERA_ACCEPTANCE.md` |
| 4 | Backend Implementation | 1,871 B | `fa0beaf251d0...` | `backend/confidence.py` |
| 5 | Backend Implementation | 8,825 B | `a7d5221afd88...` | `backend/services/camera_manager.py` |
| 6 | Backend Implementation | 26,595 B | `80bbd7dd2dfb...` | `backend/services/camera_source.py` |
| 7 | Backend Implementation | 13,688 B | `5fab5fa47da9...` | `backend/services/fair_scheduler.py` |
| 8 | Test Suite | 11,769 B | `c79707e55111...` | `backend/tests/test_confidence_contract.py` |
| 9 | Test Suite | 34,903 B | `063dff3321b5...` | `backend/tests/test_dual_camera_pipeline.py` |
| 10 | Test Suite | 16,065 B | `da629dd38497...` | `backend/tests/test_preview_transport.py` |
| 11 | Test Suite | 13,853 B | `32492677e6db...` | `backend/tests/test_sprint32b.py` |
| 12 | Configuration | 6,303 B | `97e7cf36801a...` | `data/benchmark_reports/benchmark_1920x1080.json` |
| 13 | Configuration | 6,302 B | `164e885ff4bf...` | `data/benchmark_reports/benchmark_640x480.json` |
| 14 | Configuration | 1,002 B | `1a8f8496d5d9...` | `data/benchmark_reports/benchmark_a_640x480.json` |
| 15 | Configuration | 1,008 B | `604fb9aaefef...` | `data/benchmark_reports/benchmark_b_1920x1080.json` |
| 16 | Configuration | 2,010 B | `ac7d98ee9d72...` | `data/benchmark_reports/dual_camera_benchmark_result.json` |
| 17 | Configuration | 1,402 B | `6f3de06b0181...` | `data/benchmark_reports/e2e_report_2026-09-14T04-16-59-975Z.csv` |
| 18 | Configuration | 2,976 B | `9cab61e996bb...` | `data/benchmark_reports/e2e_report_2026-09-14T04-16-59-975Z.json` |
| 19 | Configuration | 1,389 B | `1ea08d5375c5...` | `data/benchmark_reports/e2e_report_2026-09-14T04-19-44-644Z.csv` |
| 20 | Configuration | 2,970 B | `2c134f438e23...` | `data/benchmark_reports/e2e_report_2026-09-14T04-19-44-644Z.json` |
| 21 | Configuration | 1,516 B | `9d5f3a3e60d1...` | `data/benchmark_reports/e2e_report_2026-09-14T06-42-37-217Z.csv` |
| 22 | Configuration | 4,358 B | `fcf3390f64f7...` | `data/benchmark_reports/e2e_report_2026-09-14T06-42-37-217Z.json` |
| 23 | Configuration | 1,510 B | `6e296d10e7ba...` | `data/benchmark_reports/e2e_report_2026-09-14T06-45-39-250Z.csv` |
| 24 | Configuration | 4,356 B | `d36495d4da6e...` | `data/benchmark_reports/e2e_report_2026-09-14T06-45-39-250Z.json` |
| 25 | Configuration | 1,511 B | `4127f54f1c56...` | `data/benchmark_reports/e2e_report_2026-09-14T06-52-20-321Z.csv` |
| 26 | Configuration | 4,476 B | `e9b12d142f90...` | `data/benchmark_reports/e2e_report_2026-09-14T06-52-20-321Z.json` |
| 27 | Configuration | 1,643 B | `77ba5e0d3053...` | `data/benchmark_reports/phone_eval/phone_eval_summary.json` |
| 28 | Configuration | 1,749 B | `46bbb1cce862...` | `data/benchmark_reports/posture_eval/posture_eval_summary.json` |
| 29 | Acceptance Script | 9,255 B | `9e643f13bffc...` | `scripts/acceptance/audit_db_migration.py` |
| 30 | Acceptance Script | 12,274 B | `9d0c485c88ef...` | `scripts/acceptance/audit_import_side_effects.py` |
| 31 | Test Suite | 18,917 B | `fbd8abdf621c...` | `scripts/acceptance/audit_test_data_contamination.py` |
| 32 | Acceptance Script | 7,259 B | `0fede33a7eeb...` | `scripts/acceptance/capture_git_state_r2.py` |
| 33 | Acceptance Script | 7,993 B | `a92cacafc808...` | `scripts/acceptance/create_isolated_snapshot.py` |
| 34 | Acceptance Script | 9,926 B | `7c256a7d732f...` | `scripts/acceptance/db_guard.py` |
| 35 | Acceptance Script | 19,000 B | `ec0b071a1612...` | `scripts/acceptance/generate_evidence_clips_r2.py` |
| 36 | Acceptance Script | 38,643 B | `e1673c2b8c63...` | `scripts/acceptance/generate_report_r2.py` |
| 37 | Acceptance Script | 2,422 B | `4c6e20dc8515...` | `scripts/acceptance/package_and_validate_zip_r2.py` |
| 38 | Acceptance Script | 5,020 B | `c621be02d4e2...` | `scripts/acceptance/preflight_db_isolation.py` |
| 39 | Acceptance Script | 17,532 B | `319fa314403e...` | `scripts/acceptance/run_sprint32b_r2.ps1` |
| 40 | Acceptance Script | 17,456 B | `24885b9399f9...` | `scripts/acceptance/secret_scan_r2.py` |
| 41 | Acceptance Script | 12,871 B | `c43fb9c30ead...` | `scripts/acceptance/validate_artifacts_r2.py` |
| 42 | Acceptance Script | 26,356 B | `250d3dd53556...` | `scripts/acceptance/validate_zip_r2.py` |
| 43 | Benchmark Script | 17,166 B | `c4b48b848dba...` | `scripts/benchmark/benchmark_dual_camera.py` |
| 44 | Frontend Implementation | 3,199 B | `b4814c84d356...` | `src/components/demo/DemoWatermark.tsx` |
| 45 | Frontend Implementation | 1,652 B | `ba321821b51c...` | `src/config/demoConfig.ts` |
| 46 | Frontend Implementation | 1,824 B | `4705eed2f376...` | `src/demo/mockDemoData.ts` |
| 47 | Test Suite | 13,786 B | `f10ba69ba219...` | `src/services/__tests__/test_frontend_dual_camera.ts` |
| 48 | Frontend Implementation | 287 B | `77744b14b187...` | `src/vite-env.d.ts` |
| 49 | Configuration | 656 B | `339147c8571b...` | `vercel.json` |

---

## I. QUÉT BẢO MẬT (SECRET SCAN WITH FAIL-CLOSED AUDIT)

Script quét bí mật `scripts/acceptance/secret_scan_r2.py` tuân thủ nguyên tắc fail-closed:
- **Tổng số tệp được quét:** **176 tệp** (bao gồm cấu hình root, dist bundle, test files, patch git_diff, và các tệp trong snapshot).
- **Tổng số tệp bỏ qua với lý do cụ thể:** **37 tệp** (ghi nhận tường minh trong `secret_scan_manifest.json`).
- **Chính sách allowlist nghiêm ngặt:** Không allowlist cả file `camera_source.py`; mọi mẫu nhạy cảm chỉ được duyệt qua cơ chế line-level regex đối chiếu với các chuỗi mock synthetic trong unit test.
- **Số lượng allowlist hits được ghi nhận:** **20 hits** (chỉ bao gồm các chuỗi synthetic canary và unit test redaction assertions).
- **Vi phạm bí mật phát hiện:** **0 vi phạm**.

---

## J. BLOCKER REGISTER VÀ RỦI RO DƯ LƯỢNG (BLOCKER REGISTER & RESIDUAL RISKS)

### 1. Blocker Register (Ba Blocker Độc Lập):

- **D-01 — Training Dataset Lineage**
  - **Status:** `PENDING_HANDOFF_IMPORT`
  - **Mô tả:** Repository chưa import và xác minh gói training handoff. Không liên quan đến untracked source snapshot hoặc merge code.

- **D-02 — Phone Independent Untouched Holdout Evaluation**
  - **Status:** `OPEN`
  - **Mô tả:** Chưa có đánh giá phone detection trên untouched holdout độc lập chưa dùng trong training/tuning.

- **D-03 — Head-Turning Ground-Truth Event Evaluation**
  - **Status:** `OPEN`
  - **Mô tả:** Chưa có ground-truth event dataset đủ để công bố precision/recall cấp sự kiện.

### 2. Residual Risks (Rủi ro dư lượng ghi nhận riêng biệt):

- **Residual Risk 1 — Compatibility value 2.0 có thể được hiểu là legacy 2%:**
  - *Mô tả:* Compatibility contract hiện tại áp dụng quy tắc: [0, 1] canonical; (1, 100] compatibility input được chia 100; âm, >100, NaN và Inf bị từ chối; residual risk: 2.0 có thể được hiểu là legacy 2% = 0.02. Không tự thay đổi contract khi chưa có phê duyệt riêng. Sprint 3.3 chỉ dành cho Dual USB Hardware Acceptance.

- **Residual Risk 2 — Benchmark Synthetic + Stub Detector:**
  - *Mô tả:* Benchmark synthetic + stub detector; không dùng để tuyên bố tốc độ mô hình AI thật.

- **Residual Risk 3 — Hardware Acceptance Pending:**
  - *Mô tả:* Hardware acceptance pending; đã đặt mua 2 webcam EYD PC02, chờ nhận thiết bị và kiểm thử đồng thời trên 2 cổng USB độc lập.

- **Residual Risk 4 — RAM/Camera thật chưa được đánh giá:**
  - *Mô tả:* RAM/camera thật chưa được đánh giá trên máy trạm vật lý trong điều kiện thi thực tế.

---

## K. TRẠNG THÁI BÀN GIAO VÀ PHẠM VI NGHIỆM THU

- **Verdict ứng viên:** `CANDIDATE VERDICT: PASS WITH RESIDUAL RISKS — SOFTWARE/SYNTHETIC ACCEPTANCE`.
- **Trạng thái phê duyệt PM:** `FINAL PM VERDICT: PENDING INDEPENDENT ARTIFACT AUDIT`.
- **Giới hạn phạm vi (Không tự cấp final verdict):** Không tuyên bố production-ready, hardware accepted, model accuracy accepted hoặc dataset blockers đã đóng.
- **Blocker Register:** D-01 (`PENDING_HANDOFF_IMPORT`), D-02 (`OPEN`), D-03 (`OPEN`) được phân định độc lập và giữ nguyên trạng thái.
- **Rủi ro dư lượng:** 4 residual risks được theo dõi riêng biệt (compatibility value 2.0; benchmark synthetic + stub detector; hardware acceptance pending; RAM/camera thật chưa đánh giá trên môi trường thi thực tế).
- **Phân định kết quả kiểm thử:**
  - Acceptance: 15 PASS, 1 NOT_CONFIGURED, 0 FAIL.
  - Packaging/validation: SUCCESS.
- **Cấu trúc số lượng tệp trong ZIP (ZIP Cardinality):**
  - Tổng số tệp trong ZIP: 38 tệp.
  - 37 payload files được manifest quản lý; sha256_manifest.txt là control file được miễn tự liệt kê.
  - Đúng 1 ngoại lệ control file cho phép; 0 tệp ngoài danh sách.
- **Bảo toàn CSDL chính:** Trong phạm vi exists, size, mtime_ns, ctime_ns và SHA-256 được Production DB Guard theo dõi, không ghi nhận khác biệt giữa baseline và final checkpoint (SHA-256, kích thước, timestamp bảo toàn; không checkpoint, không truncate, không restore lên CSDL chính).
- **Git & Model:** Git không ghi nhận thay đổi trong model/ tại thời điểm kiểm tra; Runner không thực hiện commit, tag hoặc push.
