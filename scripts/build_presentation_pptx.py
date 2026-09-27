# -*- coding: utf-8 -*-
"""
Script to build SLIDE_THUYET_TRINH_GIAM_SAT_PHONG_THI.pptx
Generates a 14-slide widescreen (16:9) presentation with:
- Dark Slate aesthetic matching Anti-Slop guidelines
- High school accessible metaphors and explanations
- Embedded real screenshots and diagrams
- Embedded word-for-word speaker notes on each slide
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Color Palette (Dark Slate Anti-Slop)
COLOR_BG = RGBColor(9, 13, 22)         # #090d16
COLOR_CARD = RGBColor(24, 32, 47)      # #18202f
COLOR_BORDER = RGBColor(51, 65, 85)    # #334155
COLOR_TEXT_MAIN = RGBColor(248, 250, 252) # #f8fafc
COLOR_TEXT_MUTED = RGBColor(148, 163, 184) # #94a3b8
COLOR_EMERALD = RGBColor(16, 185, 129) # #10b981
COLOR_AMBER = RGBColor(245, 158, 11)   # #f59e0b
COLOR_ROSE = RGBColor(244, 63, 94)     # #f43f5e
COLOR_SKY = RGBColor(56, 189, 248)     # #38bdf8

def set_shape_flat(shape, fill_color, border_color=None, border_width_pt=1):
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(border_width_pt)
    else:
        shape.line.fill.background()

def add_header(slide, tag_text, title_text, width_in=12.0):
    # Tag
    tb_tag = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(width_in), Inches(0.35))
    tf_tag = tb_tag.text_frame
    tf_tag.word_wrap = True
    tf_tag.margin_left = tf_tag.margin_right = tf_tag.margin_top = tf_tag.margin_bottom = 0
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = tag_text.upper()
    p_tag.font.size = Pt(11)
    p_tag.font.bold = True
    p_tag.font.color.rgb = COLOR_SKY
    p_tag.font.name = "Arial"

    # Main Title
    tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(width_in), Inches(0.6))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_TEXT_MAIN
    p_title.font.name = "Arial"

def add_card(slide, left, top, width, height, title, lines, accent_color=COLOR_SKY):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    set_shape_flat(shape, COLOR_CARD, COLOR_BORDER, 1)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.25)
    tf.margin_top = Inches(0.2)
    tf.margin_bottom = Inches(0.2)

    # Title
    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.size = Pt(15)
    p0.font.bold = True
    p0.font.color.rgb = accent_color
    p0.font.name = "Arial"
    p0.space_after = Pt(8)

    # Content
    for line in lines:
        p = tf.add_paragraph()
        p.text = "• " + line
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.font.name = "Arial"
        p.space_after = Pt(6)

def add_speaker_note(slide, script_text):
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = script_text

def build_presentation():
    prs = Presentation()
    # 16:9 Widescreen
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    img_dir = os.path.join(project_root, "deliverables", "ha_noi", "screenshots")

    # =========================================================================
    # SLIDE 1: COVER
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg1, COLOR_BG)

    # Accent badge
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.2), Inches(4.5), Inches(0.45))
    set_shape_flat(badge, COLOR_CARD, COLOR_EMERALD, 1.2)
    p = badge.text_frame.paragraphs[0]
    p.text = "🏆 DỰ ÁN NGHIÊN CỨU KHKT HỌC SINH TRUNG HỌC"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.alignment = PP_ALIGN.CENTER

    # Title
    tb_title = s1.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(11.3), Inches(2.2))
    tf = tb_title.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = "HỆ THỐNG HỖ TRỢ GIÁM SÁT PHÒNG THI"
    p1.font.size = Pt(32)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_TEXT_MAIN
    p1.font.name = "Arial"

    p2 = tf.add_paragraph()
    p2.text = "Bằng Thị Giác Máy Tính & Trích Xuất Video Bằng Chứng"
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_SKY
    p2.font.name = "Arial"
    p2.space_before = Pt(8)

    p3 = tf.add_paragraph()
    p3.text = "Ứng dụng Trí tuệ Nhân tạo hỗ trợ kỳ thi công bằng, minh bạch và nhân văn"
    p3.font.size = Pt(14)
    p3.font.color.rgb = COLOR_TEXT_MUTED
    p3.font.name = "Arial"
    p3.space_before = Pt(12)

    # Author card
    add_card(s1, 1.0, 4.6, 11.3, 2.0, "THÔNG TIN ĐOÀN DỰ THI & NHÓM TÁC GIẢ", [
        "Lĩnh vực dự thi: PHẦN MỀM HỆ THỐNG (System Software)",
        "Đơn vị: Trường THPT [Tên Trường] — Đoàn dự thi Khoa học Kỹ thuật TP. HÀ NỘI",
        "Nhóm tác giả: [Họ và tên thí sinh 1 & Thí sinh 2] | GV Hướng dẫn: [Họ và tên GVHD]",
        "Triết lý: 100% Offline trên máy trạm • Con người làm trung tâm • Tôn trọng quyền riêng tư học sinh"
    ], COLOR_EMERALD)

    add_speaker_note(s1, (
        "Kính thưa quý thầy cô trong Ban Giám khảo, thưa toàn thể các bạn học sinh thân mến!\n\n"
        "Là học sinh cấp 3, chắc hẳn mỗi chúng ta ở đây đều đã từng bước qua rất nhiều kỳ thi quan trọng: "
        "thi học kỳ, thi chọn học sinh giỏi, và sắp tới là kỳ thi Tốt nghiệp THPT. Chúng ta đều hiểu rằng, "
        "cảm giác tuyệt vời nhất sau một kỳ thi là biết rằng mọi sự nỗ lực chân chính của mình đều được đền đáp một cách công bằng nhất.\n\n"
        "Thế nhưng, làm thế nào để đảm bảo một phòng thi thực sự minh bạch mà không tạo ra bầu không khí nặng nề, căng thẳng? "
        "Hôm nay, nhóm chúng em rất vinh dự được mang đến Dự án nghiên cứu khoa học: "
        "'Hệ thống hỗ trợ giám sát phòng thi bằng thị giác máy tính và trích xuất video bằng chứng'. "
        "Em xin phép được bắt đầu bài thuyết trình ngay sau đây!"
    ))

    # =========================================================================
    # SLIDE 2: THE REAL PROBLEM
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    bg2 = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg2, COLOR_BG)
    add_header(s2, "01. BÀI TOÁN THỰC TẾ TRONG PHÒNG THI", "Tại Sao Thầy Cô Giám Thị Cần Một Trợ Lý Công Nghệ?")

    add_card(s2, 0.8, 1.6, 3.7, 5.0, "1. ÁP LỰC CỦA GIÁM THỊ", [
        "Phòng thi 24 - 30 bạn ngồi trải rộng",
        "Thời gian làm bài kéo dài 90 - 120 phút",
        "Khoa học chứng minh: Sau 30 phút, mắt người bị mỏi và khả năng tập trung chú ý giảm sút rõ rệt (Hiệu ứng Mackworth Clock)",
        "Giám thị không thể nhìn bao quát 100% mọi ngóc ngách cùng một lúc"
    ], COLOR_AMBER)

    add_card(s2, 4.8, 1.6, 3.7, 5.0, "2. GIAN LẬN SIÊU NHANH", [
        "Hành vi lén mở điện thoại tra tài liệu diễn ra chỉ trong 1 - 2 giây",
        "Động tác quay đầu nhìn trộm bài bạn diễn ra rất nhanh ở góc khuất",
        "Diễn ra đồng thời ở nhiều vị trí khác nhau khi giám thị quay lưng viết bảng hoặc kiểm tra thí sinh khác",
        "Camera CCTV thông thường chỉ ghi hình thụ động, tua lại tìm rất mất thời gian"
    ], COLOR_ROSE)

    add_card(s2, 8.8, 1.6, 3.7, 5.0, "3. KHÓ KHĂN BẰNG CHỨNG", [
        "Thầy cô bắt gặp bằng mắt thường rất dễ bị học sinh chối: 'Em chỉ mỏi cổ thôi mà!'",
        "Thiếu chứng cứ ghi hình khách quan ghi lại diễn biến trước và sau sự việc",
        "Việc lập biên bản dễ gây căng thẳng, tranh cãi không đáng có trong phòng thi",
        "Cần một 'trợ lý khách quan' lưu lại đúng khoảnh khắc vi phạm để đối chứng"
    ], COLOR_SKY)

    add_speaker_note(s2, (
        "Các bạn hãy thử tưởng tượng: Trong một phòng thi tiêu chuẩn có từ 24 đến 30 bạn học sinh ngồi ngay ngắn làm bài suốt 90 đến 120 phút. "
        "Chỉ có 2 thầy cô giám thị phải đứng bao quát toàn bộ căn phòng rộng lớn ấy.\n\n"
        "Theo nghiên cứu tâm lý học nổi tiếng của tiến sĩ Mackworth, sau 30 phút nhìn chăm chú, mắt con người sẽ bị mỏi và khả năng phát hiện các cử động bất thường sẽ tụt giảm rất nhanh. "
        "Trong khi đó, các hành vi vi phạm như lén rút điện thoại xem tài liệu, hay ngoái đầu sang bàn bên cạnh chép bài, thường chỉ diễn ra chớp nhoáng trong vòng 1 đến 2 giây ở góc khuất.\n\n"
        "Nếu thầy cô bắt gặp bằng mắt thường, khi nhắc nhở, học sinh có thể phản xạ chối: 'Em đâu có làm gì, em chỉ mỏi cổ thôi mà!'. "
        "Nếu không có bằng chứng quay lại rõ ràng, giám thị sẽ rơi vào tình thế rất khó xử. Đó chính là lý do chúng em đặt câu hỏi: "
        "Tại sao không chế tạo một trợ lý thông minh giúp thầy cô quan sát liên tục và lưu lại bằng chứng khách quan?"
    ))

    # =========================================================================
    # SLIDE 3: PHILOSOPHY & OBJECTIVES
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    bg3 = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg3, COLOR_BG)
    add_header(s3, "02. TRIẾT LÝ DỰ ÁN", "Hỗ Trợ Đắc Lực — Tuyệt Đối Không Thay Thế Con Người")

    add_card(s3, 0.8, 1.6, 5.6, 5.0, "TRỢ LÝ AI: PHỤ TÁ SOI KÍNH LÚP", [
        "Mục tiêu 1: Tiếp nhận các luồng camera phòng thi mượt mà (~15 khung hình/giây).",
        "Mục tiêu 2: Tích hợp mô hình AI quét tìm điện thoại di động trong khu vực làm bài.",
        "Mục tiêu 3: Dựng khung xương cơ thể 17 điểm để phát hiện tư thế quay đầu bất thường.",
        "Mục tiêu 4: Tự động cắt clip bằng chứng 15 giây (5s trước + 10s sau sự kiện) lưu trữ an toàn."
    ], COLOR_EMERALD)

    add_card(s3, 6.8, 1.6, 5.7, 5.0, "QUY TẮC VÀNG: HUMAN-IN-THE-LOOP", [
        "AI KHÔNG PHẢI LÀ THẨM PHÁN: Hệ thống không tự ý trừ điểm, không tự lập biên bản, không phạt học sinh.",
        "THẦY CÔ LÀ NGƯỜI QUYẾT ĐỊNH: AI chỉ gửi tín hiệu cảnh báo và video clip; giám thị xem lại bối cảnh và bấm [Xác nhận] hoặc [Bỏ qua].",
        "100% CỤC BỘ (OFFLINE ON-PREMISE): Dữ liệu video chỉ nằm trong máy tính phòng thi, không gửi ra mạng Internet, tuyệt đối an toàn.",
        "BẢO VỆ THÍ SINH TRUNG THỰC: Tạo môi trường thi cử nghiêm túc, công bằng cho tất cả các bạn chăm chỉ."
    ], COLOR_SKY)

    add_speaker_note(s3, (
        "Để giải quyết vấn đề đó, chúng em xây dựng một hệ thống phần mềm chạy ngay trên máy tính của thầy cô giám thị.\n\n"
        "Nhưng trước khi đi sâu vào kỹ thuật, em muốn nhấn mạnh triết lý cốt lõi của đề tài: "
        "Hệ thống này sinh ra để làm TRỢ LÝ, chứ tuyệt đối không thay thế con người.\n\n"
        "Nhiều bạn học sinh nghe đến 'AI giám thị' thì sợ hãi nghĩ rằng máy tính sẽ tự động trừ điểm hay đuổi mình ra khỏi phòng thi. Không hề có chuyện đó! "
        "Hệ thống của chúng em tuân thủ nguyên tắc 'Human-in-the-Loop' — nghĩa là AI chỉ đóng vai trò người phụ tá soi kính lúp: "
        "khi thấy dấu hiệu bất thường, nó cắt ngay một đoạn video bằng chứng dài 15 giây gửi lên màn hình. "
        "Thầy cô giám thị sẽ trực tiếp mở video lên xem, cân nhắc bối cảnh thực tế và là người duy nhất đưa ra quyết định cuối cùng."
    ))

    # =========================================================================
    # SLIDE 4: OVERVIEW PIPELINE
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    bg4 = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg4, COLOR_BG)
    add_header(s4, "03. BỨC TRANH TOÀN CẢNH", "Hệ Thống Hoạt Động Giống Như Camera Hành Trình Ô Tô")

    add_card(s4, 0.8, 1.6, 5.0, 5.0, "CHU TRÌNH 4 BƯỚC KHÉP KÍN", [
        "1. Thu nhận liên tục: Camera ghi hình toàn cảnh phòng thi ở tốc độ 15 FPS.",
        "2. Bộ não AI phân tích: Song song quét tìm chiếc điện thoại và đo độ lệch hướng mặt.",
        "3. Tự động cắt clip: Khi có vi phạm cờ Đỏ, hệ thống 'lùi thời gian' lấy 5s trước và quay thêm 10s sau.",
        "4. Giám thị thẩm tra: Video MP4 phát đúng tốc độ thực 1.0x để thầy cô xem và ra quyết định."
    ], COLOR_SKY)

    img_arch = os.path.join(img_dir, "architecture_pipeline_diagram.png")
    if os.path.exists(img_arch):
        s4.shapes.add_picture(img_arch, Inches(6.1), Inches(1.6), width=Inches(6.4))

    add_speaker_note(s4, (
        "Để các bạn dễ hình dung, hệ thống của chúng em hoạt động hệt như một chiếc Camera hành trình trên xe ô tô "
        "hay tính năng Instant Replay quay chậm trong các trận đấu bóng đá.\n\n"
        "Quy trình diễn ra theo 4 bước khép kín:\n"
        "Đầu tiên, camera gắn trên bục giảng thu lại toàn cảnh phòng thi.\n"
        "Tiếp theo, 'bộ não' AI sẽ liên tục quan sát từng khung hình để phát hiện xem có chiếc điện thoại nào xuất hiện trên bàn hay bạn nào đang ngoái đầu sang bài bạn bên cạnh hay không.\n"
        "Nếu phát hiện hành vi nghi vấn kéo dài, chuông cảnh báo âm thầm nổi lên trên màn hình thầy cô, đồng thời hệ thống tự động 'lùi thời gian' để cắt lại đoạn video 5 giây trước đó và quay tiếp 10 giây sau đó.\n"
        "Cuối cùng, thầy cô chỉ việc bấm vào xem lại clip để biết chính xác sự thật vừa diễn ra. Rất nhanh gọn và minh bạch!"
    ))

    # =========================================================================
    # SLIDE 5: PHONE DETECTION (YOLO11s)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    bg5 = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg5, COLOR_BG)
    add_header(s5, "04. MẮT THẦN 1: NHẬN DIỆN ĐIỆN THOẠI", "Thị Giác Máy Tính: Tìm Đồ Vật Trong Chớp Mắt (0,03 Giây)")

    add_card(s5, 0.8, 1.6, 5.2, 5.0, "CÔNG NGHỆ NHẬN DIỆN YOLO", [
        "Khái niệm: Thị giác máy tính (Computer Vision) là dạy máy tính 'nhìn và hiểu' bức ảnh như mắt người.",
        "Mô hình YOLO (You Only Look Once): Quét toàn bộ khung hình trong 1 lần duy nhất, siêu nhanh (~0,03s/khung hình).",
        "Huấn luyện bài bản: Máy tính học qua gần 3.000 bức ảnh chụp điện thoại ở mọi tư thế: để trên bàn, giấu dưới ngăn bàn, cầm nghiêng...",
        "Độ chính xác cao: Đạt 80,4% Precision và mAP@0.5 = 78,58% trên tập dữ liệu kiểm thử nội bộ."
    ], COLOR_ROSE)

    img_cam = os.path.join(img_dir, "live_monitor_multi_cam.png")
    if os.path.exists(img_cam):
        s5.shapes.add_picture(img_cam, Inches(6.3), Inches(1.6), width=Inches(6.2))

    add_speaker_note(s5, (
        "Bây giờ, chúng ta hãy cùng khám phá xem: Làm sao một chiếc máy tính vô tri lại có thể 'nhìn' thấy chiếc điện thoại thông minh?\n\n"
        "Các bạn biết đấy, đối với máy tính, một bức ảnh chụp từ camera chỉ là một ma trận gồm hàng triệu con số pixel khô khốc. Để máy tính 'hiểu' được bức ảnh, chúng em ứng dụng một công nghệ gọi là Thị giác máy tính với mô hình mạng nơ-ron mang tên YOLO — viết tắt của cụm từ 'You Only Look Once' nghĩa là 'Bạn chỉ cần nhìn một lần'.\n\n"
        "Nó giống như khi các bạn chơi trò 'Tìm đồ vật bị giấu': Thay vì phải lấy kính lúp soi từng centimet vuông, mắt các bạn chỉ cần lướt qua cả bức tranh một lần là định vị được ngay món đồ cần tìm.\n\n"
        "Chúng em đã cho máy tính học gần 3.000 bức ảnh chụp điện thoại ở đủ mọi góc độ: từ điện thoại màn hình đen đặt trên bàn gỗ, điện thoại giấu nửa phần dưới tờ giấy nháp, cho đến điện thoại cầm nghiêng trong lòng bàn tay. Nhờ vậy, chỉ mất khoảng 0,03 giây cho một khung hình, mô hình đã có thể khoanh một chiếc hộp màu đỏ chính xác quanh chiếc điện thoại và báo ngay cho giám thị!"
    ))

    # =========================================================================
    # SLIDE 6: POSE ESTIMATION (STICKMAN)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    bg6 = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg6, COLOR_BG)
    add_header(s6, "05. MẮT THẦN 2: PHÁT HIỆN QUAY ĐẦU", "Vẽ 'Người Que' (Stickman) Để Bắt Trúng Tư Thế Nhìn Bài")

    add_card(s6, 0.8, 1.6, 5.2, 5.0, "HÌNH HỌC KHUNG XƯƠNG THÔNG MINH", [
        "17 Điểm Khớp Xương: Mô hình YOLO Pose định vị Mũi, 2 Mắt, 2 Tai, 2 Bờ Vai của thí sinh.",
        "Quy tắc khi làm bài bình thường: Mũi nằm ở chính giữa hai tai; khoảng cách Mũi - Tai Trái bằng Mũi - Tai Phải.",
        "Quy tắc khi quay đầu nhìn bài bạn: Chóp mũi lệch hẳn sang một bên tai; đồng thời trục Mắt bị xoắn chéo so với trục Vai.",
        "Điểm số nghi vấn (Score S): Biến cử động thực tế thành con số toán học từ 0.0 (Bình thường) đến 1.0 (Quay đầu tối đa)."
    ], COLOR_EMERALD)

    img_pose = os.path.join(img_dir, "pose_heuristic_diagram.png")
    if os.path.exists(img_pose):
        s6.shapes.add_picture(img_pose, Inches(6.3), Inches(1.6), width=Inches(6.2))

    add_speaker_note(s6, (
        "Nhận diện điện thoại đã khó, nhưng phát hiện hành vi quay đầu nhìn bài bạn còn tinh tế hơn rất nhiều. Làm sao máy tính phân biệt được bạn đang nhìn bài thi của mình hay đang nhìn bài thi của bạn ngồi cạnh?\n\n"
        "Để giải bài toán này, chúng em không dùng các cảm biến gắn lên người, mà sử dụng thuật toán Ước lượng tư thế (Pose Estimation). Mô hình sẽ biến hình ảnh của mỗi thí sinh thành một 'Người Que' (Stickman) thông minh bằng cách chấm 17 điểm mốc quan trọng: đỉnh mũi, 2 mắt, 2 tai và 2 bờ vai.\n\n"
        "Nguyên lý hình học cực kỳ đơn giản mà thú vị:\n"
        "Khi chúng mình chăm chú nhìn thẳng xuống bài thi, chóp mũi sẽ nằm ngay chính giữa hai tai. Khoảng cách từ mũi đến tai trái và tai phải là hoàn toàn cân xứng.\n"
        "Nhưng khi một bạn ngoái đầu sang trái để xem bài bạn bên cạnh, chóp mũi lập tức dịch chuyển áp sát vào tai trái, trong khi tai phải bị che khuất hoặc lệch xa ra. Đồng thời, đường nối hai con mắt sẽ bị vặn chéo so với đường nối hai bờ vai.\n\n"
        "Từ độ lệch hình học này, hệ thống sẽ tính ra một 'điểm số nghi vấn' theo thời gian thực. Càng quay đầu mạnh, điểm số càng tăng vọt!"
    ))

    # =========================================================================
    # SLIDE 7: ANTI-FALSE-ALARM (1.25S RULE)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    bg7 = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg7, COLOR_BG)
    add_header(s7, "06. BÍ QUYẾT CHỐNG BÁO ĐỘNG OAN", "Quy Tắc 1,25 Giây: Hắt Xì Hơi Hay Mỏi Cổ Không Bị Phạt")

    add_card(s7, 0.8, 1.6, 5.6, 5.0, "CỬ ĐỘNG THOÁNG QUA (< 1,25s)", [
        "Tình huống đời thường: Bạn ngồi mỏi cổ xoay đầu thư giãn, quay sang hắt xì hơi, cúi nhặt chiếc bút rơi...",
        "Thời gian diễn ra: Rất ngắn, chỉ khoảng 0,3 đến 0,8 giây.",
        "Phản ứng của Hệ thống: Kích hoạt CỜ VÀNG (Yellow Flag) âm thầm trên màn hình giám thị.",
        "Tự động xóa sạch: Nếu sau 0,75 giây bạn quay lại làm bài, hệ thống tự động reset về bình thường, KHÔNG làm phiền ai."
    ], COLOR_AMBER)

    add_card(s7, 6.8, 1.6, 5.7, 5.0, "VI PHẠM KÉO DÀI (≥ 1,25s)", [
        "Tình huống nghi vấn: Bạn ngoái đầu sang bàn bên cạnh và giữ yên ánh mắt để đọc đáp án A, B, C.",
        "Thời gian duy trì: Đủ lâu từ 1,25 giây trở lên (bộ đếm thời gian liên tục).",
        "Phản ứng của Hệ thống: Chính thức leo thang lên CỜ ĐỎ (Red Flag).",
        "Kích hoạt bằng chứng: Lập tức ra lệnh cho bộ nhớ RAM xuất video 15 giây gửi đến giám thị để xem xét."
    ], COLOR_ROSE)

    add_speaker_note(s7, (
        "Tuy nhiên, trong thực tế, các bạn học sinh làm bài thi rất hay ngọ nguậy: Có bạn ngồi lâu mỏi cổ quá thì xoay đầu sang hai bên thư giãn mất nửa giây; có bạn quay sang góc để hắt xì hơi; có bạn quay đầu nhìn đồng hồ treo tường. Nếu hệ thống cứ thấy đầu lệch đi là rú còi báo vi phạm, thì đó là một hệ thống tồi tệ và gây phiền hà!\n\n"
        "Để giải quyết vấn đề này, nhóm chúng em đã lập trình một cơ chế gọi là 'Bộ lọc thời gian chống báo động oan'.\n\n"
        "Quy tắc rất nhân văn:\n"
        "Nếu bạn chỉ xoay đầu thoáng qua dưới 1,25 giây rồi quay lại làm bài ngay, hệ thống chỉ ghi nhận một tín hiệu 'Cờ Vàng' âm thầm và tự động xóa sau 0,75 giây. Không có bất kỳ cảnh báo nào làm phiền thầy cô cả.\n"
        "Nhưng nếu góc quay đầu nghi vấn ấy bị giữ bất động liên tục từ 1,25 giây trở lên — khoảng thời gian đủ để đọc lén đáp án trắc nghiệm câu A, B, C của bạn bên cạnh — hệ thống mới chính thức leo thang thành 'Cờ Đỏ' và kích hoạt quy trình lưu bằng chứng.\n"
        "Nhờ vậy, hệ thống hoàn toàn loại bỏ được những hiểu lầm không đáng có!"
    ))

    # =========================================================================
    # SLIDE 8: RINGBUFFER 15S CLIP
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    bg8 = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg8, COLOR_BG)
    add_header(s8, "07. BỘ ĐỆM VÒNG RINGBUFFER", "Quay Ngược Thời Gian: Trích Xuất Video Cả Quá Khứ Lẫn Tương Lai")

    add_card(s8, 0.8, 1.6, 5.0, 5.0, "CƠ CHẾ 'LÙI THỜI GIAN' KỲ DIỆU", [
        "Nghịch lý: Khi AI phát hiện ra thì hành vi đã bắt đầu từ vài giây trước rồi!",
        "Giải pháp Băng chuyền RAM: Luôn lưu sẵn 5 giây video trong bộ nhớ trượt (Pre-roll). Khung hình mới vào thì khung cũ tự rơi ra.",
        "Khoảnh khắc Cờ Đỏ: Đóng băng ngay 5 giây quá khứ + quay tiếp 10 giây tương lai (Post-roll).",
        "Thuật toán Resampling: Tái lấy mẫu đều trên lưới thời gian, giúp video phát lại mượt mà đúng tốc độ thực 1.0x."
    ], COLOR_SKY)

    img_ring = os.path.join(img_dir, "ring_buffer_time_window.png")
    if os.path.exists(img_ring):
        s8.shapes.add_picture(img_ring, Inches(6.1), Inches(1.6), width=Inches(6.4))

    add_speaker_note(s8, (
        "Một câu hỏi thú vị đặt ra là: Nếu tại thời điểm này AI mới nhìn thấy chiếc điện thoại, thì làm sao quay lại được cảnh bạn đó vừa thò tay vào hộc bàn rút điện thoại ra từ 3 giây trước? Chẳng lẽ máy tính biết 'quay ngược thời gian'?\n\n"
        "Đúng là như vậy đấy các bạn ạ! Nhóm chúng em đã thiết kế một giải pháp kỹ thuật gọi là Bộ đệm vòng (RingBuffer) trong bộ nhớ RAM của máy tính.\n\n"
        "Bộ đệm này giống như một chiếc băng chuyền tròn luôn chuyển động: Nó liên tục giữ lại những thước phim của 5 giây vừa trôi qua. Khung hình mới đi vào thì khung hình quá 5 giây sẽ tự rơi ra ngoài.\n\n"
        "Ngay khoảnh khắc AI kích hoạt Cờ Đỏ, hệ thống lập tức 'đóng băng' 5 giây quá khứ quý giá đó lại, rồi thong thả quay tiếp 10 giây tiếp theo của tương lai. Sau đó, nó ráp hai nửa lại thành một đoạn clip hoàn chỉnh dài đúng 15 giây.\n\n"
        "Khi mở clip này lên, thầy cô sẽ thấy trọn vẹn cả một câu chuyện: từ lúc bạn thí sinh ngó nghiêng xung quanh, thò tay xuống ngăn bàn lấy điện thoại ra, cho đến phản ứng sau đó. Bằng chứng rõ ràng đến mức không thể chối cãi!"
    ))

    # =========================================================================
    # SLIDE 9: DUAL-STREAM ARCHITECTURE
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    bg9 = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg9, COLOR_BG)
    add_header(s9, "08. ĐỘT PHÁ TỐC ĐỘ: HAI LUỒNG ĐỘC LẬP", "Giải Quyết Giật Lag: Câu Chuyện Người Quay Phim & Bác Thám Tử")

    add_card(s9, 0.8, 1.6, 5.6, 5.0, "ANH THỢ QUAY PHIM (CAMERA STREAM)", [
        "Nhiệm vụ: Chuyên tâm ghi hình, không quan tâm AI đang làm gì.",
        "Tốc độ: 15 khung hình/giây mượt mà.",
        "Hành động: Ném thẳng mọi bức ảnh vừa quay vào túi RingBuffer.",
        "Kết quả: Không bao giờ bị dừng hình hay mất bất kỳ giây video nào!"
    ], COLOR_EMERALD)

    add_card(s9, 6.8, 1.6, 5.7, 5.0, "BÁC THÁM TỬ (AI INFERENCE STREAM)", [
        "Nhiệm vụ: Cầm kính lúp phân tích kỹ lưỡng (mất ~0,36s mỗi ảnh).",
        "Bộ đệm 1 phần tử (Single-Slot Buffer): Chỉ để đúng 1 bức ảnh mới nhất trên bàn.",
        "Quy tắc làm việc: Soi xong ảnh trước → Bốc ngay ảnh MỚI NHẤT, bỏ qua các ảnh cũ ở giữa.",
        "Kết quả: Cảnh báo luôn bám sát đời thực, triệt tiêu hoàn toàn hiện tượng nghẽn mạng tích lũy!"
    ], COLOR_AMBER)

    add_speaker_note(s9, (
        "Trong quá trình lập trình, chúng em đã đụng phải một bức tường kỹ thuật rất lớn: Đó là hiện tượng giật lag và trễ hình.\n\n"
        "Camera thông thường thu nhận tới 15 khung hình mỗi giây. Nhưng máy tính trong phòng thi thường là máy tính văn phòng bình thường, chip AI phải mất khoảng 0,36 giây mới phân tích xong một hình — tức là một giây nó chỉ soi được khoảng 3 hình. "
        "Nếu cứ bắt camera phải đứng đợi AI phân tích xong mới được quay tiếp, thì chỉ sau 1 phút, hình ảnh trên màn hình sẽ bị trễ cả chục giây so với đời thực!\n\n"
        "Để giải bài toán này, nhóm chúng em đã sáng tạo ra Kiến trúc hai luồng phân tách (Dual-Stream), ví như sự phối hợp giữa một Anh thợ quay phim và một Bác thám tử:\n"
        "- Anh thợ quay phim làm việc độc lập: Cứ 1 giây anh quay đủ 15 khung hình ném thẳng vào kho lưu trữ RingBuffer. Anh không bao giờ dừng lại chờ ai.\n"
        "- Còn Bác thám tử AI: Bác cứ bình tĩnh soi kỹ từng bức ảnh. Soi xong bức ảnh này, bác không nhìn lại những ảnh cũ đã trôi qua, mà bốc ngay bức ảnh mới nhất đang xuất hiện trước mắt để phân tích.\n\n"
        "Nhờ tách rời hai nhiệm vụ này, hệ thống vừa ghi trọn vẹn từng khoảnh khắc video mượt mà, vừa đảm bảo cảnh báo AI luôn bám sát theo thời gian thực mà không bao giờ bị nghẽn mạng!"
    ))

    # =========================================================================
    # SLIDE 10: PROCTOR DASHBOARD & MODAL
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    bg10 = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg10, COLOR_BG)
    add_header(s10, "09. TRỰC QUAN HÓA: BẢNG ĐIỀU KHIỂN GIÁM THỊ", "Giao Diện Tối Giản, Dễ Dùng: Xem Lại Clip Và Phê Duyệt Tức Thì")

    add_card(s10, 0.8, 1.6, 5.0, 5.0, "TRẢI NGHIỆM TIỆN LỢI CHO THẦY CÔ", [
        "Phong cách Anti-Slop: Tông màu tối Slate dịu mắt, chống mỏi mắt khi trực ca thi dài.",
        "Theo dõi trực tiếp: Hiển thị lưới camera kèm đồng hồ đo nhịp tim hệ thống (Acquisition FPS, AI FPS).",
        "Xem Clip tức thì: Bấm nút 'Xem Clip' là mở ngay hộp thoại phát lặp đoạn video 15 giây sắc nét.",
        "Phê duyệt 1 chạm: Bấm [Xác nhận] nếu đúng vi phạm, hoặc [Bỏ qua] nếu chỉ là cử động tự nhiên."
    ], COLOR_SKY)

    img_modal = os.path.join(img_dir, "video_evidence_modal.png")
    if os.path.exists(img_modal):
        s10.shapes.add_picture(img_modal, Inches(6.1), Inches(1.6), width=Inches(6.4))

    add_speaker_note(s10, (
        "Trên màn hình lúc này là giao diện thực tế của phần mềm do chính chúng em thiết kế bằng công nghệ React 19 mới nhất.\n\n"
        "Chúng em tuân thủ triết lý thiết kế tối giản công nghiệp: Tông màu tối Slate dịu mắt giúp thầy cô không bị chói khi ngồi trực phòng thi suốt nhiều giờ liền.\n\n"
        "Màn hình chia làm hai khu vực rất trực quan:\n"
        "- Bên trái là màn hình truyền hình trực tiếp từ các camera gắn trong phòng. Trên góc mỗi camera có đồng hồ đo tốc độ thực tế.\n"
        "- Khi có sự cố, một thẻ cảnh báo màu đỏ sẽ xuất hiện ngay ở cột bên phải. Thầy cô chỉ cần bấm vào nút 'Xem Clip'. Một cửa sổ sẽ hiện lên phát đi phát lại đoạn video bằng chứng 15 giây quay cận cảnh hành vi đó.\n"
        "- Sau khi xem xong, thầy cô có thể bấm nút 'Xác nhận' để lưu vào biên bản, hoặc bấm 'Bỏ qua' nếu thấy bạn thí sinh không hề có ý đồ xấu. Mọi thao tác chỉ diễn ra trong vòng 5 giây!"
    ))

    # =========================================================================
    # SLIDE 11: SCIENTIFIC RESULTS
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    bg11 = s11.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg11, COLOR_BG)
    add_header(s11, "10. KẾT QUẢ THỰC NGHIỆM", "Khoa Học Trung Thực: Sản Phẩm Chạy Thật, Số Liệu Thật")

    add_card(s11, 0.8, 1.6, 3.7, 5.0, "83/83 BÀI TEST PASS", [
        "Kiểm thử tự động toàn diện: 83 bài test backend, 22 test toán học, 15 test frontend dual-camera.",
        "Tỷ lệ vượt qua: 100% PASS (Exit code 0).",
        "Đảm bảo hệ thống vận hành bền bỉ, không bị văng ứng dụng giữa chừng."
    ], COLOR_EMERALD)

    add_card(s11, 4.8, 1.6, 3.7, 5.0, "PHIÊN ĐO TẢI 125,1 GIÂY", [
        "Camera gửi 1.952 khung hình ở tốc độ trung bình 15,6 FPS cực kỳ ổn định.",
        "AI thực hiện 354 kết quả suy luận bám sát thời gian thực.",
        "Tỷ lệ thay thế khung hình thông minh đạt 85,3%, giúp hệ thống không bao giờ bị nghẽn."
    ], COLOR_SKY)

    add_card(s11, 8.8, 1.6, 3.7, 5.0, "CSDL 439 BẢN GHI THẬT", [
        "Cơ sở dữ liệu SQLite WAL an toàn: Đã lưu 439 sự cố thực nghiệm.",
        "Kiểm toán kho chứng cứ: Có 382 clip MP4 hợp lệ liên kết chính xác với hồ sơ.",
        "Bộ nhớ RAM ổn định: Giữ mức ~380 MB ở chuẩn Full HD, không rò rỉ bộ nhớ."
    ], COLOR_AMBER)

    add_speaker_note(s11, (
        "Kính thưa Ban Giám khảo, một nghiên cứu khoa học chân chính phải được chứng minh bằng những con số thực nghiệm cụ thể chứ không thể nói suông.\n\n"
        "Chúng em đã xây dựng một bộ kiểm thử tự động toàn diện với 83 bài kiểm tra đơn vị và kết quả đạt 83/83 bài test đỗ tuyệt đối.\n\n"
        "Trong phiên chạy thử nghiệm đo tải liên tục hơn 2 phút:\n"
        "- Hệ thống đã tiếp nhận 1.952 khung hình từ camera ở tốc độ cực kỳ ổn định là 15,6 khung hình/giây.\n"
        "- Trí tuệ nhân tạo đã thực hiện 354 lượt suy luận chuyên sâu và phát hiện thành công các tình huống vi phạm giả định.\n"
        "- Khi thử nghiệm với camera độ phân giải cao Full HD 1080p, mức tiêu thụ bộ nhớ RAM tự động dừng lại ở mức cân bằng khoảng 380MB, hoàn toàn không bị nóng máy hay tràn RAM.\n\n"
        "Hiện tại, trong cơ sở dữ liệu thực nghiệm của hệ thống đã lưu trữ an toàn 439 bản ghi sự cố cùng hàng trăm đoạn video MP4 bằng chứng sẵn sàng truy xuất bất kỳ lúc nào!"
    ))

    # =========================================================================
    # SLIDE 12: ETHICS & PRIVACY
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    bg12 = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg12, COLOR_BG)
    add_header(s12, "11. ĐẠO ĐỨC AI & QUYỀN RIÊNG TƯ", "Nguyên Tắc '3 Không' Bảo Vệ Tối Đa Quyền Lợi Học Sinh")

    add_card(s12, 0.8, 1.6, 3.7, 5.0, "1. KHÔNG QUÉT KHUÔN MẶT", [
        "Hệ thống KHÔNG nhận diện khuôn mặt (No Face ID).",
        "KHÔNG lưu trữ số báo danh hay tên thí sinh.",
        "Chỉ phân tích hình dáng chuyển động của các khớp xương và vật thể điện thoại.",
        "Bảo vệ 100% quyền riêng tư và dữ liệu sinh trắc học của học sinh."
    ], COLOR_EMERALD)

    add_card(s12, 4.8, 1.6, 3.7, 5.0, "2. KHÔNG LÊN ĐÁM MÂY", [
        "Hoạt động Offline 100% trên máy trạm của giám thị.",
        "Không cần kết nối mạng Internet, không lo đứt cáp.",
        "Không gửi bất kỳ hình ảnh nào ra máy chủ bên ngoài.",
        "Triệt tiêu hoàn toàn nguy cơ rò rỉ hay lộ clip phòng thi ra mạng xã hội."
    ], COLOR_SKY)

    add_card(s12, 8.8, 1.6, 3.7, 5.0, "3. KHÔNG TỰ PHẠT HỌC SINH", [
        "AI không có quyền lực phán xét hạnh kiểm con người.",
        "Không tự động lập biên bản kỷ luật.",
        "Mọi quyết định đều do thầy cô giám thị xem xét dựa trên tình hình thực tế.",
        "Công nghệ là công cụ bảo vệ công bằng, nhân văn và minh bạch."
    ], COLOR_AMBER)

    add_speaker_note(s12, (
        "Khi làm đề tài này, một trong những điều mà nhóm chúng em trăn trở nhiều nhất chính là: Vấn đề đạo đức công nghệ và quyền riêng tư của các bạn học sinh.\n\n"
        "Liệu một hệ thống camera thông minh có biến phòng thi thành một nơi bị soi xét ngột ngạt hay làm lộ dữ liệu cá nhân của các bạn không?\n\n"
        "Câu trả lời của chúng em là: TUYỆT ĐỐI KHÔNG, nhờ bộ nguyên tắc '3 KHÔNG' nghiêm ngặt:\n"
        "- Thứ nhất, KHÔNG nhận diện khuôn mặt: Hệ thống chỉ phân tích tọa độ các khớp xương và hình dạng chiếc điện thoại. AI hoàn toàn không biết bạn là ai, tên gì, hay số báo danh bao nhiêu.\n"
        "- Thứ hai, KHÔNG gửi dữ liệu ra Internet: Hệ thống chạy offline 100% trên máy tính của giám thị. Không có một khung hình nào bị gửi lên đám mây, triệt tiêu hoàn toàn nguy cơ rò rỉ hình ảnh học sinh ra ngoài.\n"
        "- Và thứ ba, KHÔNG tự động kỷ luật: Công nghệ chỉ cung cấp lăng kính trung thực nhất để bảo vệ sự công bằng cho tất cả các bạn học sinh làm bài nghiêm túc, ngăn chặn sự gian lận và tránh mọi quyết định oan sai từ cảm quan nhất thời."
    ))

    # =========================================================================
    # SLIDE 13: CONCLUSION & FUTURE WORK
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    bg13 = s13.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg13, COLOR_BG)
    add_header(s13, "12. TỔNG KẾT & BƯỚC ĐI TIẾP THEO", "Từ Phòng Thi Trường Mình Đến Kỳ Thi Quy Mô Toàn Quốc")

    add_card(s13, 0.8, 1.6, 5.6, 5.0, "KẾT QUẢ ĐẠT ĐƯỢC HÔM NAY", [
        "Hoàn thiện 7 chức năng cốt lõi (F-01 đến F-07) chạy thực tế trên máy tính trường học.",
        "Tiết kiệm chi phí tối đa: Tận dụng máy tính văn phòng và webcam phổ thông có sẵn, không tốn tiền mua máy chủ đắt đỏ.",
        "Góp phần xây dựng văn hóa thi cử tự giác, công bằng và văn minh.",
        "Sẵn sàng triển khai thử nghiệm tại các kỳ thi thử, thi khảo sát chất lượng của nhà trường."
    ], COLOR_EMERALD)

    add_card(s13, 6.8, 1.6, 5.7, 5.0, "HƯỚNG PHÁT TRIỂN TƯƠNG LAI", [
        "Nâng cấp tư thế 3D (3D Head Pose): Đo góc quay đầu Euler 3 chiều chuẩn xác hơn nữa.",
        "Phát hiện hành vi chuyền đồ: Nghiên cứu mô hình tương tác tay - vật thể để bắt hành vi chuyền phao giấy dưới gầm bàn.",
        "Mạng giám sát liên phòng thi: Kết nối tín hiệu cảnh báo từ nhiều phòng thi về phòng Hội đồng thi của Ban giám hiệu.",
        "Quy chuẩn quản lý bằng chứng: Hoàn thiện quy chế phân quyền và tự động xóa dữ liệu định kỳ sau kỳ thi."
    ], COLOR_SKY)

    add_speaker_note(s13, (
        "Kính thưa Ban Giám khảo và các bạn,\n\n"
        "Sau quá trình nghiên cứu và thực nghiệm nghiêm túc, nhóm chúng em đã hoàn thành trọn vẹn nguyên mẫu phần mềm với 7 chức năng cốt lõi. Điểm sáng lớn nhất của dự án là khả năng vận hành trơn tru ngay trên những máy tính văn phòng sẵn có trong trường học kết hợp với các camera phổ thông, giúp tiết kiệm chi phí tối đa cho ngành giáo dục.\n\n"
        "Trong giai đoạn tiếp theo, nhóm chúng em ấp ủ dự định sẽ nâng cấp thêm thuật toán ước lượng tư thế 3D trong không gian để đo độ nghiêng đầu chính xác hơn nữa, cũng như nghiên cứu nhận diện cử chỉ chuyền phao giấy dưới gầm bàn.\n\n"
        "Chúng em tin rằng, công nghệ chỉ thực sự có ý nghĩa khi nó phục vụ cuộc sống và mang lại sự công bằng, văn minh cho mái trường."
    ))

    # =========================================================================
    # SLIDE 14: THANK YOU & Q&A
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    bg14 = s14.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg14, COLOR_BG)

    tb_thank = s14.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(2.0))
    tf = tb_thank.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = "XIN TRÂN TRỌNG CẢM ƠN QUÝ THẦY CÔ & CÁC BẠN!"
    p1.font.size = Pt(28)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_TEXT_MAIN
    p1.alignment = PP_ALIGN.CENTER

    p2 = tf.add_paragraph()
    p2.text = "Sẵn sàng cho phần chạy Demo trực tiếp & Trả lời câu hỏi phản biện (Q&A)"
    p2.font.size = Pt(18)
    p2.font.color.rgb = COLOR_SKY
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(12)

    # Summary box
    shape = s14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(2.0), Inches(4.2), Inches(9.333), Inches(2.2))
    set_shape_flat(shape, COLOR_CARD, COLOR_EMERALD, 1.2)
    tf_s = shape.text_frame
    tf_s.word_wrap = True
    tf_s.margin_left = tf_s.margin_right = Inches(0.4)
    tf_s.margin_top = Inches(0.3)
    p_s1 = tf_s.paragraphs[0]
    p_s1.text = "💡 THÔNG ĐIỆP ĐỀ TÀI CỦA CHÚNG EM:"
    p_s1.font.size = Pt(14)
    p_s1.font.bold = True
    p_s1.font.color.rgb = COLOR_EMERALD

    p_s2 = tf_s.add_paragraph()
    p_s2.text = "\"Khoa học bắt đầu từ những trăn trở rất đỗi bình dị của học trò.\nCông nghệ hoàn thiện không phải để trừng phạt, mà là để bảo vệ thành quả của những giọt mồ hôi học tập chân chính!\""
    p_s2.font.size = Pt(13)
    p_s2.font.italic = True
    p_s2.font.color.rgb = COLOR_TEXT_MAIN
    p_s2.space_before = Pt(8)

    add_speaker_note(s14, (
        "Bài thuyết trình của nhóm chúng em đến đây là kết thúc. Chúng em xin được gửi lời cảm ơn chân thành nhất tới quý thầy cô trong Ban Giám khảo đã chú ý lắng nghe và hướng dẫn chúng em trong suốt quá trình hoàn thiện đề tài.\n\n"
        "Sau đây, chúng em rất mong nhận được những lời nhận xét, góp ý quý báu của quý thầy cô, và chúng em đã sẵn sàng cho phần chạy thử nghiệm trực tiếp (Live Demo) cũng như trả lời các câu hỏi phản biện.\n\n"
        "Em xin trân trọng cảm ơn!"
    ))

    # Save presentation
    output_path = os.path.join(project_root, "deliverables", "ha_noi", "SLIDE_THUYET_TRINH_GIAM_SAT_PHONG_THI.pptx")
    prs.save(output_path)
    print(f"Successfully generated PowerPoint: {output_path}")

if __name__ == '__main__':
    build_presentation()
