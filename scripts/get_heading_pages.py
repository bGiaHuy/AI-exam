import os
import json
import win32com.client

path = os.path.abspath(r'deliverables\ha_noi\BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.docx')
word = win32com.client.Dispatch('Word.Application')
word.Visible = False
word.DisplayAlerts = False
doc = word.Documents.Open(path)

headings_to_find = [
    "DANH MỤC CÁC TỪ VIẾT TẮT",
    "DANH MỤC CÁC BẢNG BIỂU",
    "DANH MỤC CÁC HÌNH VẼ VÀ ĐỒ THỊ",
    "PHẦN I: MỞ ĐẦU",
    "1. Lý do chọn đề tài",
    "2. Mục tiêu nghiên cứu",
    "3. Đối tượng và phạm vi nghiên cứu",
    "4. Phương pháp nghiên cứu",
    "4.1. Phương pháp phân tích và tổng hợp lý thuyết",
    "4.2. Phương pháp quan sát khoa học",
    "4.3. Phương pháp thực nghiệm khoa học",
    "4.4. Phương pháp chuyên gia",
    "5. Tính mới và tính sáng tạo của đề tài",
    "6. Giới hạn của đề tài",
    "PHẦN II: NỘI DUNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU",
    "1. Phương án thiết kế",
    "1.1. Yêu cầu hệ thống",
    "1.2. Kiến trúc tổng thể hệ thống",
    "1.3. Các mô-đun chính của hệ thống",
    "1.4. Luồng xử lý dữ liệu và điều phối video",
    "1.5. Sơ đồ nguyên lý hoạt động",
    "1.6. Thiết kế lưu trữ và bằng chứng",
    "1.7. Thiết kế giao diện người dùng",
    "2. Công nghệ và thư viện sử dụng",
    "3. Thiết kế và lập trình phần mềm",
    "4. Các chức năng của sản phẩm",
    "4.1. Chức năng 1: Tiếp nhận và hiển thị đa luồng camera trực tiếp",
    "4.2. Chức năng 2: Phát hiện điện thoại di động trong khu vực làm bài",
    "4.3. Chức năng 3: Phân tích tư thế và phát hiện hành vi quay đầu nghi vấn",
    "4.4. Chức năng 4: Tự động trích xuất và lưu trữ clip bằng chứng chuẩn tốc độ 1.0x",
    "4.5. Chức năng 5: Thẩm tra sự cố vi phạm và phê duyệt của giám thị",
    "4.6. Chức năng 6: Cấu hình động độ nhạy AI và tham số ghi hình bằng chứng",
    "5. Nguyên lý hoạt động tổng thể của hệ thống",
    "6. Giới hạn phiên bản hiện tại",
    "PHẦN III: QUÁ TRÌNH THỬ NGHIỆM VÀ KẾT QUẢ ĐẠT ĐƯỢC",
    "1. Phương pháp thử nghiệm",
    "2. Thử nghiệm từng thành phần",
    "3. Thử nghiệm tổng thể hệ thống",
    "4. Kết quả ghi nhận",
    "5. Hạn chế của kết quả và giới hạn diễn giải khoa học",
    "6. Những cải tiến đã thực hiện sau thử nghiệm",
    "PHẦN IV: KẾT LUẬN VÀ KIẾN NGHỊ",
    "1. Kết luận",
    "2. Đóng góp kỹ thuật và xã hội của đề tài",
    "3. Kiến nghị",
    "PHẦN V: HƯỚNG PHÁT TRIỂN ĐỀ TÀI",
    "PHẦN VI: TÀI LIỆU THAM KHẢO",
    "PHỤ LỤC: MA TRẬN MINH CHỨNG VÀ TRUY VẾT DỮ LIỆU"
]

results = {}
# Start searching after page 2 (after cover and toc)
for text in headings_to_find:
    rng = doc.Content
    # Only search from character position after TOC to avoid finding the TOC itself
    rng.Start = doc.Paragraphs(25).Range.Start
    rng.Find.Execute(FindText=text)
    if rng.Find.Found:
        page = rng.Information(1)
        results[text] = page
    else:
        results[text] = "NOT_FOUND"

doc.Close(False)
word.Quit()

with open('scratch/heading_pages.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Wrote scratch/heading_pages.json successfully.")
