# Anti-Slop Design & Engineering Rules

This project adheres strictly to the **Senior Enterprise UI/UX Designer & Anti-Slop Guidelines** (`oloflun/anti-slop-design`):

## 1. No Sci-Fi / Cyberpunk Tropes

- **No excessive dark purple or neon glows**.
- **No arbitrary glassmorphism blur** or floating transparent glow cards.
- **No gradient borders** or glowing neon drop-shadows.

## 2. High Data Density & Clean Layout

- Maximize screen utility with compact tables, dense lists, and crisp 1px borders (`border-zinc-800`).
- Remove bloated nested cards and unnecessary whitespace padding.
- Crisp border radiuses: 6px to 8px max on structural elements and cards (`rounded-lg` / `rounded-md`), avoiding oversized 24px+ round shapes on data tables and video monitors.

## 3. Restrained & Professional Typography

- **Strict Hierarchy**:
  - Title: 16–20px, semi-bold
  - Body: 13–14px, regular/medium
  - Mono / Telemetry: 11–12px (`JetBrains Mono`, `font-mono`)
- No random uppercase shouting words.
- Eliminate decorative emojis / icons preceding simple headers.

## 4. Production-Ready Functional Palette

- **Base Canvas**: Neutral Charcoal / Slate (`#09090b` / `bg-zinc-950`, `#18181b` / `bg-zinc-900`, `border-zinc-800`).
- **Accents**: Monochromatic neutrals for layout structure.
- **Strict Status Colors**:
  - `Emerald` (#10b981) for Normal / Verified / Active
  - `Amber` (#f59e0b) for Attention / Yellow Warning
  - `Rose / Red` (#f43f5e / #ef4444) for Flagged / Critical Alert

## 5. Physical Examination Reality

- All metrics, UI overlays, mock data, and violation labels strictly reflect **in-person paper exam proctoring** (overhead CCTV cameras, wooden desks, paper answer sheets, physical cheat sheets, head pose angles, handover gestures).

---

# Enterprise Fullstack & Architecture Rules

## 6. Offline-First & Zero-Cloud Mandate

- The system runs 100% locally on proctor workstation (localhost only).
- Do NOT import CDNs, remote fonts, or external telemetry scripts.
- Hardcoded base URL for local services: `http://localhost:8000/api`.

## 7. Database & Concurrency (SQLite 3 + WAL)

- Database file is `./cheating_system.db`.
- Always enforce WAL mode (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`) on every connection pool.
- NEVER invent mock data arrays in frontend or backend. All reads/writes must target SQLite via SQLAlchemy 2.0.
- Handle database sessions strictly with FastAPI `Depends(get_db)` to prevent dangling locks.

## 8. Backend Engineering Contract (FastAPI)

- All endpoints must declare explicit Pydantic response models (`response_model=...`).
- Enforce strict schemas for violations:
  - Violation types: `PHONE`, `HEAD_TURNING`, `LEFT_SEAT`
  - Severity levels: `yellow`, `red`
  - Incident status: `pending`, `confirmed`, `dismissed`
- File uploads (evidence clips `.mp4`, snapshots `.jpg`) must be stored in `./data/evidence/` and served statically via `/evidence`.

## 9. Frontend Integration Contract (React 19)

- All network calls must pass through a centralized API service layer (`src/services/api.ts`). Never write raw `fetch` directly inside UI components.
- State mutation rule: When an incident status is updated or confirmed, invalidate/re-fetch or update local state immutably; do not reload the whole window.
- Graceful fallbacks: If the backend is unreachable, display a compact offline status banner (`bg-zinc-900 border-rose-800 text-rose-300`), not a blank screen crash.

## 10. File Modification Discipline for Agent

- Work in small, verifiable slices. Never rewrite an entire component if only one function needs patching.
- Do NOT touch existing CSS classes unless explicitly requested.
- Verify imports before creating files: check if libraries (`lucide-react`, `clsx`, `tailwind-merge`, etc.) are already installed in `package.json`.

## 11. Structured Logging & Vibe Coding Observability (Bảo hiểm khi sinh mã tự động)

- **Nguyên tắc "Hộp kính" (Glass Box):** Tuyệt đối không để code AI thành hộp đen hay nuốt ngoại lệ (`try...except: pass`). Mọi luồng xử lý dữ liệu ngầm phải có log rõ ràng tại Terminal.
- **3 Điểm chốt chặn bắt buộc phải có log:**
  1. **Input Payload Trace:** Log tham số đầu vào khi endpoint nhận request (Query, Path, Request Body).
  2. **Logic Branching:** Log các điểm rẽ nhánh quan trọng (ví dụ: `AI phát hiện quay đầu > 1.25s -> Leo thang cờ ĐỎ`, `Điểm liêm chính trừ 25 -> Cập nhật DB`).
  3. **Exception with Traceback:** Khi phát sinh lỗi ngoại lệ, bắt buộc log kèm stack trace chi tiết (`logger.exception(...)` hoặc `traceback.format_exc()`), không trả về lỗi 500 chung chung thiếu bối cảnh.
- **Log chuẩn hóa đa tầng:**
  - Backend: Sử dụng thư viện `logging` chuẩn Python với format `[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s`.
  - Frontend: Sử dụng prefix rõ ràng `[API]`, `[LiveMonitor]`, `[RoomMatrix]` trong console để dễ dàng bắt lỗi đồng bộ.
- **Bảo mật:** Không in dữ liệu nhạy cảm thực tế (mật khẩu, khóa bí mật, CCCD đầy đủ) ra stdout trong môi trường sản xuất.

## 12. Strict Model Isolation Mandate (Quy tắc Bất khả xâm phạm Thư mục Model)

- **TUYỆT ĐỐI KHÔNG SỬA / KHÔNG ĐỤNG VÀO THƯ MỤC `model/`**:
  - Không sửa, không ghi đè, không tái cấu trúc bất kỳ file nào trong thư mục `model/`, bao gồm: `model/exam_analyzer.py`, `model/test_demo.py`, `model/api_server.py` và toàn bộ file weights trong `model/weights/` (`yolo11m-pose.pt`, `phone_detector_v5.pt`, v.v.).
  - Thuật toán AI, logic trích xuất tư thế, phát hiện gian lận và trọng số mô hình là phần của người dùng đã hoàn thiện, phải được giữ nguyên bản 100%.
  - Phạm vi công việc của trợ lý lập trình **chỉ giới hạn ở các phần xung quanh**:
    1. **Frontend UI**: React, giao diện giám sát, danh bạ, sơ đồ phòng, biên bản, modal phát video bằng chứng, components, v.v.
    2. **Backend API & Data**: FastAPI routers, kết nối CSDL SQLite, RingBuffer lưu clip, quản lý thí sinh/phòng thi/sự cố.

