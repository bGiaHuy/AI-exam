# Tân Lập AI Proctoring UI Components

Bộ này được tạo từ phương án UI đã chọn.

## Thư mục
- `01_branding`: logo gốc + brand lockup reference
- `02_header`: header full-width reference
- `03_sidebar`: navigation sidebar
- `04_controls`: top status / toolbar / camera selector / upload / toggle
- `05_status`: system status + user menu
- `06_camera_cards`: violation / normal / offline
- `07_incident_cards`: critical / warning / info
- `08_badges_icons`: badges + icon reference
- `09_table`: bảng danh sách thí sinh
- `10_patterns`: SVG decorative scalable
- `11_reference`: full component board

## Quy tắc cho coding agent
1. PNG chỉ dùng làm visual source of truth, không ghép screenshot thành UI.
2. Recreate bằng React/HTML/CSS/Tailwind theo stack hiện tại.
3. Giữ nguyên business logic, camera pipeline, API, incident data, FPS thật.
4. Bounding box AI phải là overlay thật.
5. Pattern/watermark dùng opacity thấp 6-12%.
6. Bố cục desktop ưu tiên: sidebar trái + vùng camera trung tâm + incident sidebar phải.
