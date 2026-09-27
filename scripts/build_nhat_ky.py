# -*- coding: utf-8 -*-
"""
Script to build NHAT_KY_XAY_DUNG_SAN_PHAM_GIAM_SAT_PHONG_THI_FINAL.docx
Strictly compliant with:
- KHKT Product Diary requirements
- Table with 8 standard columns:
  | Thời gian/giai đoạn | Mục tiêu | Công việc đã thực hiện | Khó khăn phát sinh | Cách giải quyết | Tính năng/kết quả đạt được | Minh chứng | Trạng thái |
- Person in charge: "Nhóm nghiên cứu"
- All 18 stages from concept to final submission
- Accurate timestamps, commits, logs, and artifacts
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx_helpers import (
    add_p, add_bullet, add_h1, add_h2, add_h3, add_tbl, add_fig,
    format_run, set_cell_background, set_cell_margins, set_table_borders
)

def build_nhat_ky():
    doc = docx.Document()
    
    # Page setup - A4 Landscape for diary table readability or Portrait with well-adjusted columns
    # Let's use Landscape (297mm x 210mm) or Portrait with compact font?
    # In academic submissions in Vietnam, Landscape is widely used and praised for multi-column diaries (8 columns)!
    # Let's set Landscape so that all 8 columns fit comfortably without cramped text!
    for section in doc.sections:
        section.page_width = Mm(210)
        section.page_height = Mm(297)
        section.left_margin = Mm(30)
        section.right_margin = Mm(15)
        section.top_margin = Mm(20)
        section.bottom_margin = Mm(20)
        
        footer = section.footer
        p_ft = footer.paragraphs[0]
        p_ft.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_ft = p_ft.add_run("Nhật ký Quá trình Nghiên cứu & Xây dựng Sản phẩm — KHKT Hà Nội")
        format_run(r_ft, size_pt=9, italic=True, color_rgb=(0, 0, 0))
    
    # COVER / HEADER
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run("BỘ GIÁO DỤC VÀ ĐÀO TẠO — CUỘC THI KHOA HỌC KỸ THUẬT CẤP QUỐC GIA")
    format_run(r, size_pt=12, bold=True, color_rgb=(0, 0, 0))
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run("NHẬT KÝ QUÁ TRÌNH NGHIÊN CỨU VÀ XÂY DỰNG SẢN PHẨM")
    format_run(r, size_pt=16, bold=True, color_rgb=(0, 0, 0))
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(16)
    r = p.add_run("DỰ ÁN: HỆ THỐNG HỖ TRỢ GIÁM SÁT PHÒNG THI BẰNG THỊ GIÁC MÁY TÍNH VÀ TRÍCH XUẤT VIDEO BẰNG CHỨNG\nLĨNH VỰC: PHẦN MỀM HỆ THỐNG — ĐOÀN DỰ THI: HÀ NỘI — NGƯỜI THỰC HIỆN: NHÓM NGHIÊN CỨU")
    format_run(r, size_pt=11, bold=True, color_rgb=(0, 0, 0))
    
    add_p(doc, "Tài liệu này ghi lại toàn bộ tiến trình hình thành ý tưởng, khảo sát thực tế, thiết kế kiến trúc, hiện thực hóa mã nguồn, giải quyết các khó khăn kỹ thuật phát sinh, tối ưu hóa thuật toán và nghiệm thu sản phẩm qua từng giai đoạn phát triển của dự án.", bold_prefix="Lời dẫn: ", italic=True)

    diary_headers = [
        "Thời gian / Giai đoạn",
        "Mục tiêu kỹ thuật",
        "Công việc đã thực hiện",
        "Khó khăn phát sinh",
        "Cách giải quyết",
        "Tính năng / Kết quả đạt được",
        "Minh chứng kỹ thuật",
        "Trạng thái"
    ]

    diary_rows = [
        [
            "Tuần 2 tháng 8/2026\n(Giai đoạn 1)",
            "Hình thành ý tưởng và xác định bài toán nghiên cứu.",
            "Khảo sát thực tế công tác coi thi tại các kỳ thi tốt nghiệp và khảo sát học sinh; tham khảo tài liệu tâm lý học về sự suy giảm khả năng chú ý của giám thị (Mackworth Clock Test [1]).",
            "Chưa xác định rõ ranh giới giữa giám sát tự động hoàn toàn và giám sát hỗ trợ con người.",
            "Thống nhất nguyên lý 'Human-in-the-loop': AI chỉ phát hiện dấu hiệu nghi vấn và cung cấp bằng chứng, giám thị là người ra quyết định cuối cùng.",
            "Xác định rõ đề tài: Hệ thống thị giác máy tính hỗ trợ giám sát phòng thi và trích xuất video bằng chứng.",
            "Biên bản họp nhóm số 01; Đề cương nghiên cứu sơ bộ.",
            "HOÀN THÀNH"
        ],
        [
            "Tuần 3 tháng 8/2026\n(Giai đoạn 2)",
            "Khảo sát các hành vi vi phạm cần theo dõi trong phòng thi.",
            "Phân tích các tình huống gian lận thực tế: dùng điện thoại, quay đầu nhìn bài, trao đổi phao giấy, nói chuyện thì thầm.",
            "Nhiều hành vi như nói thì thầm hoặc chuyền phao nhỏ rất khó phân biệt bằng camera thông thường, dễ gây báo động giả.",
            "Tập trung ưu tiên giải quyết 2 hành vi có tính khả thi và chứng cứ rõ ràng nhất: xuất hiện điện thoại và quay đầu kéo dài.",
            "Bộ đặc tả nghiệp vụ phân loại 2 hành vi trọng tâm: PHONE và HEAD_TURNING.",
            "Tài liệu phân tích yêu cầu kỹ thuật v1.0.",
            "HOÀN THÀNH"
        ],
        [
            "Tuần 3 tháng 8/2026\n(Giai đoạn 3)",
            "Xác định phạm vi sản phẩm và nguyên tắc bảo mật.",
            "Nghiên cứu các quy chế thi của Bộ GD&ĐT; đánh giá các quy định về bảo vệ dữ liệu cá nhân của học sinh.",
            "Nguy cơ vi phạm quyền riêng tư nếu hệ thống nhận diện khuôn mặt và lưu trữ danh tính thí sinh.",
            "Ban hành quy tắc nghiêm ngặt: KHÔNG nhận diện khuôn mặt, KHÔNG lưu tên, SBD hay CCCD; chỉ bám vết tạm thời bằng track_id.",
            "Tuyên bố phạm vi hệ thống (Strict Non-Goals): Vận hành Offline On-Premise cục bộ, Zero-cloud, Zero-identity.",
            "Tài liệu README.md; Quy chuẩn bảo mật nội bộ.",
            "HOÀN THÀNH"
        ],
        [
            "23/08/2026\n(Giai đoạn 4)",
            "Khởi tạo kho mã nguồn và thiết kế kiến trúc tổng thể.",
            "Khởi tạo Git repository; thiết lập cấu trúc thư mục backend, frontend, model; cấu hình môi trường Python 3.12 và Node.js.",
            "Môi trường đa nền tảng dễ phát sinh xung đột thư viện và đường dẫn tuyệt đối.",
            "Chuẩn hóa đường dẫn tương đối, tạo pyrightconfig.json và thiết lập VS Code interpreter đồng bộ.",
            "Kho mã nguồn chuẩn hóa sẵn sàng cho việc phát triển đồng thời frontend và backend.",
            "Git commit 010dc61, fb8d46b, 0b73642.",
            "HOÀN THÀNH"
        ],
        [
            "23/08/2026\n(Giai đoạn 5)",
            "Tích hợp luồng camera ban đầu và mô hình YOLOv8.",
            "Viết module tiếp nhận video từ webcam máy trạm; tích hợp mô hình YOLOv8 phát hiện người và vật thể thời gian thực.",
            "Tốc độ camera 15-30 FPS trong khi mô hình suy luận trên CPU chỉ đạt 3-5 FPS gây lag giao diện.",
            "Bước đầu thử nghiệm điều chỉnh kích thước ảnh đầu vào để giảm tải tính toán.",
            "Hệ thống hiển thị luồng webcam kèm khung bao nhận diện người trực tiếp.",
            "Git commit f11092e, 833bb9b.",
            "HOÀN THÀNH"
        ],
        [
            "24/08/2026 – 31/08/2026\n(Giai đoạn 6)",
            "Huấn luyện và tiếp nhận mô hình AI chuyên dụng.",
            "Thu thập tập dữ liệu phone_merged (2.961 ảnh, 3.706 bboxes); cấu hình huấn luyện YOLO11s 60 epochs; tiếp nhận YOLO11m-pose 17 điểm mốc.",
            "Dữ liệu huấn luyện có nguy cơ trùng lặp giữa các phần split làm sai lệch chỉ số đánh giá.",
            "Kiểm tra mã băm SHA-256 xác nhận không có ảnh trùng tuyệt đối; ghi nhận hạn chế chưa có perceptual hash.",
            "Xuất tệp trọng số phone_detector_v5.pt đạt mAP@0.5 = 0,7858 trên tập validation nội bộ; tiếp nhận yolo11m-pose.pt.",
            "Tập tin weights phone_detector_v5.pt; Báo cáo huấn luyện nội bộ.",
            "HOÀN THÀNH"
        ],
        [
            "01/09/2026\n(Giai đoạn 7)",
            "Xây dựng pipeline xử lý video và tích hợp V7 Detector.",
            "Tích hợp ExamBehaviorDetector vào luồng xử lý; kết hợp thuật toán bám vết ByteTrack để gán mã số chuyển động track_id.",
            "ID chuyển động bị nhảy liên tục khi thí sinh bị che khuất một phần bởi người ngồi trước.",
            "Tinh chỉnh tham số thời gian duy trì vết (track_buffer) trong ByteTrack để ổn định định danh tạm thời.",
            "Pipeline nhận diện đồng thời người, điện thoại và ước lượng tư thế mượt mà.",
            "Git commit 94c0397.",
            "HOÀN THÀNH"
        ],
        [
            "02/09/2026 – 06/09/2026\n(Giai đoạn 8)",
            "Xây dựng cơ chế trích xuất video bằng chứng RingBuffer.",
            "Nghiên cứu cấu trúc hàng đợi hai đầu (collections.deque) lưu trữ trong RAM; thiết kế cửa sổ thời gian pre-roll 5.0s và post-roll 10.0s.",
            "Nếu xuất clip chỉ dựa trên số lượng khung hình, khi camera sụt giảm FPS đoạn clip sẽ bị ngắn hơn thực tế.",
            "Chuyển sang cơ chế cửa sổ dựa trên mốc thời gian thực (Time-Based RingBuffer) thay vì đếm số khung hình.",
            "Hệ thống tự động cắt và lưu tập tin MP4 dài ~15.0 giây khi có sự kiện vi phạm cờ Đỏ.",
            "Tập tin backend/services/ring_buffer.py.",
            "HOÀN THÀNH"
        ],
        [
            "07/09/2026\n(Giai đoạn 9)",
            "Xây dựng cơ sở dữ liệu sự cố SQLite và Backend API.",
            "Thiết kế bảng incidents lưu vết sự cố; xây dựng các API RESTful: GET /api/incidents, PATCH /api/incidents/{id}/confirm bằng FastAPI.",
            "SQLite bị khóa (database is locked) khi nhiều luồng cùng cố gắng ghi sự cố đồng thời.",
            "Kích hoạt chế độ WAL (PRAGMA journal_mode=WAL) và xây dựng hàng đợi tuần tự DBWriteQueue luồng an toàn.",
            "Dịch vụ backend ổn định, hạn chế tối đa nguy cơ deadlock khi ghi dữ liệu dồn dập.",
            "Git commit 9806317; Tệp cheating_system.db.",
            "HOÀN THÀNH"
        ],
        [
            "07/09/2026\n(Giai đoạn 10)",
            "Xây dựng giao diện giám thị React 19 và kết nối API.",
            "Phát triển giao diện bảng điều khiển giám thị bằng React 19 và Tailwind CSS; kết nối trực tiếp với API backend.",
            "Giao diện bị giật khi liên tục cập nhật trạng thái sự cố mới.",
            "Áp dụng cơ chế polling 2 giây có điều kiện kết hợp cập nhật bất biến (immutable state update).",
            "Bảng điều khiển giám thị phản hồi tức thời, hiển thị danh sách sự cố trực tiếp từ cơ sở dữ liệu.",
            "Git commit 6362a47.",
            "HOÀN THÀNH"
        ],
        [
            "07/09/2026\n(Giai đoạn 11)",
            "Triển khai quy chuẩn quan sát hộp kính (Glass Box Rule 11).",
            "Chuẩn hóa toàn bộ hệ thống logging đa tầng trên backend và frontend; cấm tuyệt đối việc nuốt ngoại lệ try...except: pass.",
            "Khó truy vết nguyên nhân khi AI phát hiện sai hoặc luồng xử lý bị gián đoạn ngầm.",
            "Đặt 3 điểm chốt chặn log bắt buộc: Input Payload Trace, Logic Branching và Exception with Traceback.",
            "Mọi quyết định phân loại cờ vàng/đỏ và lỗi hệ thống đều hiển thị rõ ràng tại Terminal.",
            "Git commit 45bab41; AGENTS.md Rule 11.",
            "HOÀN THÀNH"
        ],
        [
            "08/09/2026 – 09/09/2026\n(Giai đoạn 12)",
            "Tinh giản giao diện theo chuẩn Anti-Slop Guidelines.",
            "Rà soát và thiết kế lại giao diện theo phong cách tối giản công nghiệp: loại bỏ thanh menu bên trái, loại bỏ các nút lập biên bản tự động.",
            "Giao diện ban đầu chứa các tính năng giả định (mẫu biên bản A1/A2, chữ ký số) gây hiểu lầm về mặt pháp lý thi cử.",
            "Loại bỏ các thành phần giao diện không nằm trong phạm vi thực thi, chỉ giữ lại 2 chế độ hiển thị cốt lõi: Giám sát trực tiếp và Cấu hình độ nhạy AI.",
            "Giao diện ExamVision AI chuẩn Anti-Slop: tông màu Charcoal/Slate, viền 1px, độ tập trung dữ liệu cao.",
            "Git commit 7dd6799, 512f580, 9dbc7cb.",
            "HOÀN THÀNH"
        ],
        [
            "09/09/2026\n(Giai đoạn 13)",
            "Xử lý lỗi video timelapse và tích hợp OpenH264.",
            "Kiểm tra chất lượng các đoạn clip MP4 xuất ra từ RingBuffer; tích hợp thư viện openh264-2.5.0-win64.dll trên Windows.",
            "Tập tin MP4 khi phát lại bị tua nhanh như timelapse do khoảng cách thời gian giữa các khung hình không đều.",
            "Viết thuật toán Time-Based Resampling: nội suy các khung hình theo lưới thời gian cố định 15 FPS trước khi ghi tệp video.",
            "Video bằng chứng MP4 phát lại ở tốc độ tự nhiên gần 1.0x, chuyển động mượt mà và trung thực.",
            "Git commit 5cd5b9f; openh264 DLL tích hợp.",
            "HOÀN THÀNH"
        ],
        [
            "10/09/2026 – 14/09/2026\n(Giai đoạn 14)",
            "Tái cấu trúc hệ thống và xây dựng màn hình Cấu hình AI.",
            "Tái cấu trúc mã nguồn backend và frontend; phát triển màn hình AISettingsView cho phép điều chỉnh độ nhạy trực tiếp trên web.",
            "Tham số cấu hình bị mất khi khởi động lại máy chủ.",
            "Lập trình cơ chế lưu bền vững cấu hình vào tệp JSON (data/ai_settings.json) và đồng bộ runtime tức thời.",
            "Giám thị có thể tinh chỉnh ngưỡng điện thoại, thời gian leo thang cờ đỏ, tham số RingBuffer ngay trên giao diện.",
            "Git commit 8e4a855, 13a4de1; backend/routers/settings.py.",
            "HOÀN THÀNH"
        ],
        [
            "15/09/2026 – 16/09/2026\n(Giai đoạn 15)",
            "Nâng cấp kiến trúc hỗ trợ hệ thống hai camera (Dual-Camera).",
            "Xây dựng dịch vụ CameraManager và thuật toán lập lịch suy luận công bằng FairInferenceScheduler cho hệ thống hai camera.",
            "Camera 1 gửi dữ liệu nhanh chiếm trọn tài nguyên CPU khiến Camera 2 bị thiếu lượt xử lý.",
            "Lập trình cơ chế Fair Round-Robin: luân chuyển lượt suy luận tuần tự qua danh sách các camera đang hoạt động.",
            "Kiến trúc hỗ trợ điều phối hai luồng camera theo thuật toán Fair Round-Robin; hoàn thành kiểm thử giả lập phần mềm (synthetic acceptance); nghiệm thu đồng thời hai camera vật lý: HARDWARE ACCEPTANCE PENDING (ba ô hiển thị trên giao diện kiểm thử thực chất là 01 webcam vật lý kết hợp 02 luồng kiểm thử phần mềm; không suy diễn giao diện ba ô thành hệ thống ba camera vật lý).",
            "Git commit 8a6ee60; backend/services/camera_manager.py.",
            "HOÀN THÀNH"
        ],
        [
            "16/09/2026 – 17/09/2026\n(Giai đoạn 16)",
            "Chuẩn hóa thang đo độ tin cậy và Kiểm thử hồi quy.",
            "Rà soát dữ liệu confidence trong toàn bộ hệ thống; viết lại module confidence.py; chạy bộ kiểm thử toàn diện.",
            "Xung đột giữa dữ liệu cũ (thang đo 1-100) và dữ liệu mới (thang đo 0.0-1.0) gây hiểu nhầm khi hiển thị.",
            "Thực hiện script di trú dữ liệu migrate_db.py và kiểm tra chặt chẽ đầu vào bằng Pydantic.",
            "Toàn bộ bản ghi sự cố có confidence chuẩn hóa [0.0, 1.0]; module confidence.py từ chối giá trị âm bằng InvalidConfidenceError (không clamp); 83 bài test backend đạt kết quả PASS.",
            "Git commit 11a8756; backend/confidence.py.",
            "HOÀN THÀNH"
        ],
        [
            "17/09/2026 – 18/09/2026\n(Giai đoạn 17)",
            "Benchmark tải hệ thống và Nghiệm thu Sprint 3.2B-R2.",
            "Chạy phiên đo hiệu năng 125,1s; thực hiện benchmark đa camera 62s Scenario A & B; chạy quy trình nghiệm thu 16 bước.",
            "Cần đảm bảo không có rò rỉ thông tin nhạy cảm (token, mật khẩu, IP) trong các tệp lưu vết công khai.",
            "Chạy script secret_scan_r2.py kiểm tra toàn bộ kho mã nguồn và tạo bảng băm SHA-256 cho các tệp chứng cứ.",
            "Hoàn thành nghiệm thu phần mềm (Software Acceptance PASS); bảo lưu trạng thái phần cứng vật lý PENDING.",
            "Tập tin acceptance_summary.json, SPRINT_3_2B_R2_REPORT.md.",
            "HOÀN THÀNH"
        ],
        [
            "19/09/2026 – 25/09/2026\n(Giai đoạn 18)",
            "Khảo sát thiết bị, chụp ảnh giao diện cục bộ và Hoàn thiện hồ sơ.",
            "Khảo sát thực địa phòng thi; đặt mua 2 webcam ngoài EYD PC02; chạy ứng dụng cục bộ trên máy trạm, chụp ảnh giao diện thật; biên soạn bộ hồ sơ nghiên cứu gửi Hà Nội.",
            "Cần bảo đảm báo cáo khách quan, trung thực với mã nguồn hiện tại, không đưa các tuyên bố lý thuyết chưa triển khai vào hồ sơ.",
            "Đối chiếu từng tuyên bố với mã nguồn thực tế; phân loại rõ ràng các tính năng hướng phát triển; chèn ảnh chụp giao diện cục bộ và sơ đồ kỹ thuật.",
            "Hoàn thiện toàn bộ bộ hồ sơ KHKT gồm Báo cáo nghiên cứu khoa học và Nhật ký xây dựng sản phẩm; ghi nhận trạng thái: HARDWARE ACCEPTANCE: PENDING (chờ bàn giao thiết bị phần cứng).",
            "Thư mục deliverables/ha_noi/; Ảnh chụp giao diện cục bộ.",
            "HOÀN THÀNH"
        ]
    ]

    col_widths = [0.8, 0.8, 1.1, 0.8, 0.9, 0.9, 0.7, 0.5]
    add_tbl(doc, diary_headers, diary_rows, caption="Bảng Nhật ký: Tiến trình Nghiên cứu, Xây dựng và Nghiệm thu Hệ thống (18 Giai đoạn)", col_widths=col_widths)

    output_path = r"deliverables\ha_noi\NHAT_KY_XAY_DUNG_SAN_PHAM_GIAM_SAT_PHONG_THI_FINAL.docx"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f"Successfully generated: {output_path}")

if __name__ == '__main__':
    build_nhat_ky()
