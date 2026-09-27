# TÀI LIỆU ĐẶC TẢ BỐ CỤC GIAO DIỆN GỐC (ORIGINAL UI LAYOUT SPECIFICATION)
## DÀNH CHO AI THIẾT KẾ (DESIGN AI / UI GENERATOR AGENTS)

> **Mục đích tài liệu:**  
> Bản đặc tả này ghi lại toàn bộ **bố cục, cấu trúc thành phần, phân cấp visual, bảng màu và luồng tương tác của giao diện GỐC (ExamVision AI / Edge Proctor Workstation)** trước khi áp dụng bất kỳ nhận diện trường học nào (như Chuyên Hoàng Văn Thụ).  
> Tài liệu này được cấu trúc theo chuẩn kỹ thuật để AI thiết kế (Design AI) có thể đọc hiểu 100%, tái tạo (recreate), tạo mockups, hoặc phát triển các theme mới mà không làm mất đi các nguyên tắc cốt lõi của hệ thống giám thị phòng thi AI.

---

## 1. TRIẾT LÝ THIẾT KẾ CỐT LÕI (DESIGN PHILOSOPHY & ANTI-SLOP)

Hệ thống giao diện gốc tuân thủ nghiêm ngặt **Quy chuẩn Senior Enterprise UI/UX Designer & Anti-Slop Guidelines** (`oloflun/anti-slop-design`):

1. **Không Sci-Fi / Cyberpunk Tropes:**
   - Tuyệt đối không dùng màu tím phát sáng (neon purple/magenta), không hiệu ứng viền neon, không bóng đổ lòe loẹt.
   - Không lạm dụng hiệu ứng kính mờ (glassmorphism blur) hay card trong suốt lơ lửng gây rối mắt giám thị.
   - Không bo góc quá lớn (chỉ dùng bo góc sắc nét 6px – 8px: `rounded-md` / `rounded-lg`).
2. **Mật độ dữ liệu cao (High Data Density):**
   - Tận dụng tối đa không gian màn hình, đường viền mảnh 1px (`border-zinc-800`), giảm bớt khoảng trắng (padding/margin) thừa thãi.
   - Phù hợp với màn hình giám sát thi thực tế của giám thị (proctor workstation).
3. **Thực tế phòng thi trực tiếp (Physical Exam Reality):**
   - Mọi thông số, nhãn dán, khung nhận diện phản ánh đúng bối cảnh: bàn thi gỗ, giấy thi, camera góc cao/góc trước, tư thế cúi/quay đầu, điện thoại di động cầm tay.
4. **Phân cấp màu sắc chức năng nghiêm ngặt:**
   - **Nền chủ đạo:** Neutral Charcoal / Slate (`#09090b` - `bg-zinc-950`, `#18181b` - `bg-zinc-900`).
   - **Xanh lục (Emerald - `#10b981`):** Trạng thái Bình thường / Hệ thống sẵn sàng / Đã duyệt vi phạm.
   - **Vàng cam (Amber - `#f59e0b`):** Trạng thái Nghi vấn / Cờ vàng / Chú ý.
   - **Đỏ hồng (Rose/Red - `#f43f5e` / `#ef4444`):** Cờ đỏ / Vi phạm nghiêm trọng (dùng điện thoại, đổi chỗ).

---

## 2. BẢNG MÃ MÀU & DESIGN TOKENS (DESIGN TOKENS)

| Thành phần | Mã Màu Hex | Tailwind Class | Vai trò trong giao diện |
| :--- | :--- | :--- | :--- |
| **Canvas Background** | `#09090b` | `bg-zinc-950` | Nền tổng thể toàn trang web |
| **Panel Surface** | `#18181b` | `bg-zinc-900` | Nền thanh Topbar, Sidebar sự cố, Card chứa camera |
| **Card Surface** | `#27272a` / `#18181b` | `bg-zinc-900` / `bg-zinc-950` | Nền của từng thẻ vi phạm (`IncidentCard`) |
| **Structural Border** | `#27272a` | `border-zinc-800` | Đường phân cách 1px giữa các cột, thanh công cụ, viền card |
| **Subtle Border** | `#3f3f46` | `border-zinc-700` | Viền nút bấm, dropdown, thẻ trạng thái active |
| **Primary Text** | `#f4f4f5` | `text-zinc-100` | Tiêu đề, số liệu chính, nhãn thẻ |
| **Secondary Text** | `#a1a1aa` | `text-zinc-400` | Ghi chú phụ, đơn vị đo, nhãn tham số |
| **Muted Text** | `#71717a` | `text-zinc-500` | Nhãn trạng thái offline, văn bản placeholder |
| **Status Normal** | `#10b981` | `text-emerald-400` | Chấm báo online, cờ bình thường, tick xanh đã duyệt |
| **Status Normal Bg** | `#022c22` | `bg-emerald-950/40` | Nền huy hiệu trạng thái bình thường |
| **Status Warning** | `#f59e0b` | `text-amber-400` | Cờ vàng, cảnh báo quay đầu, rủi ro vừa |
| **Status Warning Bg** | `#451a03` | `bg-amber-950/40` | Nền huy hiệu cờ vàng, viền cảnh báo nghi vấn |
| **Status Critical** | `#ef4444` | `text-rose-400` | Cờ đỏ, vi phạm điện thoại, nút xóa tệp |
| **Status Critical Bg** | `#4c0519` | `bg-rose-950/40` | Nền huy hiệu cờ đỏ, viền thẻ vi phạm khẩn |

### Quy chuẩn Typography:
- **Font giao diện (UI Text):** `Inter`, `sans-serif` (13px – 14px regular/medium, tiêu đề 14px – 16px semibold).
- **Font số liệu / Telemetry:** `JetBrains Mono`, `font-mono` (10px – 12px) dùng cho: FPS, độ trễ `ms`, tỉ lệ `%`, Track ID, mã thời gian UTC, timestamp.

---

## 3. SƠ ĐỒ KHUNG DÂY TỔNG THỂ (MASTER WIREFRAME LAYOUT)

Màn hình chia làm **2 khối chính theo chiều dọc**, trong đó thân trang chia làm **2 cột theo tỷ lệ ~70% : 30%**:

```
+-----------------------------------------------------------------------------------------------------------------+
| [HEADER - TOP NAVIGATION BAR] (Chiều cao cố định 56px / h-14)                                                  |
| Logo + Tên App ("ExamVision AI") | Nguồn Camera          Thời gian thực UTC | Trạng thái AI | Cấu hình | Fullscreen|
+-----------------------------------------------------------------------------------------------------------------+
| [MAIN WORKSPACE] (flex-1 overflow-hidden, Padding: 12px, Gap: 12px)                                              |
|                                                                                                                 |
| +-------------------------------------------------------------+ +---------------------------------------------+ |
| | CỘT TRÁI (70% - 75%): LIVE CAMERA VIEWPORT & TELEMETRY       | | CỘT PHẢI (25% - 30% / 380px):              | |
| |                                                             | | INCIDENT FEED & EVIDENCE CLIPS              | |
| | +---------------------------------------------------------+ | | +-----------------------------------------+ | |
| | | 1. TOOLBAR GIÁM SÁT & TELEMETRY (h-11)                  | | | | TIÊU ĐỀ SỰ CỐ VI PHẠM (Số lượng)   | Nút Ref | | |
| | | [FPS: 15] [Trễ: 42ms] [Drop: 0] [Trạng thái AI]   [Menu] | | | +-----------------------------------------+ | |
| | +---------------------------------------------------------+ | | | DANH SÁCH CUỘN CÁC THẺ VI PHẠM (Cards):  | | |
| | |                                                         | | | | +-------------------------------------+ | | |
| | | 2. KHUNG PHÁT VIDEO CHÍNH (Tỉ lệ 16:9, background đen)  | | | | | [Cờ Đỏ] PHONE • 14:20:15 UTC        | | |
| | |                                                         | | | | | [Ảnh Snapshot Bằng Chứng] (Play Icon)| | |
| | |    +----------------------------------+                 | | | | | Track 10 • Tin cậy: 95.0%            | | |
| | |    | [BBOX: PHONE (95%)]              |                 | | | | | [Xem Clip] [Bỏ qua (X)] [Duyệt (V)]  | | |
| | |    +----------------------------------+                 | | | | +-------------------------------------+ | | |
| | |                                                         | | | | +-------------------------------------+ | | |
| | |                                                         | | | | | [Cờ Vàng] QUAY ĐẦU • 14:19:02 UTC    | | |
| | |                                                         | | | | | [Ảnh Snapshot Bằng Chứng] (Play Icon)| | |
| | |                                                         | | | | | Track 20 • Tin cậy: 88.5%            | | |
| | |                                                         | | | | | [Xem Clip] [Bỏ qua (X)] [Duyệt (V)]  | | |
| | +---------------------------------------------------------+ | | | +-------------------------------------+ | | |
| | | 3. DẢI TRẠNG THÁI STREAM DƯỚI (Floating Bottom Strip)   | | | | (Cuộn vô hạn nếu có nhiều sự cố...)    | | |
| | | [Nút Tạm Dừng/Bật AI] | Trạng thái | RingBuffer: 15 FPS | | | |                                         | | |
| | +---------------------------------------------------------+ | | +-----------------------------------------+ | |
| +-------------------------------------------------------------+ +---------------------------------------------+ |
+-----------------------------------------------------------------------------------------------------------------+
```

---

## 4. CHI TIẾT CÁC THÀNH PHẦN (COMPONENT BREAKDOWN)

### 4.1. Thanh điều hướng trên cùng (`TopNavBar`)
- **Vị trí:** `sticky top-0`, `h-14` (56px), `bg-zinc-950/95`, viền đáy `border-b border-zinc-800`.
- **Cấu trúc bên trái:**
  - Icon khiên bảo mật (`ShieldCheck`) nền xám đậm `bg-zinc-900 border-zinc-700`.
  - Tiêu đề ứng dụng: `ExamVision AI` (Font Mono, bold, trắng).
  - Badge công nghệ: `EDGE PROCTOR` (`bg-zinc-800 text-zinc-300 border-zinc-700 text-[9px]`).
  - Nguồn giám sát đang chọn: `Nguồn: Webcam máy trạm` (text xám mờ).
- **Cấu trúc bên phải:**
  - Đồng hồ thời gian thực: Giờ:Phút:Giây kèm đuôi `UTC`, icon `Clock`, font Mono.
  - Badge trạng thái AI:
    - Sẵn sàng: Chấm xanh nhấp nháy, chữ `AI SẴN SÀNG` (`bg-emerald-950/40 text-emerald-400 border-emerald-800`).
    - Chờ: Chấm vàng, chữ `AI STANDBY` (`bg-amber-950/40 text-amber-400 border-amber-800`).
  - Nút chuyển chế độ xem: `Cấu Hình AI` (Icon sliders) -> Mở trang cài đặt độ nhạy.
  - Nút Toàn màn hình (`Maximize2` / `Minimize2`).

---

### 4.2. Khung giám sát Video bên trái (`Monitoring Area`)
Chiếm từ **70% đến 75% chiều rộng**, gồm 3 tầng hiển thị:

#### Tầng 1: Thanh Telemetry & Công cụ trên (`MonitoringToolbar`)
- **Chiều cao:** `h-11` (44px), `bg-zinc-900 border-b border-zinc-800`.
- **Các badge hiển thị bên trái:**
  - `FPS Badge:` Số FPS thu nhận thực tế (Ví dụ: `15.0 FPS (32ms)`).
  - `Drop Badge (nếu > 0):` Báo số frame bị nghẽn (`Drop: 2`).
  - `Superseded Badge:` Báo số frame bị ghi đè khi AI đang tính toán (`Superseded: 12`).
  - `Huy hiệu Trạng thái Vi phạm Tức thì (Live Alert Level):`
    - Xanh: `BÌNH THƯỜNG` (Icon ShieldCheck)
    - Vàng: `NGHI VẤN (CỜ VÀNG)` (Icon AlertTriangle)
    - Đỏ: `VI PHẠM (CỜ ĐỎ)` (Icon ShieldAlert)
- **Các nút chức năng bên phải:**
  - Nút chuyển nguồn video: `Dùng Webcam` / `Nạp Video Demo` (hỗ trợ chọn file `.mp4`).
  - Nút bật/tắt khung AI: `Khung AI: BẬT / TẮT` (Icon Eye / EyeOff).

#### Tầng 2: Màn hình Video & Lớp Bounding Box AI
- Container: Tỉ lệ 16:9 (`aspect-video`), nền đen thuần (`bg-black`), phần tử `<video>` đặt `object-contain`.
- **Lớp phủ nhận diện AI (Bounding Box Layer):**
  - Đặt `absolute inset-0 pointer-events-none`.
  - Tọa độ khung được tính toán chính xác theo `%` (`left`, `top`, `width`, `height`).
  - **Màu khung viền:**
    - Cờ đỏ (Điện thoại): Viền `border-rose-500`, nền `bg-rose-500/10`.
    - Cờ vàng (Quay đầu / Tư thế lạ): Viền `border-amber-400`, nền `bg-amber-400/10`.
    - Bình thường (Người ngồi thi): Viền `border-emerald-500/80`, nền `bg-emerald-500/5`.
  - **Nhãn dán trên góc khung:** Huy hiệu nhỏ ở góc trên bên trái `text-[10px] font-mono text-white`:
    - Ví dụ: `Dùng điện thoại (95.4%)` hoặc `Quay đầu 35° (88.0%)`.

#### Tầng 3: Dải trạng thái Stream bên dưới (Bottom Strip)
- Thanh nổi bán trong suốt nằm sát mép dưới video: `bg-zinc-950/90 border border-zinc-800 text-[11px] font-mono`.
- Nút bấm nhanh: `Tạm Dừng AI` / `Bật Giám Sát` (Icon Play/Pause).
- Trạng thái luồng: `Đang phân tích` (xanh) hoặc `Tạm ngừng` (xám).
- Thông số kỹ thuật bộ đệm: `RingBuffer: 15 FPS Realtime (Pre 5.0s / Post 10.0s)`.

---

### 4.3. Cột danh sách vi phạm bên phải (`IncidentSidebar`)
Chiếm từ **25% đến 30% chiều rộng** (cố định tối thiểu 360px – 380px trên Desktop):

#### Header của Sidebar:
- Tiêu đề: `SỰ CỐ VI PHẠM (N)` kèm icon cuộn phim `Film`.
- Nút `Làm mới (Refresh)` kèm hiệu ứng xoay khi đang polling dữ liệu.
- Nút `Dọn sạch video (Purge All)` (icon thùng rác đỏ nhạt).

#### Danh sách cuộn các thẻ sự cố (`IncidentCard`):
Mỗi sự cố được thể hiện như một thẻ thẻ điều hành (Ops Card) độc lập:
1. **Header thẻ:**
   - Badge mức độ: `Cờ Đỏ • Dùng Điện Thoại` (`bg-rose-950 border-rose-800 text-rose-300`) hoặc `Cờ Vàng • Quay Đầu` (`bg-amber-950 border-amber-800 text-amber-300`).
   - Thời gian ghi nhận: `14:20:15 UTC` (Font Mono).
2. **Khu vực xem trước (Thumbnail / Snapshot):**
   - Ảnh chụp đúng thời điểm vi phạm (`aspect-video`, `bg-black`, bo góc).
   - Nút Play tròn bán trong suốt ở chính giữa: Khi rê chuột vào, nút nổi bật lên mời giám thị bấm vào để phát lại clip.
   - Nhãn góc dưới: `Clip MP4` (Font Mono 9px).
3. **Chân thẻ (Footer & Hành động của Giám thị):**
   - Thông số: `Track ID • Điểm tin cậy (VD: Track 12 | 96.2%)`.
   - Bộ 3 nút thao tác:
     - Nút `Xem Clip`: Mở modal phát lại video MP4.
     - Nút `Bỏ qua (X)`: Đánh dấu sự cố là false positive (`status: dismissed`).
     - Nút `Duyệt (✓)`: Xác nhận thí sinh vi phạm biên bản (`status: confirmed`).
     - Nút `Xóa (Trash2)`: Xóa vĩnh viễn tệp video khỏi máy chủ/ổ cứng.

---

### 4.4. Cửa sổ phát video bằng chứng (`VideoEvidenceModal`)
- **Loại modal:** Overlay chính giữa màn hình `fixed inset-0 z-50 bg-black/80 backdrop-blur-sm`.
- **Hộp thoại chính:** `w-full max-w-2xl bg-zinc-900 border border-zinc-800 rounded-lg p-4`.
- **Nội dung:**
  1. Header: Tiêu đề in hoa `CLIP BẰNG CHỨNG TỰ ĐỘNG: [TÊN VI PHẠM]`, mã sự cố UUID, nút đóng `X`.
  2. Video Player: Trình phát video chuẩn HTML5, tự động phát (`autoPlay`), hỗ trợ lặp (`loop`), nguồn tệp trực tiếp từ endpoint backend `/evidence/{id}.mp4`.
  3. Bảng tóm tắt thông số vi phạm:
     - Mức độ cảnh báo (Chấm màu Đỏ / Vàng).
     - Điểm tin cậy AI (%).
     - Thời điểm phát hiện (giờ UTC).
     - Nguồn camera ghi nhận.
     - Ghi chú thuật toán trích xuất RingBuffer.
  4. Footer Modal:
     - Nút bật/tắt lặp clip (`Lặp video: BẬT / TẮT`).
     - Nút `Xóa video sự cố` (màu đỏ cảnh báo, yêu cầu xác nhận trước khi xóa tệp vật lý).
     - Nút `Đóng`.

---

### 4.5. Màn hình cấu hình độ nhạy AI (`AISettingsView`)
Khi giám thị bấm vào nút "Cấu Hình AI" trên TopNavBar, toàn bộ vùng `main` chuyển sang chế độ xem cấu hình:
- **Thanh tiêu đề phụ:** Nút quay lại `← Quay Lại Giám Sát` và nhãn `CẤU HÌNH ĐỘ NHẠY & THAM SỐ GHI BẰNG CHỨNG AI`.
- **Form điều khiển gồm các thanh trượt (Sliders) kỹ thuật:**
  1. *Ngưỡng phát hiện điện thoại (Phone Confidence):* Mặc định `0.55` (dải `0.30 - 0.90`).
  2. *Thời gian quay đầu phát cảnh báo (Posture Alert Seconds):* Mặc định `1.25s` (dải `0.5s - 5.0s`).
  3. *Ngưỡng nghi vấn hành vi (Suspicion Threshold):* Mặc định `0.50`.
  4. *Thời lượng ghi hình trước sự cố (Pre-roll seconds):* Mặc định `5.0s`.
  5. *Thời lượng ghi hình sau sự cố (Post-roll seconds):* Mặc định `10.0s`.
  6. *Thời gian nghỉ giữa 2 lần kích hoạt (Cooldown seconds):* Mặc định `6.0s`.
- Nút lưu cấu hình: `Lưu Cấu Hình` (đồng bộ trực tiếp vào SQLite và gửi tín hiệu cập nhật RingBuffer ngay lập tức).

---

## 5. CÂY CẤU TRÚC COMPONENT (REACT DOM TREE)

Dành cho AI thiết kế khi dựng mã nguồn hoặc phân tích logic DOM:

```jsx
<App> (bg-zinc-950 text-zinc-100 flex-col h-screen)
│
├── <TopNavBar /> (h-14 bg-zinc-950/95 border-b border-zinc-800)
│    ├── BrandLockup (ShieldCheck + "ExamVision AI" + "EDGE PROCTOR")
│    ├── SourceInfo ("Nguồn: Webcam máy trạm")
│    ├── ClockDisplay (Giờ UTC, font-mono)
│    ├── AIStatusBadge ("AI SẴN SÀNG" / "AI STANDBY")
│    ├── ViewToggleBtn ("Cấu Hình AI")
│    └── FullscreenBtn
│
├── <main> (flex-1 flex overflow-hidden p-3 gap-3)
│    │
│    ├── [IF view === 'live-monitor']
│    │   └── <StreamlinedProctorDashboard />
│    │        ├── LeftColumn: VideoViewportContainer (flex-1 bg-zinc-900 border border-zinc-800)
│    │        │    ├── <MonitoringToolbar /> (FPS, Latency, Drop, Status Badge, Toggle Box, Source Switch)
│    │        │    ├── VideoSurface (relative flex-1 bg-black)
│    │        │    │    ├── <video ref={videoRef} />
│    │        │    │    └── DetectionOverlay (Absolute Bounding Boxes + Tag labels)
│    │        │    └── VideoStatusBar (Bottom floating strip: Pause/Play, RingBuffer metrics)
│    │        │
│    │        └── RightColumn: <IncidentSidebar /> (w-[380px] bg-zinc-900 border border-zinc-800)
│    │             ├── SidebarHeader ("SỰ CỐ VI PHẠM (N)", RefreshBtn, PurgeAllBtn)
│    │             └── ScrollableList (divide-y-0 space-y-2.5)
│    │                  └── <IncidentCard /> (Repeated map)
│    │                       ├── CardHeader (Level badge, timestamp)
│    │                       ├── ThumbnailContainer (img, overlay play icon, clip badge)
│    │                       └── CardFooter (Track ID, confidence, action buttons: View, Dismiss, Confirm, Delete)
│    │
│    └── [IF view === 'ai-settings']
│        └── <AISettingsView /> (Form sliders, Save button)
│
├── <ToastNotification /> (fixed top-16 right-6, animated status pill)
│
└── <VideoEvidenceModal /> (fixed inset-0 z-50 backdrop-blur)
     ├── ModalHeader (Title, Incident ID, CloseBtn)
     ├── HTML5VideoPlayer (src=/evidence/{id}.mp4, loop, controls)
     ├── IncidentMetadataBox (confidence, timestamp, source, proctor notes)
     └── ModalFooter (ToggleLoop, DeleteVideoBtn, CloseBtn)
```

---

## 6. HƯỚNG DẪN PROMPT CHO AI THIẾT KẾ (DESIGN AI PROMPTING CHEATSHEET)

Nếu bạn đưa tài liệu này cho một mô hình sinh giao diện AI (như Claude 3.7 Sonnet, v0.dev, Midjourney UI, Cursor Agent):

### System Prompt gợi ý:
> *"Bạn là chuyên gia thiết kế giao diện doanh nghiệp cao cấp (Senior Enterprise UI/UX Designer) theo phong cách Industrial Utility & Anti-Slop. Hãy tạo giao diện giám sát thi bằng AI dựa trên tài liệu ORIGINAL_UI_LAYOUT_SPEC.md. Tông màu chủ đạo là Charcoal / Slate (`#09090b` và `#18181b`), viền sắc nét 1px `border-zinc-800`, font chữ Inter kết hợp JetBrains Mono cho số liệu. Màn hình chia tỉ lệ 70:30 với khung camera video AI ở bên trái và danh sách sự cố bằng chứng ở bên phải. Tuyệt đối không dùng phong cách Cyberpunk, không có hiệu ứng phát sáng neon tím, không dùng bo góc tròn trịa 24px."*

### Các từ khóa thẩm mỹ bắt buộc (Mandatory Keywords):
- `dark mode enterprise dashboard`
- `high data density proctoring station`
- `neutral charcoal zinc-950 canvas`
- `subtle 1px zinc-800 borders`
- `clean status indicators (emerald green, amber warning, rose critical)`
- `technical monospace telemetry readouts`
- `no cyberpunk glows, no gradient borders, no decorative emojis`
