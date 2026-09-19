# MỤC LỤC VÀ ĐỐI SOÁT ARTIFACT BẰNG CHỨNG THỰC NGHIỆM THÔ (RUNTIME ARTIFACT INDEX)
## DỰ ÁN: AI-POWERED AUTOMATED PROCTORING SYSTEM (AI EXAM CONTROL)
**Mã tài liệu:** `RPT-ARTIFACT-INDEX-V4.0B`  
**Thời điểm khởi tạo:** 2026-09-14T13:10:46+00:00  
**Thư mục lưu trữ:** `reports/evidence/report_runtime/`  
**Trạng thái kiểm tra:** ĐÃ ĐỐI SOÁT TOÀN VẸN (ALL ARTIFACTS VERIFIED)  

---

## 1. BẢNG DANH MỤC TỆP BẰNG CHỨNG THỰC NGHIỆM THÔ (RAW RUNTIME ARTIFACTS)

| Tên tệp | Kích thước (Bytes) | Mã băm SHA-256 | Lệnh sinh dữ liệu | Trạng thái |
|---|---|---|---|:---:|
| `e2e_benchmark_result.json` | 662 | `88c4ee7fd7a10548037a7612e8ea463c6f2b0ab83e459854550ce59e04106858` | `Node.js/Playwright/Python WebSocket E2E benchmark script (125.1s live session telemetry capture)` | `VERIFIED` |
| `COMMAND_RESULTS.json` | 3,334 | `29f5ddfeaed511eaa56a44d8ef456d173781ddbdee827a2adec62867bbe2a6ec` | `scripts/record_commands.py (Structured execution trace of 6 verification commands)` | `VERIFIED` |
| `test_backend_output.txt` | 52,474 | `1ce9099ce30e6bbb3dc6b8610339357f4452fe1812d1fc602e3a8c7f0b803924` | `.venv\Scripts\python.exe -m unittest backend.tests.test_refactored_system` | `VERIFIED` |
| `test_harness_output.txt` | 126 | `5a7f4677f28a22228f1ad25eeb31a6c51d769d02da7fefef16934cce235ce0a0` | `.venv\Scripts\python.exe -m unittest scripts.evaluation.tests.test_evaluation_harness` | `VERIFIED` |
| `tsc_output.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `npx tsc --noEmit` | `VERIFIED` |
| `build_output.txt` | 576 | `dfe9e1d11ecf5a15349396df10d7884f1c139e0d1d940a8cae14cb44a4883fbd` | `npm run build` | `VERIFIED` |
| `verify_lineage_output.txt` | 1,690 | `d5b2b613fc75960549eadd07839a22de72bfcd167ab2156a84c736e8954fb256` | `.venv\Scripts\python.exe scripts/verify_training_lineage_handoff.py` | `VERIFIED` |
| `verify_consistency_output.txt` | 7,323 | `135f1090101605d422a3f6f69c4efdbacf1fe9f3fcdbb0155c05468305bbdd57` | `.venv\Scripts\python.exe scripts/verify_report_consistency.py` | `VERIFIED` |

---

## 2. CHI TIẾT NGUỒN GỐC VÀ MỤC ĐÍCH TỪNG TỆP BẰNG CHỨNG

### 2.1. `e2e_benchmark_result.json`
- **Kích thước:** 662 bytes
- **Mã băm SHA-256:** `88c4ee7fd7a10548037a7612e8ea463c6f2b0ab83e459854550ce59e04106858`
- **Lệnh thực thi:** `Node.js/Playwright/Python WebSocket E2E benchmark script (125.1s live session telemetry capture)`
- **Thời điểm sinh:** `2026-09-14T02:10:50+00:00`
- **Nguồn dữ liệu:** Live WebSocket E2E streaming benchmark against local FastAPI server and React client
- **Mục đích & Ý nghĩa đối soát:** Raw telemetry logs measuring 125.1s stream, frame counts (1952 captured/sent, 1949 received, 0 dropped at transport, 1662 superseded at single-slot buffer, 354 results, 2.77 CPU FPS, 360.4ms latency)

### 2.2. `COMMAND_RESULTS.json`
- **Kích thước:** 3,334 bytes
- **Mã băm SHA-256:** `29f5ddfeaed511eaa56a44d8ef456d173781ddbdee827a2adec62867bbe2a6ec`
- **Lệnh thực thi:** `scripts/record_commands.py`
- **Thời điểm sinh:** `2026-09-14T13:10:46+00:00`
- **Nguồn dữ liệu:** Python automated process runner with UTC timestamps, duration, exit codes, and output artifact hashes
- **Mục đích & Ý nghĩa đối soát:** Machine-readable audit ledger recording execution results for all 6 core verification commands (all 6 PASS, exit code 0)

### 2.3. `test_backend_output.txt`
- **Kích thước:** 52,474 bytes
- **Mã băm SHA-256:** `1ce9099ce30e6bbb3dc6b8610339357f4452fe1812d1fc602e3a8c7f0b803924`
- **Lệnh thực thi:** `.venv\Scripts\python.exe -m unittest backend.tests.test_refactored_system`
- **Thời điểm sinh:** `2026-09-14T13:10:39+00:00`
- **Nguồn dữ liệu:** Local Python 3.12 unittest runner on backend refactored test suite
- **Mục đích & Ý nghĩa đối soát:** Execution log proving 31/31 backend tests passed (Ran 31 tests, OK)

### 2.4. `test_harness_output.txt`
- **Kích thước:** 126 bytes
- **Mã băm SHA-256:** `5a7f4677f28a22228f1ad25eeb31a6c51d769d02da7fefef16934cce235ce0a0`
- **Lệnh thực thi:** `.venv\Scripts\python.exe -m unittest scripts.evaluation.tests.test_evaluation_harness`
- **Thời điểm sinh:** `2026-09-14T13:10:41+00:00`
- **Nguồn dữ liệu:** Local Python 3.12 unittest runner on evaluation harness test suite
- **Mục đích & Ý nghĩa đối soát:** Execution log proving 22/22 evaluation harness tests passed (Ran 22 tests, OK)

### 2.5. `tsc_output.txt`
- **Kích thước:** 0 bytes
- **Mã băm SHA-256:** `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- **Lệnh thực thi:** `npx tsc --noEmit`
- **Thời điểm sinh:** `2026-09-14T13:10:43+00:00`
- **Nguồn dữ liệu:** TypeScript 5 compiler (strict type checking)
- **Mục đích & Ý nghĩa đối soát:** Zero-output log confirming exit code 0 and 0 type errors across frontend codebase

### 2.6. `build_output.txt`
- **Kích thước:** 576 bytes
- **Mã băm SHA-256:** `dfe9e1d11ecf5a15349396df10d7884f1c139e0d1d940a8cae14cb44a4883fbd`
- **Lệnh thực thi:** `npm run build`
- **Thời điểm sinh:** `2026-09-14T13:10:46+00:00`
- **Nguồn dữ liệu:** Vite 6 production bundler
- **Mục đích & Ý nghĩa đối soát:** Production build artifact log confirming clean bundling of client application

### 2.7. `verify_lineage_output.txt`
- **Kích thước:** 1,690 bytes
- **Mã băm SHA-256:** `d5b2b613fc75960549eadd07839a22de72bfcd167ab2156a84c736e8954fb256`
- **Lệnh thực thi:** `.venv\Scripts\python.exe scripts/verify_training_lineage_handoff.py`
- **Thời điểm sinh:** `2026-09-14T13:10:46+00:00`
- **Nguồn dữ liệu:** Training lineage verification script
- **Mục đích & Ý nghĩa đối soát:** Verification log confirming 10 canonical lineage files match PM-approved SHA-256 hashes

### 2.8. `verify_consistency_output.txt`
- **Kích thước:** 7,323 bytes
- **Mã băm SHA-256:** `135f1090101605d422a3f6f69c4efdbacf1fe9f3fcdbb0155c05468305bbdd57`
- **Lệnh thực thi:** `.venv\Scripts\python.exe scripts/verify_report_consistency.py`
- **Thời điểm sinh:** `2026-09-14T13:10:46+00:00`
- **Nguồn dữ liệu:** Sprint 4.0B report consistency checker
- **Mục đích & Ý nghĩa đối soát:** Verification log confirming all 6 report markdown files have 0 active forbidden claims

---
**KẾT THÚC MỤC LỤC ARTIFACT BẰNG CHỨNG THỰC NGHIỆM THÔ (RPT-ARTIFACT-INDEX-V4.0B)**

