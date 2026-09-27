# Hoàng Văn Thụ AI Proctoring – Asset Pack

Bộ ZIP này gồm các asset/component đã tách từ reference và một số SVG sạch để agent dùng trực tiếp.

## Cấu trúc
- 01_branding: ribbon, logo, header lockup
- 02_patterns: pattern trống đồng + ribbon/divider SVG
- 03_footer: line-art trường, slogan, divider/name
- 04_controls: nút, selector, status cards
- 05_badges: detection/severity/status badge
- 06_camera_cards: 3 trạng thái camera hoàn chỉnh
- 07_incident_cards: card sự cố đỏ/vàng
- 08_reference: ảnh gốc + asset-board
- layout-spec.json: kích thước, tọa độ, màu, ghi chú triển khai

## Cách dùng cho agent
1. Dùng `08_reference/original-dashboard-reference.png` làm visual source of truth.
2. Dùng component PNG để đối chiếu pixel/layout.
3. Ưu tiên recreate UI bằng HTML/CSS/React; không nhúng card PNG làm UI thật.
4. Dùng SVG ở `02_patterns` cho các decorative elements có thể scale.
5. Pattern trống đồng chỉ ở opacity thấp 8–15%, nằm dưới content.
6. Logo trường trong pack là reference crop; nếu có logo gốc chất lượng cao thì thay bằng file chính thức.
