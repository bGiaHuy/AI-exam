# -*- coding: utf-8 -*-
"""
Script to build BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.docx
Strictly audited against:
- Single Unified Feature Catalog (7 functions: F-01 to F-07)
- Bounded, honest academic language (no overclaiming, no 100% absolute claims)
- Clear image classification (Group A: Local UI screenshots vs Group B: Illustrated technical diagrams)
- Exact canonical confidence contract: rejects negative values (no clamping to 0)
- Hardware status: HARDWARE ACCEPTANCE: PENDING (webcam hardware pending delivery)
- Database audit: 439 incident records noted following live capture session
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

def append_t_event(p, size_pt=13):
    r_t = p.add_run("t")
    format_run(r_t, size_pt=size_pt, italic=True)
    r_ev = p.add_run("event")
    format_run(r_ev, size_pt=size_pt - 3.5)
    r_ev.font.subscript = True

def build_bao_cao():
    doc = docx.Document()
    
    # Page setup - A4, standard margins (Left 30mm, Right 20mm, Top 20mm, Bottom 20mm)
    for section in doc.sections:
        section.page_width = Mm(210)
        section.page_height = Mm(297)
        section.left_margin = Mm(30)
        section.right_margin = Mm(20)
        section.top_margin = Mm(20)
        section.bottom_margin = Mm(20)
        
        # Configure Header & Footer
        footer = section.footer
        p_ft = footer.paragraphs[0]
        p_ft.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_ft = p_ft.add_run("Báo cáo Nghiên cứu KHKT — Hệ thống Hỗ trợ Giám sát Phòng thi")
        format_run(r_ft, size_pt=9, italic=True, color_rgb=(0, 0, 0))
    
    # =========================================================================
    # TRANG BÌA (COVER PAGE)
    # =========================================================================
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(25)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run("BỘ GIÁO DỤC VÀ ĐÀO TẠO")
    format_run(r, size_pt=14, bold=True, color_rgb=(0, 0, 0))
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(20)
    r = p.add_run("CUỘC THI KHOA HỌC KỸ THUẬT CẤP QUỐC GIA DÀNH CHO HỌC SINH TRUNG HỌC")
    format_run(r, size_pt=13, bold=True, color_rgb=(0, 0, 0))
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(35)
    p.paragraph_format.space_after = Pt(12)
    r = p.add_run("BÁO CÁO KẾT QUẢ DỰ ÁN")
    format_run(r, size_pt=18, bold=True, color_rgb=(0, 0, 0))
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(18)
    r = p.add_run("HỆ THỐNG HỖ TRỢ GIÁM SÁT PHÒNG THI\nBẰNG THỊ GIÁC MÁY TÍNH VÀ TRÍCH XUẤT VIDEO BẰNG CHỨNG")
    format_run(r, size_pt=16, bold=True, color_rgb=(0, 0, 0))
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(50)
    r = p.add_run("LĨNH VỰC: PHẦN MỀM HỆ THỐNG")
    format_run(r, size_pt=13.5, bold=True, color_rgb=(0, 0, 0))
    
    # Author info table with explicit pending metadata placeholders
    info_data = [
        ["Đoàn dự thi:", "HÀ NỘI"],
        ["Đơn vị / Trường học:", "[Tên trường THPT — Thí sinh bổ sung trước khi in nộp]"],
        ["Nhóm tác giả thực hiện:", "[Họ và tên thí sinh 1 & Thí sinh 2 — Thí sinh bổ sung]"],
        ["Người hướng dẫn khoa học:", "[Họ và tên giáo viên hướng dẫn — Thí sinh bổ sung]"],
        ["Địa điểm thực nghiệm:", "Phòng máy trạm nghiên cứu & Phòng thi mô phỏng"],
        ["Thời gian thực hiện:", "Năm học 2025 – 2026"]
    ]
    tbl_info = doc.add_table(rows=len(info_data), cols=2)
    tbl_info.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(info_data):
        c0 = tbl_info.rows[r_idx].cells[0]
        c1 = tbl_info.rows[r_idx].cells[1]
        c0.text = row[0]
        c1.text = row[1]
        c0.width = Inches(2.5)
        c1.width = Inches(3.7)
        set_cell_margins(c0, top=50, bottom=50, left=80, right=80)
        set_cell_margins(c1, top=50, bottom=50, left=80, right=80)
        p0 = c0.paragraphs[0]
        p1 = c1.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        format_run(p0.runs[0], size_pt=11.5, bold=True)
        format_run(p1.runs[0], size_pt=11.5, bold=False)
        
    doc.add_page_break()

    # =========================================================================
    # MỤC LỤC
    # =========================================================================
    add_h1(doc, "MỤC LỤC", space_before=10, space_after=12)
    
    # TOC placeholders will be updated after exact page scan
    toc_items = [
        ("DANH MỤC CÁC TỪ VIẾT TẮT", "4"),
        ("DANH MỤC CÁC BẢNG BIỂU", "5"),
        ("DANH MỤC CÁC HÌNH VẼ VÀ ĐỒ THỊ", "5"),
        ("PHẦN I: MỞ ĐẦU", "6"),
        ("  1. Lý do chọn đề tài", "6"),
        ("  2. Mục tiêu nghiên cứu", "6"),
        ("  3. Đối tượng và phạm vi nghiên cứu", "7"),
        ("  4. Phương pháp nghiên cứu", "8"),
        ("    4.1. Phương pháp phân tích và tổng hợp lý thuyết", "8"),
        ("    4.2. Phương pháp quan sát khoa học", "8"),
        ("    4.3. Phương pháp thực nghiệm khoa học", "8"),
        ("    4.4. Phương pháp chuyên gia", "8"),
        ("  5. Tính mới và tính sáng tạo của đề tài", "8"),
        ("  6. Giới hạn của đề tài", "9"),
        ("PHẦN II: NỘI DUNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU", "10"),
        ("  1. Phương án thiết kế", "10"),
        ("    1.1. Yêu cầu hệ thống", "10"),
        ("    1.2. Kiến trúc tổng thể hệ thống", "10"),
        ("    1.3. Các mô-đun chính của hệ thống", "10"),
        ("    1.4. Luồng xử lý dữ liệu và điều phối video", "11"),
        ("    1.5. Sơ đồ nguyên lý hoạt động", "11"),
        ("    1.6. Thiết kế lưu trữ và bằng chứng", "12"),
        ("    1.7. Thiết kế giao diện người dùng", "13"),
        ("  2. Công nghệ và thư viện sử dụng", "14"),
        ("  3. Thiết kế và lập trình phần mềm", "15"),
        ("    3.1. Hiện thực hóa Backend và Giải quyết tranh chấp tài nguyên", "15"),
        ("    3.2. Hiện thực hóa Frontend và Quy chuẩn Quan sát Hộp kính", "16"),
        ("  4. Danh mục 7 chức năng cốt lõi của sản phẩm", "16"),
        ("    4.1. Chức năng 1 (F-01): Tiếp nhận và hiển thị đa luồng camera trực tiếp", "17"),
        ("    4.2. Chức năng 2 (F-02): Phát hiện điện thoại di động trong khu vực làm bài", "18"),
        ("    4.3. Chức năng 3 (F-03): Phân tích tư thế và phát hiện hành vi quay đầu nghi vấn", "19"),
        ("    4.4. Chức năng 4 (F-04): Bộ đệm vòng và trích xuất clip bằng chứng chuẩn tốc độ 1.0x", "20"),
        ("    4.5. Chức năng 5 (F-05): Quản lý và lưu trữ sự cố an toàn bằng SQLite WAL", "21"),
        ("    4.6. Chức năng 6 (F-06): Thẩm tra sự cố vi phạm và phê duyệt của giám thị", "21"),
        ("    4.7. Chức năng 7 (F-07): Cấu hình động độ nhạy AI và tham số ghi hình bằng chứng", "23"),
        ("  5. Nguyên lý hoạt động tổng thể của hệ thống", "24"),
        ("  6. Giới hạn phiên bản hiện tại", "25"),
        ("PHẦN III: QUÁ TRÌNH THỬ NGHIỆM VÀ KẾT QUẢ ĐẠT ĐƯỢC", "26"),
        ("  1. Phương pháp thử nghiệm", "26"),
        ("  2. Thử nghiệm từng thành phần", "26"),
        ("    2.1. Tập dữ liệu và Huấn luyện mô hình phát hiện điện thoại", "26"),
        ("    2.2. Thử nghiệm thuật toán phát hiện quay đầu nghi vấn", "27"),
        ("  3. Thử nghiệm tổng thể hệ thống", "28"),
        ("    3.1. Phiên đo thông lượng thời gian thực 125,1 giây", "28"),
        ("    3.2. Kết quả kiểm thử tự động toàn diện (Aggregate Test Suite)", "28"),
        ("    3.3. Thử nghiệm độ ổn định bộ nhớ đa camera (62 giây)", "29"),
        ("  4. Kết quả ghi nhận", "29"),
        ("  5. Hạn chế của kết quả và giới hạn diễn giải khoa học", "30"),
        ("  6. Những cải tiến đã thực hiện sau thử nghiệm", "30"),
        ("PHẦN IV: KẾT LUẬN VÀ KIẾN NGHỊ", "32"),
        ("  1. Kết luận", "32"),
        ("  2. Đóng góp kỹ thuật và xã hội của đề tài", "32"),
        ("  3. Kiến nghị", "32"),
        ("PHẦN V: HƯỚNG PHÁT TRIỂN ĐỀ TÀI", "32"),
        ("PHẦN VI: TÀI LIỆU THAM KHẢO", "33"),
        ("PHỤ LỤC: MA TRẬN MINH CHỨNG VÀ TRUY VẾT DỮ LIỆU", "35")
    ]
    
    for title, page in toc_items:
        p_toc = doc.add_paragraph()
        p_toc.paragraph_format.line_spacing = 1.15
        p_toc.paragraph_format.space_before = Pt(1)
        p_toc.paragraph_format.space_after = Pt(2)
        dots_count = max(3, 75 - len(title))
        dots = " " + ("." * dots_count) + " "
        r_title = p_toc.add_run(title)
        is_main = title.startswith("PHẦN") or title.startswith("DANH MỤC")
        format_run(r_title, size_pt=11.5, bold=is_main)
        r_dots = p_toc.add_run(dots)
        format_run(r_dots, size_pt=10, bold=False, color_rgb=(0, 0, 0))
        r_page = p_toc.add_run(page)
        format_run(r_page, size_pt=11.5, bold=is_main)
        
    doc.add_page_break()

    # =========================================================================
    # DANH MỤC TỪ VIẾT TẮT
    # =========================================================================
    add_h1(doc, "DANH MỤC CÁC TỪ VIẾT TẮT", space_before=10, space_after=12)
    abbr_data = [
        ["AI", "Artificial Intelligence (Trí tuệ nhân tạo)"],
        ["API", "Application Programming Interface (Giao diện lập trình ứng dụng)"],
        ["ASGI", "Asynchronous Server Gateway Interface (Giao thức máy chủ bất đồng bộ)"],
        ["CCTV", "Closed-Circuit Television (Hệ thống camera truyền hình mạch kín)"],
        ["CNN", "Convolutional Neural Network (Mạng nơ-ron tích chập)"],
        ["COCO", "Common Objects in Context (Bộ dữ liệu thị giác máy tính chuẩn quốc tế)"],
        ["CPU", "Central Processing Unit (Bộ vi xử lý trung tâm máy tính)"],
        ["EMA", "Exponential Moving Average (Trung bình trượt lũy thừa làm mượt tọa độ)"],
        ["FPS", "Frames Per Second (Số lượng khung hình xử lý trên mỗi giây)"],
        ["GPU", "Graphics Processing Unit (Bộ vi xử lý đồ họa tăng tốc tính toán)"],
        ["HUD", "Heads-Up Display (Bảng thông số chỉ số hiển thị trực tiếp trên giao diện)"],
        ["mAP", "Mean Average Precision (Độ chính xác trung bình toàn diện của mô hình)"],
        ["MOT", "Multi-Object Tracking (Bám vết đa đối tượng qua chuỗi khung hình liên tục)"],
        ["MP4", "MPEG-4 Part 14 (Định dạng tập tin chuẩn nén video số)"],
        ["ORM", "Object-Relational Mapping (Ánh xạ cơ sở dữ liệu quan hệ sang đối tượng)"],
        ["REST", "Representational State Transfer (Kiến trúc dịch vụ web truyền nhận dữ liệu)"],
        ["RTSP", "Real-Time Streaming Protocol (Giao thức truyền luồng video từ camera IP)"],
        ["SBD", "Số báo danh (Mã định danh cá nhân của thí sinh dự thi)"],
        ["UTC", "Coordinated Universal Time (Giờ phối hợp quốc tế)"],
        ["WAL", "Write-Ahead Logging (Cơ chế nhật ký ghi trước đảm bảo an toàn SQLite)"],
        ["WebSocket", "Giao thức truyền thông hai chiều thời gian thực giữa máy khách và máy chủ"],
        ["YOLO", "You Only Look Once (Họ mô hình nhận diện đối tượng thời gian thực)"]
    ]
    add_tbl(doc, ["Ký hiệu", "Tên đầy đủ và Giải thích ý nghĩa"], abbr_data, col_widths=[1.5, 4.5])
    
    # DANH MỤC BẢNG BIỂU
    add_h2(doc, "DANH MỤC CÁC BẢNG BIỂU", space_before=16, space_after=8)
    tbl_list = [
        ("Bảng 1.1", "So sánh các phương pháp giám sát phòng thi hiện nay"),
        ("Bảng 2.1", "Đặc tả các mô-đun chức năng thành phần trong hệ thống"),
        ("Bảng 2.2", "Cấu trúc dữ liệu lược đồ bảng lưu trữ sự cố (incidents schema)"),
        ("Bảng 2.3", "Danh mục đối chiếu các thư viện và công nghệ thực tế sử dụng trong hệ thống"),
        ("Bảng 2.4", "Danh mục 7 chức năng cốt lõi đã triển khai và kiểm chứng (F-01 đến F-07)"),
        ("Bảng 3.1", "Phân bố tập dữ liệu huấn luyện lịch sử phone_merged"),
        ("Bảng 3.2", "Thông số cấu hình huấn luyện mô hình nhận diện điện thoại"),
        ("Bảng 3.3", "Kết quả huấn luyện mô hình YOLO11s trên tập xác thực nội bộ"),
        ("Bảng 3.4", "Kết quả đo thông lượng phiên thực nghiệm 125,1 giây"),
        ("Bảng 3.5", "Kết quả thực thi các bộ kiểm thử tự động hệ thống"),
        ("Bảng 3.6", "Kết quả đo tải bộ nhớ kịch bản đa camera (Scenario A & B)")
    ]
    add_tbl(doc, ["Mã bảng", "Tên nội dung bảng số liệu"], tbl_list, col_widths=[1.5, 4.5])
    
    # DANH MỤC HÌNH VẼ
    add_h2(doc, "DANH MỤC CÁC HÌNH VẼ VÀ ĐỒ THỊ", space_before=16, space_after=8)
    fig_list = [
        ("Hình 2.1 (Nhóm B)", "Sơ đồ kỹ thuật kiến trúc điều phối hai luồng xử lý (Dual-Stream Architecture)"),
        ("Hình 2.2 (Nhóm B)", "Sơ đồ kỹ thuật cơ chế trích xuất cửa sổ thời gian video bằng chứng trong RingBuffer"),
        ("Hình 2.3 (Nhóm B)", "Sơ đồ kỹ thuật 17 điểm khung xương YOLO Pose và quy tắc tính điểm nghi vấn 2D"),
        ("Hình 2.4 (Nhóm A)", "Ảnh giao diện cục bộ: Lưới hiển thị chi tiết các luồng camera giám sát"),
        ("Hình 2.5 (Nhóm A)", "Ảnh giao diện cục bộ: Bảng điều khiển giám sát trực tiếp ExamVision AI"),
        ("Hình 2.6 (Nhóm A)", "Ảnh giao diện cục bộ: Bảng danh sách sự cố vi phạm cờ đỏ và nút phê duyệt"),
        ("Hình 2.7 (Nhóm A)", "Ảnh giao diện cục bộ: Hộp thoại phát lại video bằng chứng MP4 đã nội suy chuẩn 1.0x"),
        ("Hình 2.8 (Nhóm A)", "Ảnh giao diện cục bộ: Màn hình cấu hình động độ nhạy AI và tham số RingBuffer"),
        ("Hình 3.1 (Nhóm B)", "Đồ thị diễn biến Precision, Recall và mAP@0.5 trong quá trình huấn luyện mô hình")
    ]
    add_tbl(doc, ["Mã hình", "Tên nội dung hình ảnh / sơ đồ kỹ thuật minh họa"], fig_list, col_widths=[1.5, 4.5])
    
    doc.add_page_break()

    # =========================================================================
    # PHẦN I: MỞ ĐẦU
    # =========================================================================
    add_h1(doc, "PHẦN I: MỞ ĐẦU", space_before=10, space_after=10)
    
    add_h2(doc, "1. Lý do chọn đề tài")
    add_p(doc, "Trong các kỳ thi tập trung, tính công bằng, nghiêm minh và minh bạch là yêu cầu quan trọng nhằm bảo đảm đánh giá thực chất năng lực người học. Hiện nay, công tác giám sát tại phòng thi truyền thống phụ thuộc chủ yếu vào sự quan sát trực tiếp của cán bộ coi thi (giám thị). Trong một phòng thi tiêu chuẩn từ 24 đến 30 thí sinh, kéo dài từ 90 đến 180 phút, giám thị phải bao quát liên tục một không gian rộng.")
    add_p(doc, "Các nghiên cứu tâm lý học thực nghiệm về khả năng duy trì sự chú ý thị giác kéo dài (tiêu biểu như thí nghiệm Mackworth Clock Test [1] và các công trình của Warm, Parasuraman [2]) đã chỉ ra rằng: khả năng phát hiện tín hiệu bất thường suy giảm nhanh chóng sau khoảng 30 phút làm việc liên tục do mỏi mắt và căng thẳng nhận thức. Trong khi đó, các hành vi vi phạm quy chế thi cử phổ biến—như lén sử dụng điện thoại thông minh hoặc quay đầu nhìn bài thi của thí sinh bên cạnh—thường diễn ra trong thời gian ngắn (từ 1 đến 3 giây), xảy ra ở góc khuất hoặc diễn ra đồng thời ở nhiều vị trí.")
    add_p(doc, "Nếu chỉ dựa vào cảm quan tức thời, việc lập biên bản xử lý vi phạm dễ phát sinh tranh cãi do thiếu chứng cứ ghi hình khách quan ghi lại diễn biến trước và sau thời điểm xảy ra sự việc. Việc trang bị camera giám sát CCTV thông thường chỉ ghi lại video thụ động toàn ca thi; khi phát sinh nghi vấn, giám thị phải mất nhiều thời gian tua quét thủ công trong hàng gigabyte dữ liệu để tìm đoạn trích liên quan.")
    add_p(doc, "Xuất phát từ thực tế đó, nhóm nghiên cứu lựa chọn đề tài: “Hệ thống hỗ trợ giám sát phòng thi bằng thị giác máy tính và trích xuất video bằng chứng”. Đề tài hướng tới việc xây dựng một giải pháp phần mềm chạy cục bộ trên máy trạm (on-premise offline), có khả năng phân tích hình ảnh theo thời gian thực để phát hiện dấu hiệu nghi vấn (sự xuất hiện của điện thoại và tư thế quay đầu kéo dài), đồng thời tự động cắt trích đoạn clip video bằng chứng dài khoảng 15 giây (chứa cả bối cảnh trước và sau sự kiện) lưu trữ có cấu trúc để hỗ trợ giám thị xem xét, ra quyết định chính xác.")

    add_h2(doc, "2. Mục tiêu nghiên cứu")
    add_p(doc, "Đề tài được thực hiện nhằm hướng tới các mục tiêu kỹ thuật cụ thể sau:")
    add_bullet(doc, "Xây dựng nguyên mẫu phần mềm chạy cục bộ trên máy trạm của giám thị, có khả năng tiếp nhận luồng video từ nguồn camera (webcam máy trạm, USB camera, camera IP RTSP) với tốc độ thu nhận đạt xấp xỉ 15 FPS.", "Mục tiêu 1: ");
    add_bullet(doc, "Tích hợp mô hình học sâu thị giác máy tính (YOLO11s) được huấn luyện để phát hiện điện thoại di động trong khu vực làm bài thi của thí sinh với độ tin cậy được chuẩn hóa.", "Mục tiêu 2: ");
    add_bullet(doc, "Xây dựng thuật toán phân tích tư thế hình học 2D dựa trên 17 điểm khung xương cơ thể (YOLO11m-pose) kết hợp bộ lọc trung bình trượt lũy thừa EMA và điều kiện duy trì thời gian nhằm phát hiện hành vi quay đầu bất thường, hạn chế cảnh báo cử động thoáng qua.", "Mục tiêu 3: ");
    add_bullet(doc, "Giải quyết bài toán thắt nút cổ chai hiệu năng bằng kiến trúc hai luồng: phân tách luồng ghi hình RingBuffer khỏi luồng suy luận AI, ưu tiên khung hình mới nhất, hạn chế sự gia tăng độ trễ tích lũy trong kịch bản thử nghiệm.", "Mục tiêu 4: ");
    add_bullet(doc, "Tự động trích xuất các đoạn video clip bằng chứng ngắn định dạng MP4 danh định khoảng 15 giây (5 giây trước sự kiện và 10 giây sau sự kiện) được nội suy tốc độ thực 1.0x, lưu trữ cùng siêu dữ liệu có cấu trúc trong cơ sở dữ liệu SQLite chế độ WAL.", "Mục tiêu 5: ");
    add_bullet(doc, "Phát triển giao diện bảng điều khiển giám thị (Proctor Dashboard) trực quan theo phong cách tối giản công nghiệp, hỗ trợ giám thị xem lại video bằng chứng, phê duyệt xác nhận hoặc bỏ qua cảnh báo.", "Mục tiêu 6: ");

    add_h2(doc, "3. Đối tượng và phạm vi nghiên cứu")
    add_p(doc, "Đối tượng nghiên cứu của đề tài gồm:", bold_prefix="a) Đối tượng nghiên cứu: ")
    add_bullet(doc, "Hình ảnh video ghi lại hoạt động trong phòng thi giấy truyền thống với bàn ghế và cử động cơ thể của thí sinh.");
    add_bullet(doc, "Hai hành vi nghi vấn trọng tâm: sử dụng điện thoại di động và tư thế quay đầu bất thường sang bài thi xung quanh.");
    add_bullet(doc, "Các giải thuật thị giác máy tính: nhận diện vật thể (Object Detection), ước lượng tư thế người (Pose Estimation), bám vết chuyển động (ByteTrack) và quản trị bộ đệm video vòng (Circular RingBuffer).");
    
    add_p(doc, "Phạm vi nghiên cứu và ranh giới kỹ thuật được xác định cụ thể:", bold_prefix="b) Phạm vi nghiên cứu: ")
    add_bullet(doc, "Hệ thống vận hành cục bộ trên máy trạm (Offline On-Premise), không gửi dữ liệu ra máy chủ đám mây, bảo đảm an toàn dữ liệu nội bộ phòng thi.");
    add_bullet(doc, "Quy mô thực nghiệm: áp dụng cho một phòng thi cụ thể với cấu hình kết nối camera giám sát.");
    add_bullet(doc, "Ranh giới kỹ thuật rõ ràng (Strict Non-Goals): Hệ thống KHÔNG nhận diện danh tính thí sinh (không quét khuôn mặt, không lưu tên hay số báo danh), KHÔNG sử dụng mô hình ngôn ngữ lớn RAG/AI Chatbot, KHÔNG tự động lập biên bản kỷ luật và KHÔNG tự đưa ra quyết định xử lý thí sinh. Quyết định xử lý vi phạm thuộc về giám thị con người (Human-in-the-Loop).");

    add_h2(doc, "4. Phương pháp nghiên cứu")
    add_p(doc, "Nhóm nghiên cứu đã áp dụng bốn phương pháp nghiên cứu khoa học cơ bản:")
    
    add_h3(doc, "4.1. Phương pháp phân tích và tổng hợp lý thuyết")
    add_p(doc, "Thu thập và phân tích các công trình nghiên cứu về thị giác máy tính, kiến trúc mạng YOLO (Redmon et al. [3], Jocher & Qiu [4]), chuẩn biểu diễn điểm mốc cơ thể COCO Keypoints [5], thuật toán bám vết ByteTrack [6], cùng tài liệu kỹ thuật về cơ chế quản trị giao dịch SQLite Write-Ahead Logging (WAL) [7]. Từ đó, tổng hợp các nguyên lý nền tảng để lựa chọn mô hình học sâu phù hợp với năng lực phần cứng máy trạm phổ thông và thiết kế kiến trúc điều phối luồng dữ liệu.")
    
    add_h3(doc, "4.2. Phương pháp quan sát khoa học")
    add_p(doc, "Quan sát và ghi nhận các chuỗi cử động thực tế trong môi trường phòng thi mô phỏng. Bằng việc phân tích góc quay đầu, vị trí tay và thao tác cầm nắm đồ vật, nhóm xác định hai tín hiệu thị giác có thể nhận biết rõ ràng: (1) thiết bị điện thoại xuất hiện trong vùng thao tác; (2) góc quay đầu sang bên duy trì liên tục vượt ngưỡng thời gian quy định.")
    
    add_h3(doc, "4.3. Phương pháp thực nghiệm khoa học")
    add_p(doc, "Xây dựng nguyên mẫu phần mềm, triển khai các bộ kiểm thử đơn vị, kiểm thử tích hợp và các phiên đo tải hiệu năng liên tục. Thông qua việc đo đạc định lượng (FPS thu nhận, FPS suy luận, tỷ lệ khung hình thay thế, độ trễ xử lý, mức chiếm dụng bộ nhớ RAM), nhóm liên tục phân tích sai số và thực hiện các chu kỳ tinh chỉnh giải thuật.")
    
    add_h3(doc, "4.4. Phương pháp chuyên gia")
    add_p(doc, "Tham vấn ý kiến của cán bộ coi thi, giáo viên Tin học và chuyên gia phần mềm. Các phản biện chuyên môn giúp nhóm hoàn thiện định hướng sản phẩm: tập trung vào việc cung cấp video bằng chứng khách quan hỗ trợ giám thị thay vì tự động hóa các quyết định hành chính.")

    add_h2(doc, "5. Tính mới và tính sáng tạo của đề tài")
    add_p(doc, "Tính mới và sáng tạo của đề tài thể hiện ở ba khía cạnh kỹ thuật:")
    add_bullet(doc, "Kiến trúc hai luồng xử lý phân tách (Dual-Stream Architecture): Hạn chế nhược điểm của các hệ thống AI xử lý tuần tự (nơi mà tốc độ suy luận mô hình chậm hơn tốc độ camera sẽ làm gia tăng hàng đợi). Bằng cách kết hợp bộ đệm vòng (RingBuffer) ghi nhận khung hình ở tốc độ khoảng 15 FPS và bộ đệm suy luận một phần tử (Single-slot Buffer) luôn giữ khung hình mới nhất, hệ thống vừa duy trì ghi hình vừa bám sát thời gian thực.", "Điểm mới 1: ");
    add_bullet(doc, "Cơ chế trích xuất bằng chứng hai chiều (Pre-roll & Post-roll Evidence Window): Hệ thống không chỉ lưu lại khung hình tại thời điểm cảnh báo mà trích xuất chuỗi khung hình từ 5.0 giây trước khi vi phạm đến 10.0 giây sau khi vi phạm (tổng ~15.0 giây), cung cấp bối cảnh hành vi trước và sau sự kiện.", "Điểm mới 2: ");
    add_bullet(doc, "Bộ lọc giảm cảnh báo giả và thuật toán nội suy thời gian thực: Áp dụng trung bình trượt lũy thừa EMA làm mượt tọa độ mốc xương, kết hợp điều kiện trễ thời gian 1.25 giây để hạn chế các cử động nhìn sang bên thoáng qua; thuật toán resampling video hỗ trợ clip MP4 xuất ra phát ở tốc độ tự nhiên xấp xỉ 1.0x.", "Điểm mới 3: ");

    add_h2(doc, "6. Giới hạn của đề tài")
    add_p(doc, "Nhóm nghiên cứu ghi nhận các giới hạn kỹ thuật của phiên bản hiện tại:")
    add_bullet(doc, "Mô hình nhận diện điện thoại được đánh giá trên tập dữ liệu lịch sử nội bộ (phone_merged), chưa có tập kiểm tra độc lập thu thập từ các phòng thi thực tế với góc máy và ánh sáng đa dạng.");
    add_bullet(doc, "Thuật toán phát hiện quay đầu dựa trên heuristic hình học 2D trên mặt phẳng ảnh, chưa phải phép đo góc quay 3D Euler (Yaw/Pitch/Roll) trong không gian thực, do đó kết quả phụ thuộc vào góc lắp đặt camera.");
    add_bullet(doc, "Phần cứng thực nghiệm hiện mới đo đạc trên cấu hình máy trạm CPU đơn, chưa đánh giá diện rộng trên các hệ thống tăng tốc phần cứng chuyên dụng.");

    doc.add_page_break()

    # =========================================================================
    # PHẦN II: NỘI DUNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU
    # =========================================================================
    add_h1(doc, "PHẦN II: NỘI DUNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU", space_before=10, space_after=10)
    
    add_h2(doc, "1. Phương án thiết kế")
    
    add_h3(doc, "1.1. Yêu cầu hệ thống")
    add_p(doc, "Hệ thống được thiết kế dựa trên các yêu cầu kỹ thuật cơ bản:")
    add_bullet(doc, "Tiếp nhận luồng video từ nguồn camera với độ phân giải tối thiểu 720p, duy trì tốc độ thu nhận mục tiêu ~15 FPS. Phát hiện hai hành vi: PHONE (điện thoại) và HEAD_TURNING (quay đầu kéo dài ≥ 1,25 giây). Tự động tạo clip MP4 bằng chứng danh định 15 giây và ghi nhận sự cố vào CSDL SQLite.", "Yêu cầu chức năng: ");
    add_bullet(doc, "Vận hành cục bộ trên máy trạm giám thị; không yêu cầu Internet; độ trễ xử lý suy luận không làm tắc nghẽn luồng ghi hình; giao diện tối giản theo phong cách Anti-Slop (màu tối Slate/Zinc, viền mỏng 1px, phản hồi nhanh).", "Yêu cầu phi chức năng: ");

    add_h3(doc, "1.2. Kiến trúc tổng thể hệ thống")
    add_p(doc, "Hệ thống được tổ chức theo kiến trúc phân tầng hướng dịch vụ cục bộ, gồm ba tầng chính:")
    add_bullet(doc, "Tầng thu nhận và hiển thị (Presentation & Acquisition Layer): Ứng dụng web React 19 chạy trên nền Vite, cung cấp bảng điều khiển giám thị (Proctor Dashboard), quản lý kết nối WebSocket truyền luồng hình ảnh nhị phân và hiển thị lưới camera.", "Tầng 1: ");
    add_bullet(doc, "Tầng xử lý trung tâm (Core Processing Layer): Máy chủ FastAPI (Python 3.12) kết hợp máy chủ ASGI Uvicorn, điều phối luồng xử lý qua CameraManager, bộ lập lịch luân phiên FairInferenceScheduler, các tiến trình suy luận YOLO và bộ đệm vòng Time-based RingBuffer.", "Tầng 2: ");
    add_bullet(doc, "Tầng lưu trữ dữ liệu (Data Layer): Cơ sở dữ liệu SQLite 3 chạy chế độ WAL, quản lý qua hàng đợi tuần tự luồng an toàn DBWriteQueue, cùng thư mục lưu trữ tập tin chứng cứ tĩnh /data/evidence/.", "Tầng 3: ");

    add_h3(doc, "1.3. Các mô-đun chính của hệ thống")
    tbl_modules = [
        ["Mô-đun CameraManager", "Quản lý vòng đời các nguồn video (USB Webcam, Camera IP RTSP, Video giả lập); hỗ trợ chuyển đổi chế độ cấu hình camera."],
        ["Mô-đun Thu nhận WebSocket", "Tiếp nhận các gói tin nhị phân chứa khung hình JPEG, số thứ tự (frame_index) và mốc thời gian (timestamp) từ phía giao diện."],
        ["Mô-đun Time-Based RingBuffer", "Bộ đệm hàng đợi vòng (collections.deque) lưu trữ chuỗi khung hình trong RAM theo cửa sổ thời gian trượt; quản lý việc xuất clip MP4."],
        ["Mô-đun Suy luận AI", "Đóng gói mô hình YOLO11s (phát hiện điện thoại) và YOLO11m-pose (ước lượng 17 điểm mốc cơ thể), chạy luồng riêng với bộ đệm một phần tử."],
        ["Mô-đun Fair Scheduler", "Bộ lập lịch luân phiên vòng tròn giữa các nguồn camera, phân bổ lượt suy luận theo chu kỳ."],
        ["Mô-đun DBWriteQueue", "Hàng đợi ghi dữ liệu tuần tự luồng an toàn (queue.Queue) nhằm giảm thiểu nguy cơ xung đột khóa đọc/ghi đồng thời trong SQLite."],
        ["Mô-đun Proctor Dashboard", "Bảng điều khiển React 19 hiển thị video gắn bounding box, danh sách thẻ sự cố vi phạm cờ đỏ và hộp thoại phát lại clip chứng cứ."]
    ]
    add_tbl(doc, ["Tên Mô-đun", "Chức năng và Nhiệm vụ Kỹ thuật"], tbl_modules, caption="Bảng 2.1. Đặc tả các mô-đun chức năng thành phần trong hệ thống", col_widths=[2.0, 4.0])

    add_h3(doc, "1.4. Luồng xử lý dữ liệu và điều phối video")
    add_p(doc, "Luồng dữ liệu được điều phối theo nguyên lý phân tách hai kênh độc lập:")
    add_bullet(doc, "Kênh 1 - Luồng ghi hình liên tục: Khung hình camera thu nhận được lập tức nạp vào bộ đệm RingBuffer tương ứng của camera đó. Luồng này vận hành ở tốc độ của camera (~15 FPS), lưu trữ dữ liệu video phục vụ trích xuất bằng chứng.");
    add_bullet(doc, "Kênh 2 - Luồng suy luận AI: Khung hình mới nhất được cập nhật vào bộ đệm một phần tử (Single-Slot Buffer). Khi tiến trình AI hoàn tất suy luận khung hình trước, nó sẽ nhận khung hình mới nhất đang chờ. Các khung hình trung gian cũ hơn sẽ được thay thế có chủ đích. Nhờ đó, luồng AI bám sát thời gian thực hiện tại mà không làm dồn ứ hàng đợi.");

    add_h3(doc, "1.5. Sơ đồ nguyên lý hoạt động")
    p_arch = add_p(doc, "Sơ đồ nguyên lý phối hợp giữa luồng thu nhận, bộ đệm vòng và luồng suy luận AI được minh họa tại Hình 2.1 (Sơ đồ kỹ thuật thuộc Nhóm B):")
    p_arch.paragraph_format.keep_with_next = True
    img_arch = r"deliverables\ha_noi\screenshots\architecture_pipeline_diagram.png"
    if os.path.exists(img_arch):
        add_fig(doc, img_arch, "Hình 2.1 (Nhóm B). Sơ đồ kỹ thuật kiến trúc điều phối hai luồng xử lý (Dual-Stream Architecture)", width_in=5.8)

    add_h3(doc, "1.6. Thiết kế lưu trữ và bằng chứng")
    p_ev = doc.add_paragraph()
    p_ev.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_ev.paragraph_format.line_spacing = 1.25
    p_ev.paragraph_format.space_before = Pt(0)
    p_ev.paragraph_format.space_after = Pt(6)
    p_ev.paragraph_format.first_line_indent = Mm(10)
    r_ev_1 = p_ev.add_run("Khi có sự kiện cờ Đỏ (phát hiện điện thoại hoặc quay đầu kéo dài ≥ 1,25 giây), hệ thống kích hoạt tiến trình trích xuất clip bằng chứng VideoClipTask từ RingBuffer. Thời điểm phát hiện vi phạm được lấy làm mốc ")
    format_run(r_ev_1, size_pt=13)
    append_t_event(p_ev, size_pt=13)
    r_ev_colon = p_ev.add_run(":")
    format_run(r_ev_colon, size_pt=13)

    p_b1 = doc.add_paragraph(style='List Bullet')
    p_b1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_b1.paragraph_format.line_spacing = 1.25
    p_b1.paragraph_format.space_before = Pt(0)
    p_b1.paragraph_format.space_after = Pt(3)
    p_b1.paragraph_format.left_indent = Mm(10)
    p_b1.paragraph_format.first_line_indent = Mm(-5)
    r_b1_pre = p_b1.add_run("Pre-roll window: ")
    format_run(r_b1_pre, size_pt=13, bold=True)
    r_b1_1 = p_b1.add_run("Thu thập chuỗi khung hình từ thời điểm ")
    format_run(r_b1_1, size_pt=13)
    append_t_event(p_b1, size_pt=13)
    r_b1_2 = p_b1.add_run(" – 5,0 giây đến ")
    format_run(r_b1_2, size_pt=13)
    append_t_event(p_b1, size_pt=13)
    r_b1_3 = p_b1.add_run(".")
    format_run(r_b1_3, size_pt=13)

    p_b2 = doc.add_paragraph(style='List Bullet')
    p_b2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_b2.paragraph_format.line_spacing = 1.25
    p_b2.paragraph_format.space_before = Pt(0)
    p_b2.paragraph_format.space_after = Pt(3)
    p_b2.paragraph_format.left_indent = Mm(10)
    p_b2.paragraph_format.first_line_indent = Mm(-5)
    r_b2_pre = p_b2.add_run("Post-roll window: ")
    format_run(r_b2_pre, size_pt=13, bold=True)
    r_b2_1 = p_b2.add_run("Bộ đệm tiếp tục thu thập thêm khung hình trong 10,0 giây tiếp theo, đến thời điểm ")
    format_run(r_b2_1, size_pt=13)
    append_t_event(p_b2, size_pt=13)
    r_b2_2 = p_b2.add_run(" + 10,0 giây.")
    format_run(r_b2_2, size_pt=13)

    p_b3 = doc.add_paragraph(style='List Bullet')
    p_b3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_b3.paragraph_format.line_spacing = 1.25
    p_b3.paragraph_format.space_before = Pt(0)
    p_b3.paragraph_format.space_after = Pt(3)
    p_b3.paragraph_format.left_indent = Mm(10)
    p_b3.paragraph_format.first_line_indent = Mm(-5)
    r_b3 = p_b3.add_run("Chuỗi khung hình sau đó được đưa qua thuật toán tái lấy mẫu đều trên lưới thời gian (Uniform Time-Grid Resampling) để xuất tập tin MP4 với mã hóa codec OpenH264, hỗ trợ clip phát lại ở tốc độ xấp xỉ 1.0x đúng nhịp thời gian thực.")
    format_run(r_b3, size_pt=13)
    
    img_ring = r"deliverables\ha_noi\screenshots\ring_buffer_time_window.png"
    if os.path.exists(img_ring):
        add_fig(doc, img_ring, "Hình 2.2 (Nhóm B). Sơ đồ kỹ thuật cơ chế trích xuất cửa sổ thời gian video bằng chứng trong RingBuffer", width_in=5.8)
        
    add_p(doc, "Dữ liệu sự cố được quản lý trong cơ sở dữ liệu SQLite tại tệp ./cheating_system.db với bảng duy nhất incidents có cấu trúc như Bảng 2.2:")
    tbl_schema = [
        ["id", "VARCHAR(100)", "Khóa chính sự cố (định dạng inc_{source}_{timestamp}_{uuid})"],
        ["source_id", "VARCHAR(100)", "Định danh nguồn camera phát hiện (cam1, cam2)"],
        ["track_id", "INTEGER", "Mã số bám vết tạm thời của đối tượng qua thuật toán ByteTrack"],
        ["violation_type", "VARCHAR(50)", "Loại hành vi vi phạm: PHONE hoặc HEAD_TURNING"],
        ["confidence", "REAL", "Độ tin cậy nhận diện của mô hình (chuẩn hóa trên đoạn 0.0 - 1.0)"],
        ["level", "VARCHAR(20)", "Cấp độ cảnh báo: 'yellow' (nghi vấn) hoặc 'red' (cờ đỏ vi phạm)"],
        ["detected_at", "DATETIME", "Mốc thời gian phát hiện sự kiện (chuẩn ISO 8601 UTC)"],
        ["clip_started_at", "DATETIME", "Mốc thời gian bắt đầu đoạn clip bằng chứng (pre-roll)"],
        ["clip_ended_at", "DATETIME", "Mốc thời gian kết thúc đoạn clip bằng chứng (post-roll)"],
        ["video_path", "VARCHAR(500)", "Đường dẫn tập tin video bằng chứng MP4 (/evidence/{id}.mp4)"],
        ["snapshot_path", "VARCHAR(500)", "Đường dẫn tập tin ảnh chụp khoảnh khắc đỉnh (/evidence/{id}_snap.jpg)"],
        ["status", "VARCHAR(20)", "Trạng thái xử lý của giám thị: 'pending', 'confirmed', 'dismissed'"],
        ["proctor_notes", "TEXT", "Ghi chú bổ sung của giám thị khi xem xét sự việc"]
    ]
    add_tbl(doc, ["Tên trường", "Kiểu dữ liệu", "Mô tả ý nghĩa nghiệp vụ"], tbl_schema, caption="Bảng 2.2. Cấu trúc dữ liệu lược đồ bảng lưu trữ sự cố (incidents schema)", col_widths=[1.5, 1.3, 3.2])

    add_h3(doc, "1.7. Thiết kế giao diện người dùng")
    add_p(doc, "Giao diện bảng điều khiển giám thị được thiết kế theo phong cách Anti-Slop (tham khảo hướng dẫn oloflun/anti-slop-design):")
    add_bullet(doc, "Bảng màu chức năng trung tính: Nền tối Charcoal/Slate (bg-zinc-950, bg-zinc-900), viền 1px (border-zinc-800). Hạn chế các hiệu ứng màu sắc neon hay thẻ kính mờ glassmorphism.");
    add_bullet(doc, "Quy ước màu trạng thái: Màu Xanh Emerald (#10b981) biểu thị hệ thống bình thường / AI sẵn sàng; Màu Hổ phách Amber (#f59e0b) biểu thị trạng thái chú ý / cờ Vàng; Màu Đỏ Rose (#f43f5e) biểu thị cờ Đỏ cần xem xét.");
    add_bullet(doc, "Bố cục thông tin: Bố cục hai cột; cột trái hiển thị lưới camera kèm HUD đo đạc thông số thực tế (Acquisition FPS, AI FPS); cột phải hiển thị ma trận danh sách sự cố gần nhất giúp giám thị thẩm tra thuận tiện.");

    # =========================================================================
    # 2. CÔNG NGHỆ VÀ THƯ VIỆN SỬ DỤNG
    # =========================================================================
    add_h2(doc, "2. Công nghệ và thư viện sử dụng")
    add_p(doc, "Hệ thống sử dụng các thư viện mã nguồn mở có trong kho mã nguồn thực tế (requirements.txt, package.json và các câu lệnh import trong code), không liệt kê các thư viện ngoài phạm vi triển khai:")
    
    lib_data = [
        ["FastAPI", ">=0.110.0", "Backend Core API", "Xây dựng REST API và WebSocket, quản lý các endpoint, tuần tự hóa dữ liệu Pydantic."],
        ["Uvicorn", ">=0.28.0", "Backend Server", "Máy chủ web ASGI xử lý các kết nối HTTP và WebSocket nhị phân bất đồng bộ."],
        ["SQLAlchemy", ">=2.0.0", "Backend ORM", "Ánh xạ cơ sở dữ liệu quan hệ sang đối tượng phần mềm, quản lý phiên làm việc an toàn."],
        ["SQLite 3", "3.x (WAL)", "Cơ sở dữ liệu", "Hệ quản trị CSDL nhúng cục bộ chạy chế độ Write-Ahead Logging (WAL) hỗ trợ truy cập đồng thời."],
        ["OpenCV (cv2)", ">=4.9.0", "Xử lý ảnh / video", "Giải mã khung hình, vẽ khung nhận diện, nén ảnh JPEG và mã hóa video clip bằng chứng MP4 qua OpenH264."],
        ["NumPy", ">=1.26.0", "Toán học & Ma trận", "Xử lý mảng điểm ảnh, dữ liệu đầu vào cho mô hình AI và giải thuật lọc trung bình trượt EMA."],
        ["Ultralytics YOLO", ">=8.3.0", "AI Engine", "Nạp trọng số và thực thi suy luận mô hình nhận diện vật thể YOLO11s và ước lượng tư thế YOLO11m-pose."],
        ["PyTorch (torch)", ">=2.0.0", "Học sâu nền tảng", "Động cơ tính toán tensor nền tảng cho việc thực thi suy luận mô hình học sâu."],
        ["Pydantic", ">=2.6.0", "Ràng buộc dữ liệu", "Xác thực cấu trúc dữ liệu cho siêu dữ liệu sự cố và các yêu cầu cấu hình hệ thống."],
        ["WebSockets", ">=14.0.0", "Truyền thông mạng", "Giao thức truyền dữ liệu nhị phân hai chiều giữa giao diện người dùng và máy chủ."],
        ["Python logging", "Chuẩn thư viện", "Ghi nhật ký quan sát", "Ghi nhận dấu vết luồng xử lý và ngoại lệ chi tiết tại Terminal."],
        ["React", "19.0.1", "Frontend UI Core", "Thư viện giao diện người dùng, quản lý trạng thái hiển thị cho bảng điều khiển giám sát."],
        ["TypeScript", "~5.8.2", "Frontend Logic", "Hệ thống kiểm tra kiểu dữ liệu tĩnh, bảo đảm tính an toàn của hợp đồng dữ liệu với API backend."],
        ["Vite", "^6.2.3", "Frontend Build", "Công cụ biên dịch và máy chủ phát triển frontend hỗ trợ Hot Module Replacement (HMR)."],
        ["Tailwind CSS", "^4.1.14", "Frontend Styling", "Framework CSS tiện ích xây dựng giao diện tối giản."],
        ["Lucide React", "^0.546.0", "Biểu tượng đồ họa", "Cung cấp hệ thống biểu tượng kỹ thuật đồng bộ cho camera, đồng hồ, cảnh báo và điều khiển video."],
        ["Motion", "^12.23.24", "Hiệu ứng giao diện", "Xử lý chuyển cảnh cho các thông báo dạng toast và hộp thoại phát video bằng chứng."]
    ]
    add_tbl(doc, ["Thư viện / Công nghệ", "Phiên bản", "Thành phần sử dụng", "Vai trò và Nhiệm vụ kỹ thuật thực tế"], 
            lib_data, caption="Bảng 2.3. Danh mục đối chiếu các thư viện và công nghệ thực tế sử dụng trong hệ thống", 
            col_widths=[1.4, 0.9, 1.4, 2.3])

    # =========================================================================
    # 3. THIẾT KẾ VÀ LẬP TRÌNH PHẦN MỀM
    # =========================================================================
    add_h2(doc, "3. Thiết kế và lập trình phần mềm")
    add_p(doc, "Phần mềm được xây dựng qua sự kết hợp giữa dịch vụ Backend bằng Python và ứng dụng Frontend bằng React 19 / TypeScript:")
    
    add_h3(doc, "3.1. Hiện thực hóa Backend và Giải quyết tranh chấp tài nguyên")
    add_p(doc, "Trong quá trình xây dựng, nhóm đã giải quyết các vấn đề kỹ thuật phát sinh:")
    add_bullet(doc, "Hạn chế xung đột ghi SQLite bằng DBWriteQueue: Khi xảy ra nhiều sự kiện cờ Đỏ từ các camera, việc ghi đồng thời vào tệp SQLite có thể phát sinh lỗi database is locked. Lớp DBWriteQueue sử dụng hàng đợi queue.Queue kết hợp tiến trình nền (Worker Thread) duy nhất chịu trách nhiệm thực thi các câu lệnh INSERT/UPDATE tuần tự.", "Giải pháp 1: ");
    add_bullet(doc, "Cơ chế lập lịch công bằng Fair Round-Robin Scheduler: Khi hệ thống kết nối nhiều camera, camera có tốc độ truyền nhanh hơn có thể chiếm nhiều thời gian suy luận. Lớp FairInferenceScheduler luân chuyển lượt suy luận tuần tự qua danh sách các camera đang hoạt động nhằm phân bổ tài nguyên hợp lý.", "Giải pháp 2: ");
    add_bullet(doc, "Kiểm soát mã hóa OpenH264: Để xuất video MP4 phát được trên trình duyệt, mã nguồn tích hợp openh264-2.5.0-win64.dll và thiết lập cơ chế kiểm tra tính toàn vẹn tập tin sau khi ghi bằng hàm validate_video_file().", "Giải pháp 3: ");
    add_bullet(doc, "Quy tắc chuẩn hóa độ tin cậy Canonical Confidence Contract: Module confidence.py định nghĩa hàm normalize_confidence() tuân thủ quy tắc nghiêm ngặt: giá trị trong [0.0, 1.0] giữ nguyên; giá trị trong (1.0, 100.0] chia cho 100.0; các giá trị âm (< 0.0), lớn hơn 100.0, NaN, Inf, boolean hoặc chuỗi phi số bị TỪ CHỐI bằng ngoại lệ InvalidConfidenceError. Không thực hiện ép kiểu (clamp) giá trị âm về 0.", "Giải pháp 4: ");

    add_h3(doc, "3.2. Hiện thực hóa Frontend và Quy chuẩn Quan sát Hộp kính")
    add_p(doc, "Mã nguồn frontend được phân tách rõ ràng thành các tầng dịch vụ (Service Layer) và các thành phần hiển thị (Component Layer):")
    add_bullet(doc, "Tầng API tập trung (src/services/api.ts): Mọi yêu cầu HTTP mạng đều đi qua một cổng dịch vụ thống nhất, chuyển đổi cấu trúc dữ liệu BackendIncident sang giao diện dữ liệu nội bộ Incident, đồng thời cung cấp thông báo khi mất kết nối mạng.");
    add_bullet(doc, "Quy tắc Quan sát Hộp kính: Các tiến trình ngầm ghi nhận log với tiền tố [API], [LiveMonitor], [CameraManager], [RingBuffer], hỗ trợ việc theo dõi luồng dữ liệu tại Terminal.");

    # =========================================================================
    # 4. DANH MỤC 7 CHỨC NĂNG CỐT LÕI
    # =========================================================================
    add_h2(doc, "4. Danh mục 7 chức năng cốt lõi của sản phẩm")
    add_p(doc, "Hệ thống bao gồm 7 chức năng cốt lõi đã được triển khai trong mã nguồn và kiểm chứng chạy thực tế trên máy trạm (Bảng 2.4):")
    
    tbl_func_summary = [
        ["F-01", "Tiếp nhận và hiển thị đa luồng camera trực tiếp", "camera_manager.py, camera_source.py, Dashboard", "Đã kiểm chứng (Webcam thật & Luồng kiểm thử)"],
        ["F-02", "Phát hiện điện thoại di động trong khu vực làm bài", "ai_engine.py, phone_detector_v5.pt", "Đã kiểm chứng (Validation Split mAP=0.7858)"],
        ["F-03", "Phân tích tư thế và phát hiện hành vi quay đầu nghi vấn", "ai_engine.py, temporal_tracker.py, YOLO Pose", "Đã kiểm chứng (Heuristic 2D & Gap reset 0.75s)"],
        ["F-04", "Bộ đệm vòng và trích xuất clip bằng chứng chuẩn tốc độ 1.0x", "ring_buffer.py, openh264 DLL", "Đã kiểm chứng (422 clip MP4 tại data/evidence)"],
        ["F-05", "Quản lý và lưu trữ sự cố an toàn bằng SQLite WAL", "database.py, db_queue.py, confidence.py", "Đã kiểm chứng (cheating_system.db 439 bản ghi)"],
        ["F-06", "Thẩm tra sự cố vi phạm và phê duyệt của giám thị", "incidents.py, Dashboard, VideoEvidenceModal", "Đã kiểm chứng (API PATCH confirm/dismiss)"],
        ["F-07", "Cấu hình động độ nhạy AI và tham số ghi hình", "settings.py, AISettingsView, ai_settings.json", "Đã kiểm chứng (Runtime sync không restart)"]
    ]
    add_tbl(doc, ["Mã CN", "Tên chức năng thống nhất", "Mã nguồn chứng minh", "Trạng thái kiểm thử kỹ thuật"], 
            tbl_func_summary, caption="Bảng 2.4. Danh mục 7 chức năng cốt lõi đã triển khai và kiểm chứng (F-01 đến F-07)", 
            col_widths=[0.8, 2.4, 2.0, 1.8])

    # 4.1 Chức năng 1 (F-01)
    add_h3(doc, "4.1. Chức năng 1 (F-01): Tiếp nhận và hiển thị đa luồng camera trực tiếp")
    add_bullet(doc, "Tiếp nhận và hiển thị đa luồng camera trực tiếp (Live Multi-Camera Video Acquisition & HUD).", "1. Tên chức năng: ");
    add_bullet(doc, "Cung cấp góc nhìn bao quát không gian phòng thi từ các vị trí đặt camera (góc trước, góc bên bàn thi, góc phòng), hiển thị các chỉ số kỹ thuật vận hành.", "2. Mục đích: ");
    add_bullet(doc, "Luồng video từ webcam máy trạm, USB camera ngoài hoặc luồng video thử nghiệm.", "3. Dữ liệu đầu vào: ");
    add_bullet(doc, "CameraManager khởi tạo các nguồn camera. Mỗi khung hình được nén JPEG gửi qua WebSocket về máy chủ. HUD trên giao diện cập nhật tốc độ lấy mẫu camera (Acquisition FPS), tốc độ suy luận mô hình (AI FPS) và trạng thái kết nối.", "4. Cách hoạt động: ");
    add_bullet(doc, "Lưới hiển thị camera với nhãn định danh (Góc trước, Góc bên, Toàn cảnh), biểu tượng trạng thái RingBuffer và thanh đo FPS.", "5. Kết quả đầu ra: ");
    add_bullet(doc, "Quan sát hình ảnh các góc trong phòng; có thể chọn chế độ hiển thị (chế độ 1 Camera, 2 Camera) hoặc bật/tắt khung AI.", "6. Vai trò của giám thị: ");
    add_bullet(doc, "Nghiệm thu đồng thời hai camera vật lý: HARDWARE ACCEPTANCE PENDING (ba ô hiển thị trên giao diện kiểm thử thực chất là 01 webcam vật lý kết hợp 02 luồng kiểm thử phần mềm; không suy diễn giao diện ba ô thành hệ thống ba camera vật lý).", "7. Giới hạn hiện tại: ");
    
    img_cam_grid = r"deliverables\ha_noi\screenshots\camera_monitoring_grid.png"
    if os.path.exists(img_cam_grid):
        add_fig(doc, img_cam_grid, "Hình 2.4 (Nhóm A). Ảnh giao diện cục bộ: Lưới hiển thị chi tiết các luồng camera giám sát", width_in=5.8)

    # 4.2 Chức năng 2 (F-02)
    add_h3(doc, "4.2. Chức năng 2 (F-02): Phát hiện điện thoại di động trong khu vực làm bài")
    add_bullet(doc, "Phát hiện điện thoại di động trong khu vực làm bài (Phone Detection via YOLO11s).", "1. Tên chức năng: ");
    add_bullet(doc, "Cảnh báo khi phát hiện thiết bị điện thoại di động xuất hiện trong khu vực làm bài của thí sinh.", "2. Mục đích: ");
    add_bullet(doc, "Khung hình từ luồng camera trực tiếp.", "3. Dữ liệu đầu vào: ");
    add_bullet(doc, "Mô hình YOLO11s (trọng số phone_detector_v5.pt) quét khung hình, xác định vị trí khung bao và độ tin cậy của lớp 'phone'. Nếu vượt ngưỡng cấu hình (mặc định 0.50), hệ thống gán vào mã bám vết người gần nhất và kích hoạt cảnh báo cờ ĐỎ (PHONE).", "4. Cách hoạt động: ");
    add_bullet(doc, "Khung bao cảnh báo trên video trực tiếp, thẻ sự cố cờ đỏ trên bảng điều khiển và lệnh tạo clip gửi tới RingBuffer.", "5. Kết quả đầu ra: ");
    add_bullet(doc, "Quan sát vị trí cảnh báo, kiểm tra bối cảnh để phân biệt điện thoại với các vật dụng khác (như máy tính cầm tay, hộp bút).", "6. Vai trò của giám thị: ");
    add_bullet(doc, "Đánh giá dựa trên tập xác thực nội bộ, chưa có tập kiểm tra độc lập ngoài phòng thi thực tế; khả năng nhận diện giảm nếu thiết bị bị che khuất nhiều.", "7. Giới hạn hiện tại: ");
    
    img_multi = r"deliverables\ha_noi\screenshots\live_monitor_multi_cam.png"
    if os.path.exists(img_multi):
        add_fig(doc, img_multi, "Hình 2.5 (Nhóm A). Ảnh giao diện cục bộ: Bảng điều khiển giám sát trực tiếp ExamVision AI", width_in=5.8)

    # 4.3 Chức năng 3 (F-03)
    add_h3(doc, "4.3. Chức năng 3 (F-03): Phân tích tư thế và phát hiện hành vi quay đầu nghi vấn")
    add_bullet(doc, "Phân tích tư thế và phát hiện hành vi quay đầu nghi vấn (Pose & Head Turning Detection via YOLO11m-Pose).", "1. Tên chức năng: ");
    add_bullet(doc, "Phát hiện hành vi quay đầu sang bên kéo dài nghi vấn nhìn bài thí sinh xung quanh.", "2. Mục đích: ");
    add_bullet(doc, "17 tọa độ điểm mốc cơ thể COCO (mũi, mắt, tai, vai,...) trích xuất từ khung hình.", "3. Dữ liệu đầu vào: ");
    add_bullet(doc, "Tọa độ mốc cơ thể được theo dõi qua bộ TemporalPostureTracker (ngưỡng gián đoạn tối đa max_gap_seconds = 0,75 giây, min_samples = 3). Thuật toán hình học tính tỷ lệ bất đối xứng mũi - tai và độ lệch trục mắt - vai để cho ra điểm nghi vấn S trong đoạn [0.0, 1.0]. Nếu S ≥ 0,50, hệ thống kích hoạt cờ VÀNG; nếu duy trì liên tục ≥ 1,25 giây với khoảng gián đoạn không quá 0,75 giây, hệ thống leo thang lên cờ ĐỎ (HEAD_TURNING) và kích hoạt tạo clip. Nếu khoảng gián đoạn giữa hai khung hình nghi vấn vượt quá 0,75 giây, chuỗi theo dõi thời gian bị đặt lại (reset) về trạng thái bình thường.", "4. Cách hoạt động: ");
    add_bullet(doc, "Khung xương tư thế hiển thị trên màn hình với điểm nghi vấn; cảnh báo cờ Vàng trên HUD và sự kiện cờ Đỏ kèm clip nếu vi phạm kéo dài.", "5. Kết quả đầu ra: ");
    add_bullet(doc, "Theo dõi cảnh báo để nhắc nhở thí sinh; thẩm tra clip cờ Đỏ để xác định tính chất hành vi.", "6. Vai trò của giám thị: ");
    add_bullet(doc, "Dựa trên hình học 2D trên mặt phẳng ảnh, chưa phải phép đo góc quay 3D Euler; nhạy cảm với góc đặt camera.", "7. Giới hạn hiện tại: ");
    
    img_pose = r"deliverables\ha_noi\screenshots\pose_heuristic_diagram.png"
    if os.path.exists(img_pose):
        add_fig(doc, img_pose, "Hình 2.3 (Nhóm B). Sơ đồ kỹ thuật 17 điểm khung xương YOLO Pose và quy tắc tính điểm nghi vấn 2D", width_in=5.5)

    # 4.4 Chức năng 4 (F-04)
    add_h3(doc, "4.4. Chức năng 4 (F-04): Bộ đệm vòng và trích xuất clip bằng chứng chuẩn tốc độ 1.0x")
    add_bullet(doc, "Bộ đệm vòng và trích xuất clip bằng chứng chuẩn tốc độ 1.0x (Time-Based RingBuffer & Uniform Resampling).", "1. Tên chức năng: ");
    add_bullet(doc, "Lưu lại diễn biến video quanh thời điểm vi phạm, hỗ trợ xem lại video phát ở tốc độ thời gian thực.", "2. Mục đích: ");
    add_bullet(doc, "Chuỗi khung hình trong bộ đệm RAM và tín hiệu kích hoạt cờ Đỏ từ luồng AI.", "3. Dữ liệu đầu vào: ");
    p_f4 = doc.add_paragraph(style='List Bullet')
    p_f4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_f4.paragraph_format.line_spacing = 1.25
    p_f4.paragraph_format.space_before = Pt(0)
    p_f4.paragraph_format.space_after = Pt(3)
    p_f4.paragraph_format.left_indent = Mm(10)
    p_f4.paragraph_format.first_line_indent = Mm(-5)
    r_f4_pre = p_f4.add_run("4. Cách hoạt động: ")
    format_run(r_f4_pre, size_pt=13, bold=True)
    r_f4_1 = p_f4.add_run("RingBuffer duy trì hàng đợi trong RAM lưu các cặp (timestamp, frame). Khi có cờ Đỏ tại mốc ")
    format_run(r_f4_1, size_pt=13)
    append_t_event(p_f4, size_pt=13)
    r_f4_2 = p_f4.add_run(", tiến trình trích xuất cửa sổ pre-roll (5,0 giây trước) và thu thêm post-roll (10,0 giây sau). Chuỗi khung hình được lấy mẫu lại theo lưới thời gian đồng đều (Uniform Time-Grid Nearest-Neighbor Resampling) theo tần số danh định 15 FPS rồi nén thành tập tin MP4 bằng OpenH264 (hoặc avc1/mp4v). Phương pháp này giúp clip MP4 phát lại ở tốc độ tự nhiên gần 1.0x mà không bị tua nhanh khi camera gửi khung hình ngắt quãng.")
    format_run(r_f4_2, size_pt=13)
    add_bullet(doc, "Tập tin video bằng chứng MP4 hoàn chỉnh (thời lượng ~15,0 giây) lưu tại ./data/evidence/ và ảnh chụp snapshot khoảnh khắc vi phạm.", "5. Kết quả đầu ra: ");
    add_bullet(doc, "Không cần bấm nút ghi thủ công; hệ thống tự động ghi nhận khi có sự kiện cờ Đỏ.", "6. Vai trò của giám thị: ");
    add_bullet(doc, "Yêu cầu máy trạm có dung lượng RAM phù hợp để duy trì bộ đệm trượt cho các luồng video.", "7. Giới hạn hiện tại: ");

    # 4.5 Chức năng 5 (F-05)
    add_h3(doc, "4.5. Chức năng 5 (F-05): Quản lý và lưu trữ sự cố an toàn bằng SQLite WAL")
    add_bullet(doc, "Quản lý và lưu trữ sự cố an toàn bằng SQLite WAL (Safe Incident Logging & DB Queue).", "1. Tên chức năng: ");
    add_bullet(doc, "Lưu trữ bền vững siêu dữ liệu sự cố vi phạm vào cơ sở dữ liệu cục bộ, hạn chế xung đột ghi đồng thời.", "2. Mục đích: ");
    add_bullet(doc, "Đối tượng sự cố (ID, camera, track_id, loại vi phạm, confidence chuẩn hóa, mốc thời gian, đường dẫn video/ảnh).", "3. Dữ liệu đầu vào: ");
    add_bullet(doc, "Hàng đợi DBWriteQueue nhận sự cố và thực thi ghi tuần tự vào SQLite chế độ WAL (Write-Ahead Logging). Hàm normalize_confidence() chuẩn hóa điểm số về đoạn [0.0, 1.0], từ chối các giá trị âm hoặc sai định dạng bằng ngoại lệ InvalidConfidenceError (không ép kiểu về 0).", "4. Cách hoạt động: ");
    add_bullet(doc, "Bản ghi sự cố được lưu an toàn trong bảng incidents tại tệp cheating_system.db (hiện có 439 bản ghi, trong đó 416 bản ghi có đường dẫn video, 382 clip tham chiếu tồn tại hợp lệ trên đĩa, tổng cộng 422 tệp MP4 trong data/evidence/).", "5. Kết quả đầu ra: ");
    add_bullet(doc, "Tra cứu lịch sử sự cố theo bộ lọc camera, loại vi phạm và trạng thái xử lý.", "6. Vai trò của giám thị: ");
    add_bullet(doc, "Cơ sở dữ liệu lưu cục bộ trên máy trạm; chưa đồng bộ qua mạng phân tán liên phòng thi.", "7. Giới hạn hiện tại: ");

    # 4.6 Chức năng 6 (F-06)
    add_h3(doc, "4.6. Chức năng 6 (F-06): Thẩm tra sự cố vi phạm và phê duyệt của giám thị")
    add_bullet(doc, "Thẩm tra sự cố vi phạm và phê duyệt của giám thị (Incident Review Matrix & Video Playback Modal).", "1. Tên chức năng: ");
    add_bullet(doc, "Cung cấp giao diện để giám thị kiểm tra chi tiết cảnh báo, xem lại clip video và đưa ra quyết định xử lý.", "2. Mục đích: ");
    add_bullet(doc, "Danh sách bản ghi sự cố từ SQLite và tập tin video MP4 từ thư mục /evidence/.", "3. Dữ liệu đầu vào: ");
    add_bullet(doc, "Cột bên phải bảng điều khiển hiển thị danh sách sự cố. Giám thị nhấp 'Xem Clip' để mở hộp thoại phát video bằng chứng MP4 (có tính năng lặp Loop). Giám thị có thể bấm 'Xác nhận' (confirmed) để ghi nhận hoặc bấm 'Bỏ qua' (dismissed) để phân loại cảnh báo không vi phạm.", "4. Cách hoạt động: ");
    add_bullet(doc, "Trạng thái bản ghi được cập nhật qua API PATCH /api/incidents/{id}/confirm; thông báo toast hiển thị góc màn hình.", "5. Kết quả đầu ra: ");
    add_bullet(doc, "Đóng vai trò người thẩm định quyết định; AI chỉ cung cấp tín hiệu và chứng cứ hỗ trợ.", "6. Vai trò của giám thị: ");
    add_bullet(doc, "Phê duyệt từng sự cố trên máy trạm cục bộ; chưa có tính năng đồng bộ quyết định liên phòng.", "7. Giới hạn hiện tại: ");
    
    img_inc_panel = r"deliverables\ha_noi\screenshots\incident_matrix_panel.png"
    if os.path.exists(img_inc_panel):
        add_fig(doc, img_inc_panel, "Hình 2.6 (Nhóm A). Ảnh giao diện cục bộ: Bảng danh sách sự cố vi phạm cờ đỏ và nút phê duyệt", width_in=3.8)
        
    img_modal = r"deliverables\ha_noi\screenshots\video_evidence_modal.png"
    if os.path.exists(img_modal):
        add_fig(doc, img_modal, "Hình 2.7 (Nhóm A). Ảnh giao diện cục bộ: Hộp thoại phát lại video bằng chứng MP4 đã nội suy chuẩn 1.0x", width_in=5.8)

    # 4.7 Chức năng 7 (F-07)
    add_h3(doc, "4.7. Chức năng 7 (F-07): Cấu hình động độ nhạy AI và tham số ghi hình bằng chứng")
    add_bullet(doc, "Cấu hình động độ nhạy AI và tham số ghi hình bằng chứng (Dynamic AI Sensitivity & RingBuffer Configuration View).", "1. Tên chức năng: ");
    add_bullet(doc, "Cho phép giám thị điều chỉnh độ nhạy phát hiện của mô hình và độ dài video bằng chứng cho phù hợp với điều kiện phòng thi.", "2. Mục đích: ");
    add_bullet(doc, "Giá trị các thanh trượt tham số do người dùng điều chỉnh trên giao diện web.", "3. Dữ liệu đầu vào: ");
    add_bullet(doc, "Khi người dùng thay đổi tham số (Ngưỡng điện thoại, Thời gian leo thang cờ đỏ, Ngưỡng nghi vấn tư thế, Giãn cách cooldown, Thời lượng Pre-roll, Thời lượng Post-roll) và bấm 'Lưu Cấu Hình', frontend gửi yêu cầu PUT /api/settings. Backend cập nhật trực tiếp biến runtime và lưu bền vững vào tệp data/ai_settings.json mà không cần khởi động lại dịch vụ.", "4. Cách hoạt động: ");
    add_bullet(doc, "Thuật toán AI và bộ đệm RingBuffer áp dụng ngay tham số mới cho các khung hình tiếp theo.", "5. Kết quả đầu ra: ");
    add_bullet(doc, "Tinh chỉnh mức độ cảnh báo tùy theo yêu cầu của ca thi.", "6. Vai trò của giám thị: ");
    add_bullet(doc, "Cần người vận hành hiểu rõ ý nghĩa tham số để tránh đặt ngưỡng quá nhạy làm tăng cảnh báo cờ Vàng.", "7. Giới hạn hiện tại: ");
    
    img_settings = r"deliverables\ha_noi\screenshots\ai_settings_view.png"
    if os.path.exists(img_settings):
        add_fig(doc, img_settings, "Hình 2.8 (Nhóm A). Ảnh giao diện cục bộ: Màn hình cấu hình động độ nhạy AI và tham số RingBuffer", width_in=5.8)

    # 5 & 6
    add_h2(doc, "5. Nguyên lý hoạt động tổng thể của hệ thống")
    add_p(doc, "Quy trình vận hành của Hệ thống hỗ trợ giám sát phòng thi diễn ra qua 5 bước tuần tự:")
    add_bullet(doc, "Khởi động và Thiết lập kết nối: Khởi động hệ thống qua start.bat. Máy chủ FastAPI và ứng dụng React kích hoạt. Người dùng truy cập bảng điều khiển tại http://localhost:3000, kiểm tra trạng thái 'AI SẴN SÀNG' trên thanh điều hướng và quan sát lưới camera.", "Bước 1: ");
    add_bullet(doc, "Thu nhận luồng hình ảnh: Trình duyệt mở các luồng camera, thu nhận khung hình ở tốc độ mục tiêu ~15 FPS, đóng gói nhị phân gửi về máy chủ để nạp vào RingBuffer.", "Bước 2: ");
    add_bullet(doc, "Suy luận AI song song và Đánh giá quy tắc: Luồng AI bốc khung hình mới nhất, chạy mô hình YOLO11s và YOLO11m-pose. Điểm số nhận diện điện thoại và độ bất đối xứng tư thế được tính toán. Nếu phát hiện vi phạm thỏa mãn điều kiện thời gian, cờ ĐỎ được kích hoạt.", "Bước 3: ");
    add_bullet(doc, "Đóng gói video bằng chứng và Ghi cơ sở dữ liệu: RingBuffer trích xuất cửa sổ 5s trước và chờ đủ 10s sau, nội suy resampling chuẩn tốc độ 1.0x và xuất tệp video MP4. Siêu dữ liệu sự cố được đẩy vào hàng đợi DBWriteQueue để lưu vào SQLite cheating_system.db.", "Bước 4: ");
    add_bullet(doc, "Thẩm tra và Ra quyết định của Giám thị: Thẻ sự cố xuất hiện trên bảng điều khiển. Giám thị mở clip video bằng chứng xem lại bối cảnh. Sau khi kiểm chứng, giám thị bấm nút 'Xác nhận' để ghi nhận hoặc bấm 'Bỏ qua' nếu nhận thấy thí sinh chỉ có cử động tự nhiên.", "Bước 5: ");

    add_h2(doc, "6. Giới hạn phiên bản hiện tại")
    add_p(doc, "Nhóm nghiên cứu ghi nhận rõ các giới hạn của phiên bản thử nghiệm hiện tại:")
    add_bullet(doc, "Hệ thống hỗ trợ giám sát trong phạm vi một phòng thi cục bộ (Local Exam Room), chưa triển khai mạng giám sát tập trung nhiều phòng thi.");
    add_bullet(doc, "Chỉ nhận diện 2 lớp hành vi cụ thể (PHONE và HEAD_TURNING), chưa phát hiện các hành vi khác như phao giấy nhỏ dưới ngăn bàn.");
    add_bullet(doc, "Chưa tích hợp phân tích âm thanh trong phòng thi.");

    doc.add_page_break()

    # =========================================================================
    # PHẦN III: QUÁ TRÌNH THỬ NGHIỆM VÀ KẾT QUẢ ĐẠT ĐƯỢC
    # =========================================================================
    add_h1(doc, "PHẦN III: QUÁ TRÌNH THỬ NGHIỆM VÀ KẾT QUẢ ĐẠT ĐƯỢC", space_before=10, space_after=10)
    
    add_h2(doc, "1. Phương pháp thử nghiệm")
    add_p(doc, "Công tác thử nghiệm được tiến hành kết hợp giữa kiểm thử tự động (Automated Testing) và đo lường thực nghiệm tải thời gian thực (Empirical Real-Time Benchmarking):")
    add_bullet(doc, "Kiểm thử đơn vị và hợp đồng dữ liệu: Sử dụng thư viện unittest của Python để kiểm tra bất biến của RingBuffer, hợp đồng độ tin cậy confidence và hàng đợi DBWriteQueue.");
    add_bullet(doc, "Kiểm tra kiểu tĩnh và đóng gói Frontend: Sử dụng trình biên dịch TypeScript (tsc --noEmit) để kiểm tra tính tương thích kiểu dữ liệu và thực hiện đóng gói sản phẩm (npm run build).");
    add_bullet(doc, "Thử nghiệm tải và thông lượng thời gian thực: Thực hiện các phiên đo liên tục trong các điều kiện cấu hình (độ phân giải 640x480 và 1920x1080) để đo đạc FPS thu nhận, FPS suy luận, độ trễ và mức tiêu hao bộ nhớ.");

    add_h2(doc, "2. Thử nghiệm từng thành phần")
    
    add_h3(doc, "2.1. Tập dữ liệu và Huấn luyện mô hình phát hiện điện thoại")
    add_p(doc, "Mô hình phát hiện điện thoại được xây dựng dựa trên kiến trúc YOLO11s. Dữ liệu huấn luyện lịch sử (phone_merged) gồm 2.961 ảnh và 3.706 khung bao của một lớp 'phone', tổng hợp từ ba nguồn Roboflow có giấy phép CC BY 4.0 [8]–[10]. Phân bố tập dữ liệu được trình bày tại Bảng 3.1:")
    
    tbl_ds = [
        ["Tập huấn luyện (Train)", "2.434", "3.042", "82,2%"],
        ["Tập xác thực (Validation)", "382", "490", "12,9%"],
        ["Tập kiểm tra nội bộ (Internal Test)", "145", "174", "4,9%"],
        ["Tổng cộng toàn bộ tập dữ liệu", "2.961", "3.706", "100,0%"]
    ]
    add_tbl(doc, ["Phần tập dữ liệu", "Số lượng ảnh", "Số khung bao (BBoxes)", "Tỷ lệ ảnh"], tbl_ds, 
            caption="Bảng 3.1. Phân bố tập dữ liệu huấn luyện lịch sử phone_merged", col_widths=[2.0, 1.2, 1.6, 1.2])

    add_p(doc, "Quá trình huấn luyện mô hình được thực hiện với các thông số cấu hình như Bảng 3.2:")
    tbl_hyp = [
        ["Kiến trúc mô hình mạng", "YOLO11s (Ultralytics)", "Một lớp phát hiện đối tượng 'phone'"],
        ["Số epoch huấn luyện", "60 epochs", "Ghi nhận tiến trình huấn luyện 60 epochs"],
        ["Kích thước ảnh đầu vào (imgsz)", "960 x 960 pixels", "Hỗ trợ phát hiện vật thể nhỏ trong khung hình"],
        ["Kích thước batch (Batch size)", "6", "Phù hợp với bộ nhớ phần cứng huấn luyện"],
        ["Thuật toán tối ưu (Optimizer)", "Auto (SGD / AdamW)", "Tự động điều chỉnh suy giảm trọng số"],
        ["Hạt giống ngẫu nhiên (Seed)", "0 (deterministic = True)", "Đảm bảo tính tái lập kết quả"]
    ]
    add_tbl(doc, ["Tham số huấn luyện", "Giá trị thiết lập", "Ghi chú kỹ thuật"], tbl_hyp, 
            caption="Bảng 3.2. Thông số cấu hình huấn luyện mô hình nhận diện điện thoại", col_widths=[2.2, 1.8, 2.0])

    add_p(doc, "Báo cáo phiên bản trước ghi nhận mAP@0.5 = 0,7858 trên tập validation nội bộ. Trong lần rà soát hồ sơ này, nhóm chưa tìm thấy log đánh giá hoặc tệp kết quả huấn luyện gốc để tái lập độc lập chỉ số; do đó số liệu được giữ dưới dạng kết quả kế thừa có dẫn nguồn, không phải kết quả được vòng kiểm toán hiện tại xác nhận lại. Các chỉ số được ghi nhận tại Bảng 3.3:")
    tbl_train_res = [
        ["Độ chính xác (Precision) cao nhất", "0,8040 (80,40%)", "Ghi nhận tại Epoch 53"],
        ["Độ bao phủ (Recall) cao nhất", "0,7041 (70,41%)", "Ghi nhận tại Epoch 59"],
        ["mAP@0.5 cao nhất", "0,7858 (78,58%)", "Ghi nhận tại Epoch 55"],
        ["mAP@0.5 tại epoch cuối", "0,7692 (76,92%)", "Ghi nhận tại Epoch 60"],
        ["mAP@0.5:0.95 tại epoch cuối", "0,4716 (47,16%)", "Ghi nhận tại Epoch 60"]
    ]
    add_tbl(doc, ["Chỉ số đánh giá", "Giá trị đạt được", "Thời điểm ghi nhận trong quá trình huấn luyện"], tbl_train_res, 
            caption="Bảng 3.3. Kết quả huấn luyện mô hình YOLO11s trên tập xác thực nội bộ", col_widths=[2.5, 1.5, 2.0])

    add_h3(doc, "2.2. Thử nghiệm thuật toán phát hiện quay đầu nghi vấn")
    add_p(doc, "Thuật toán phát hiện quay đầu bằng mô hình YOLO11m-pose kết hợp bộ theo dõi chuỗi thời gian (ngưỡng gián đoạn max_gap_seconds = 0.75s) được kiểm thử qua các chuỗi video tình huống mô phỏng. Kết quả ghi nhận:")
    add_bullet(doc, "Khi thí sinh cử động đầu nhẹ trong lúc làm bài, điểm nghi vấn S dao động trong khoảng 0.15 - 0.35, nằm dưới ngưỡng cảnh báo.");
    add_bullet(doc, "Khi thí sinh quay mặt sang bên (góc lệch cổ lớn), điểm S vượt ngưỡng 0.50. Nếu chỉ quay đầu trong thời gian ngắn (< 1.25s) rồi quay lại, hệ thống hiển thị cờ Vàng trên HUD mà không kích hoạt tạo clip.");
    add_bullet(doc, "Khi hành vi quay đầu duy trì liên tục từ 1.25 giây trở lên, cờ Đỏ được kích hoạt và clip bằng chứng được tạo.");

    add_h2(doc, "3. Thử nghiệm tổng thể hệ thống")
    
    add_h3(doc, "3.1. Phiên đo thông lượng thời gian thực 125,1 giây")
    add_p(doc, "Nhóm nghiên cứu đã thực hiện phép đo hiệu năng trong 125,1 giây hoạt động liên tục trên máy trạm cấu hình CPU, nguồn video có tốc độ mục tiêu 15 FPS. Cần phân biệt rõ: tốc độ thu nhận khung hình của camera (Capture rate) đạt 15,60 khung hình/giây (1.952 khung hình / 125,1s); tỷ lệ nghịch của độ trễ xử lý (Processing-rate ratio) là 1000 ms / 360,4 ms ≈ 2,77 lượt xử lý/giây tính toán (inferences/compute-second), không phải thông lượng quan sát theo thời gian thực wall-clock của toàn hệ thống; số kết quả suy luận AI nhận về trên thực tế là 354 kết quả trong 125,1 giây (≈ 2,83 kết quả/giây wall-clock). Kết quả chi tiết được tổng hợp tại Bảng 3.4:")
    tbl_bench = [
        ["Thời lượng phiên đo liên tục (Wall-clock)", "125,1 giây", "Thời lượng phiên vận hành đo đạc thực tế"],
        ["Số khung hình máy khách gửi (Sent Frames)", "1.952 khung hình", "Tốc độ thu nhận trung bình đạt 15,60 FPS"],
        ["Số khung hình máy chủ nhận (Recv Frames)", "1.949 khung hình", "Tốc độ nạp vào hệ thống đạt 15,58 FPS"],
        ["Tốc độ thu nhận tức thời trung bình (Acq FPS)", "15,88 FPS", "Duy trì bám sát tốc độ mục tiêu 15 FPS"],
        ["Số kết quả suy luận AI nhận về (Results)", "354 kết quả", "Thông lượng quan sát đạt ~2,83 kết quả/giây wall-clock"],
        ["Số khung hình thay thế chủ đích (Superseded)", "1.662 khung hình", "Tỷ lệ thay thế đạt 85,3% số khung nạp vào bộ đệm đơn"],
        ["Độ trễ xử lý suy luận trung bình (Latency)", "360,4 ms", "Tương đương 2,77 lượt xử lý trên mỗi giây tính toán (compute-sec)"],
        ["Quy trình tạo video bằng chứng (Clip Trigger)", "Hoạt động", "Đã tạo các tệp MP4 bằng chứng trong phiên thử nghiệm"]
    ]
    add_tbl(doc, ["Chỉ số thông lượng", "Số liệu thực nghiệm", "Nhận xét phân tích kỹ thuật"], tbl_bench, 
            caption="Bảng 3.4. Kết quả đo thông lượng phiên thực nghiệm 125,1 giây", col_widths=[2.5, 1.5, 2.0])

    add_h3(doc, "3.2. Kết quả kiểm thử tự động toàn diện (Aggregate Test Suite)")
    add_p(doc, "Hệ thống đã trải qua quy trình kiểm thử tự động trong đợt nghiệm thu phần mềm Sprint 3.2B-R2, ghi nhận kết quả tại Bảng 3.5:")
    tbl_test_suite = [
        ["Kiểm thử đơn vị Backend (Aggregate Suite)", "83 bài test", "83/83 PASS (Exit code 0)", "Kiểm tra pipeline, database queue, camera manager, confidence contract."],
        ["Kiểm thử toán học Evaluation Harness", "22 bài test", "22/22 PASS (Exit code 0)", "Kiểm tra công thức tính điểm và ma trận nhầm lẫn."],
        ["Kiểm thử giao tiếp Preview WebSocket", "8 bài test", "8/8 PASS (Exit code 0)", "Kiểm tra tính toàn vẹn của luồng truyền nhị phân và bất biến bộ đệm."],
        ["Kiểm tra kiểu tĩnh Frontend TypeScript", "Toàn bộ dự án", "PASS (Exit code 0)", "Lệnh npx tsc --noEmit không phát hiện lỗi xung đột kiểu dữ liệu."],
        ["Kiểm thử hợp đồng Frontend Dual-Camera", "15 bài test", "15/15 PASS (Exit code 0)", "Kiểm tra logic nhận diện và điều phối đa nguồn video phía máy khách."],
        ["Đóng gói sản phẩm Vite Production Build", "Toàn bộ bundle", "PASS (Exit code 0)", "Biên dịch thành công gói triển khai tối ưu hóa trong thư mục /dist/."]
    ]
    add_tbl(doc, ["Hạng mục kiểm thử", "Số lượng / Phạm vi", "Trạng thái nghiệm thu", "Ý nghĩa kỹ thuật"], tbl_test_suite, 
            caption="Bảng 3.5. Kết quả thực thi các bộ kiểm thử tự động hệ thống", col_widths=[1.8, 1.1, 1.3, 1.8])

    add_h3(doc, "3.3. Thử nghiệm độ ổn định bộ nhớ đa camera (62 giây)")
    add_p(doc, "Để kiểm tra độ ổn định bộ nhớ khi vận hành đa camera, nhóm thực hiện 2 kịch bản đo tải liên tục trong 62,0 giây:")
    tbl_mem_bench = [
        ["Kịch bản A: Độ phân giải 640x480 @ 15 FPS", "Đạt 15,0 FPS ổn định", "Mức chiếm dụng RAM tăng trong khoảng 15s đầu (lấp đầy RingBuffer) sau đó duy trì ổn định."],
        ["Kịch bản B: Độ phân giải 1920x1080 @ 15 FPS", "Đạt 15,0 FPS ổn định", "Bộ đệm đạt trạng thái cân bằng động ở mốc xấp xỉ 380 MB, không ghi nhận hiện tượng tràn bộ nhớ."]
    ]
    add_tbl(doc, ["Kịch bản đo tải", "Thông lượng ghi nhận", "Đánh giá độ ổn định tài nguyên RAM"], tbl_mem_bench, 
            caption="Bảng 3.6. Kết quả đo tải bộ nhớ kịch bản đa camera (Scenario A & B)", col_widths=[2.2, 1.5, 2.3])

    add_h2(doc, "4. Kết quả ghi nhận")
    add_p(doc, "Từ các số liệu thực nghiệm trên, nhóm nghiên cứu rút ra những kết quả kỹ thuật chính:")
    add_bullet(doc, "Khả năng phân tách luồng: Trong điều kiện độ trễ suy luận AI trên CPU đạt 360,4 ms (tương đương 2,77 lượt xử lý/giây tính toán), tốc độ thu nhận khung hình vẫn duy trì ở mức 15,60 FPS. Việc thay thế các khung hình cũ trong bộ đệm một phần tử hỗ trợ luồng AI bám sát thời gian thực.");
    add_bullet(doc, "Quy trình tạo chứng cứ: Các đoạn clip MP4 được tạo ra trong các phiên thử nghiệm có độ dài danh định xấp xỉ 15.0 giây, phát lại ở tốc độ tự nhiên gần 1.0x qua tái lấy mẫu lưới thời gian đều, ghi nhận bối cảnh trước và sau sự kiện.");

    add_h2(doc, "5. Hạn chế của kết quả và giới hạn diễn giải khoa học")
    add_p(doc, "Nhóm nghiên cứu làm rõ các giới hạn diễn giải của số liệu:")
    add_bullet(doc, "Báo cáo phiên bản trước ghi nhận mAP@0.5 = 0,7858 trên tập validation nội bộ. Trong lần rà soát hồ sơ này, nhóm chưa tìm thấy log đánh giá hoặc tệp kết quả huấn luyện gốc để tái lập độc lập chỉ số; do đó số liệu được giữ dưới dạng kết quả kế thừa có dẫn nguồn, không phải kết quả được vòng kiểm toán hiện tại xác nhận lại.");
    add_bullet(doc, "Thuật toán quay đầu là quy tắc hình học 2D dựa trên tọa độ khung xương YOLO Pose. Nhóm chưa có tập dữ liệu video phòng thi thực tế được gán nhãn thời điểm bắt đầu và kết thúc (Temporal Ground Truth) để tính toán các chỉ số Event Precision, Event Recall và Event F1.");
    add_bullet(doc, "Về phần cứng: Nghiệm thu hiện tại ở mức Software / Synthetic Acceptance. Nhóm đã đặt mua 2 webcam ngoài chuẩn EYD PC02; nghiệm thu đồng thời hai camera vật lý: HARDWARE ACCEPTANCE PENDING (ba ô hiển thị trên giao diện kiểm thử thực chất là 01 webcam vật lý kết hợp 02 luồng kiểm thử phần mềm; không suy diễn giao diện ba ô thành hệ thống ba camera vật lý).");

    add_h2(doc, "6. Những cải tiến đã thực hiện sau thử nghiệm")
    add_p(doc, "Qua các chu kỳ thực nghiệm, nhóm đã thực hiện 5 cải tiến kỹ thuật:")
    add_bullet(doc, "Phân tách luồng ghi hình khỏi luồng suy luận AI: Áp dụng mô hình Dual-Stream, hạn chế hiện tượng dồn ứ khung hình.");
    add_bullet(doc, "Tái lấy mẫu lưới thời gian đều (Uniform Time-Grid Resampling) cho RingBuffer: Khắc phục hiện tượng video bị tua nhanh khi camera gửi khung hình ngắt quãng mà không cần nội suy khung hình quang học.");
    add_bullet(doc, "Chuẩn hóa thang đo độ tin cậy về đoạn [0.0, 1.0]: Viết lại module confidence.py để chuẩn hóa giá trị đầu vào, từ chối giá trị âm và giá trị sai quy cách.");
    add_bullet(doc, "Bộ lập lịch công bằng Fair Round-Robin Scheduler: Điều phối lượt suy luận tuần tự khi kết nối nhiều camera.");
    add_bullet(doc, "Tối giản hóa giao diện: Loại bỏ thanh điều hướng phụ và các nút lập biên bản tự động không phù hợp thực tế, tập trung màn hình vào khu vực thẩm tra video bằng chứng.");

    doc.add_page_break()

    # =========================================================================
    # PHẦN IV: KẾT LUẬN VÀ KIẾN NGHỊ
    # =========================================================================
    add_h1(doc, "PHẦN IV: KẾT LUẬN VÀ KIẾN NGHỊ", space_before=10, space_after=10)
    
    add_h2(doc, "1. Kết luận")
    add_p(doc, "Nhóm nghiên cứu đã xây dựng nguyên mẫu phần mềm “Hệ thống hỗ trợ giám sát phòng thi bằng thị giác máy tính và trích xuất video bằng chứng”.")
    add_p(doc, "Nguyên mẫu đáp ứng các mục tiêu kỹ thuật bước đầu: tiếp nhận video từ camera ở tốc độ khoảng 15 FPS; phát hiện hai dấu hiệu nghi vấn (điện thoại và quay đầu kéo dài ≥ 1,25 giây); phân tách luồng xử lý để hạn chế độ trễ tích lũy; tự động trích xuất clip bằng chứng MP4 danh định 15 giây (chứa bối cảnh trước và sau sự kiện) phát ở tốc độ tự nhiên gần 1.0x; và lưu trữ sự cố trong SQLite WAL để giám thị xem xét trên giao diện trực quan.")
    add_p(doc, "Hệ thống tuân thủ nguyên lý con người làm trung tâm (Human-in-the-Loop): AI không thay thế con người, không định danh thí sinh và không tự ý đưa ra quyết định kỷ luật. Các cảnh báo và đoạn clip ngắn đóng vai trò chứng cứ hỗ trợ giám thị xem xét tình huống khách quan hơn.")

    add_h2(doc, "2. Đóng góp kỹ thuật và xã hội của đề tài")
    add_bullet(doc, "Về kỹ thuật: Đề xuất phương án kết hợp giữa RingBuffer và Single-slot Buffer nhằm dung hòa giữa tốc độ camera nhanh và tốc độ suy luận AI chậm trên máy trạm thông thường; giải pháp resampling hỗ trợ video xuất ra đúng tốc độ thực.", "Về kỹ thuật: ");
    add_bullet(doc, "Về kinh tế: Phần mềm chạy trên máy vi tính kết hợp webcam phổ thông, không đòi hỏi đầu tư máy chủ chuyên dụng, có tiềm năng ứng dụng linh hoạt.", "Về kinh tế: ");
    add_bullet(doc, "Về xã hội: Hỗ trợ giám thị giảm bớt căng thẳng chú ý kéo dài, góp phần nâng cao tính nghiêm minh và công bằng trong thi cử.", "Về xã hội: ");

    add_h2(doc, "3. Kiến nghị")
    add_p(doc, "Để hoàn thiện hệ thống trước khi đưa vào ứng dụng thực tế, nhóm nghiên cứu kiến nghị:")
    add_bullet(doc, "Thử nghiệm hệ thống trong các kỳ thi thử, thi khảo sát chất lượng nhằm thu thập thêm dữ liệu thực tế và đánh giá phản hồi của cán bộ coi thi.");
    add_bullet(doc, "Xây dựng quy định về quản lý tệp video bằng chứng: thời hạn lưu trữ, phân quyền truy cập và quy trình xóa dữ liệu định kỳ để bảo đảm quyền riêng tư của học sinh.");

    # =========================================================================
    # PHẦN V: HƯỚNG PHÁT TRIỂN ĐỀ TÀI
    # =========================================================================
    add_h1(doc, "PHẦN V: HƯỚNG PHÁT TRIỂN ĐỀ TÀI", space_before=10, space_after=10)
    add_p(doc, "Các nội dung nghiên cứu định hướng trong giai đoạn tiếp theo gồm:")
    add_bullet(doc, "Thu thập tập dữ liệu kiểm thử độc lập (Independent Test Set): Ghi hình các tình huống thực tế tại phòng học với các điều kiện ánh sáng và góc đặt camera khác nhau để đánh giá mô hình phát hiện điện thoại.");
    add_bullet(doc, "Gán nhãn mốc thời gian sự kiện quay đầu (Temporal Annotation): Xây dựng dữ liệu gán nhãn khung thời gian bắt đầu và kết thúc của hành vi để tính toán các chỉ số Event Precision, Event Recall và Event F1.");
    add_bullet(doc, "Nghiên cứu mô hình ước lượng góc quay đầu 3D (3D Head Pose Estimation): Khảo sát phương pháp ước lượng góc Euler trong không gian 3 chiều nhằm nâng cao độ chính xác so với hình học 2D.");
    add_bullet(doc, "Khảo sát phát hiện các hành vi phức tạp khác: Nghiên cứu nhận diện hành vi trao đổi vật dụng bằng mô hình tương tác tay - vật thể; phát hiện thí sinh rời vị trí bàn thi.");
    add_bullet(doc, "Định hướng mở rộng kiến trúc mạng giám sát liên phòng thi (Multi-Room Monitoring): Nghiên cứu mô hình quản lý tập trung tín hiệu cảnh báo từ nhiều phòng thi phục vụ hội đồng thi.");

    # =========================================================================
    # PHẦN VI: TÀI LIỆU THAM KHẢO
    # =========================================================================
    add_h1(doc, "PHẦN VI: TÀI LIỆU THAM KHẢO", space_before=10, space_after=10)
    refs = [
        "[1] Mackworth, N. H. (1948). The breakdown of vigilance during prolonged visual search. Quarterly Journal of Experimental Psychology, 1(1), 6–21. https://doi.org/10.1080/17470214808416738",
        "[2] Warm, J. S., Parasuraman, R., & Matthews, G. (2008). Vigilance requires hard mental work and is stressful. Human Factors, 50(3), 433–441. https://doi.org/10.1518/001872008X312152",
        "[3] Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). You Only Look Once: Unified, Real-Time Object Detection. IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 779–788.",
        "[4] Jocher, G., & Qiu, J. (2024). Ultralytics YOLO11 software and documentation. https://docs.ultralytics.com/models/yolo11/",
        "[5] Lin, T.-Y., Maire, M., Belongie, S., Hays, J., Perona, P., Ramanan, D., Dollár, P., & Zitnick, C. L. (2014). Microsoft COCO: Common Objects in Context. European Conference on Computer Vision (ECCV), 740–755.",
        "[6] Zhang, Y., Sun, P., Jiang, Y., Yu, D., Weng, F., Yuan, Z., Luo, P., Liu, W., & Wang, X. (2022). ByteTrack: Multi-Object Tracking by Associating Every Detection Box. European Conference on Computer Vision (ECCV), 1–21.",
        "[7] SQLite Consortium. (2026). Write-Ahead Logging in SQLite 3. https://www.sqlite.org/wal.html",
        "[8] Roboflow user du-tran. (2024). mobilephone v3 dataset. CC BY 4.0. https://universe.roboflow.com/du-tran/mobilephone-f4v6n",
        "[9] Roboflow user du-tran. (2024). mobilephone2 v1 dataset. CC BY 4.0. https://universe.roboflow.com/du-tran/mobilephone2",
        "[10] Roboflow user du-tran. (2024). mobilephone3 v1 dataset. CC BY 4.0. https://universe.roboflow.com/du-tran/mobilephone3",
        "[11] FastAPI Documentation. (2026). High performance, easy to learn, fast to code, ready for production. https://fastapi.tiangolo.com/",
        "[12] React Documentation. (2026). React 19: The library for web and native user interfaces. https://react.dev/"
    ]
    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_ref.paragraph_format.line_spacing = 1.15
        p_ref.paragraph_format.space_before = Pt(2)
        p_ref.paragraph_format.space_after = Pt(4)
        p_ref.paragraph_format.left_indent = Mm(10)
        p_ref.paragraph_format.first_line_indent = Mm(-10)
        r_ref = p_ref.add_run(ref)
        format_run(r_ref, size_pt=11.5)

    # =========================================================================
    # PHỤ LỤC: MA TRẬN MINH CHỨNG VÀ TRUY VẾT DỮ LIỆU
    # =========================================================================
    doc.add_page_break()
    add_h1(doc, "PHỤ LỤC: MA TRẬN MINH CHỨNG VÀ TRUY VẾT DỮ LIỆU", space_before=10, space_after=10)
    add_p(doc, "Bảng phụ lục đối chiếu 7 chức năng cốt lõi và các kết quả kỹ thuật trong báo cáo với bằng chứng thực tế tại mã nguồn, lịch sử cam kết Git và nhật ký kiểm thử:")
    
    audit_matrix = [
        ["F-01", "Tiếp nhận và hiển thị đa luồng camera trực tiếp", "Mã nguồn camera_manager.py, camera_source.py; ảnh giao diện live_monitor_multi_cam.png", "ĐÃ XÁC MINH (Code & UI)"],
        ["F-02", "Phát hiện điện thoại di động trong khu vực làm bài", "Mã nguồn ai_engine.py, trọng số phone_detector_v5.pt; số liệu kế thừa có dẫn nguồn mAP=0.7858", "ĐÃ XÁC MINH (Code & Weights)"],
        ["F-03", "Phân tích tư thế và phát hiện quay đầu nghi vấn", "Mã nguồn ai_engine.py, temporal_tracker.py; sơ đồ pose_heuristic_diagram.png", "ĐÃ XÁC MINH (Code & Diagram)"],
        ["F-04", "Bộ đệm vòng và trích xuất clip bằng chứng chuẩn 1.0x", "Mã nguồn ring_buffer.py, openh264 DLL; 382 clip hợp lệ đọc được liên kết DB (422 tệp MP4 trên đĩa)", "ĐÃ XÁC MINH (Code & Clips)"],
        ["F-05", "Quản lý và lưu trữ sự cố an toàn bằng SQLite WAL", "Mã nguồn database.py, db_queue.py, confidence.py; tệp cheating_system.db (439 bản ghi)", "ĐÃ XÁC MINH (Code & Database)"],
        ["F-06", "Thẩm tra sự cố vi phạm và phê duyệt của giám thị", "Mã nguồn incidents.py; ảnh giao diện incident_matrix_panel.png, video_evidence_modal.png", "ĐÃ XÁC MINH (Code & UI)"],
        ["F-07", "Cấu hình động độ nhạy AI và tham số ghi hình", "Mã nguồn settings.py; tệp ai_settings.json; ảnh giao diện ai_settings_view.png", "ĐÃ XÁC MINH (Code & UI)"],
        ["D-08", "Chuẩn hóa độ tin cậy Canonical Confidence Contract", "Module confidence.py từ chối giá trị âm, không clamp về 0; test_confidence_contract.py", "ĐÃ XÁC MINH (Test pass)"],
        ["D-09", "Bộ kiểm thử tự động Sprint 3.2B-R2", "83 tests backend, 22 tests evaluation harness, 15 tests frontend dual-camera pass", "ĐÃ XÁC MINH (Acceptance log)"],
        ["D-10", "Nghiệm thu đồng thời hai camera vật lý", "Đang chờ nhận 2 thiết bị webcam EYD PC02 đã đặt mua để thử nghiệm đồng thời", "HARDWARE ACCEPTANCE PENDING"]
    ]
    add_tbl(doc, ["Mã", "Nội dung chức năng / Kết quả kỹ thuật", "Căn cứ minh chứng kỹ thuật", "Trạng thái xác minh"], 
            audit_matrix, caption="Bảng Phụ lục 1. Ma trận đối chiếu minh chứng kỹ thuật và truy vết mã nguồn", 
            col_widths=[0.8, 2.5, 2.7, 1.2])

    output_path = r"deliverables\ha_noi\BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.docx"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f"Successfully generated: {output_path}")

if __name__ == '__main__':
    build_bao_cao()
