# Bộ đào tạo AI Exam Control

**5 buổi × 90 phút · Người học chưa có nền tảng AI/CNTT · Bản 2, ngày 26/09/2026**

Mục tiêu: học viên xây kiến thức nền về dữ liệu, nhãn, ML, DL, Computer Vision, object detection, pose, fine-tune, đánh giá và triển khai thông qua chính project. Khả năng trình diễn và phản biện là kết quả của việc hiểu, không phải học thuộc đáp án. Hoàn thành khóa học không đồng nghĩa mô hình đã được đánh giá độc lập hoặc sản phẩm đã nghiệm thu tại phòng thi.

## Cách dùng

1. Người dạy đọc `02_KHUNG_KIEN_THUC.md`, `01_GIAO_AN.md` và `11_NGUON_VA_GIOI_HAN.md` trước buổi đầu.
2. Phát `03_SO_TAY_HOC_VIEN.md` và các mẫu cần dùng trong `12_PHIEU_THUC_HANH.md`. Tách phần đáp án khỏi `07_KIEM_TRA.md` trước khi phát.
3. Mở slide tương ứng trong thư mục `slides/`. Mỗi buổi có 7 slide và ghi chú cho người dạy.
4. Buổi 4 đọc artifact fine-tune lịch sử trên bản sao chỉ đọc. Không chạy lại training và không truy cập `model/`.
5. Buổi 5 chấm báo cáo đánh giá mini và phần giải thích pipeline theo `10_PHIEU_DANH_GIA.md`.

## Đủ 10 nhóm tài liệu

| Nhóm | Tài liệu |
|---|---|
| 1 | [Giáo án chuyên ngành 5 buổi](01_GIAO_AN.md) và [bản đồ kiến thức](02_KHUNG_KIEN_THUC.md) |
| 2 | Slide PowerPoint từng buổi trong `slides/` |
| 3 | [Sổ tay học viên](03_SO_TAY_HOC_VIEN.md) |
| 4 | [Kịch bản demo đi thi](04_KICH_BAN_DEMO.md), dùng sau khi đã học kiến thức |
| 5 | [30 câu hỏi ban giám khảo](05_NGAN_HANG_CAU_HOI.md), tài liệu phụ để kiểm tra hiểu |
| 6 | [Đáp án mẫu và cách trả lời khi thiếu bằng chứng](06_DAP_AN_MAU.md), không dùng để học thuộc |
| 7 | [Kiểm tra cuối 5 buổi](07_KIEM_TRA.md) |
| 8 | [Checklist lắp đặt và vận hành](08_CHECKLIST_VAN_HANH.md) |
| 9 | [Kịch bản dự phòng](09_DU_PHONG.md) |
| 10 | [Phiếu đánh giá học viên](10_PHIEU_DANH_GIA.md), [phiếu thực hành](12_PHIEU_THUC_HANH.md) và [nguồn nội bộ](11_NGUON_VA_GIOI_HAN.md) |

Các file Markdown là bản sửa được. Slide PowerPoint đã được xuất và kiểm tra cấu trúc/hiển thị. Đáp án trong tài liệu 07 và 06 dành cho người dạy; không phát trước khi kiểm tra.

## Điều kiện thực hành

Máy đã cài đủ môi trường và trọng số, camera đã kiểm tra, bộ video tình huống được phép sử dụng, bản dữ liệu đào tạo và người phụ trách kỹ thuật. Chương trình giả định nhóm 1–4 học viên cùng một máy. Với nhóm đông hơn, chia trạm hoặc tăng thời gian thực hành, không chia nhỏ thời gian thao tác đến mức học viên chỉ quan sát.

Vòng soạn tài liệu không chạy AI, không mở hoặc ghi DB và không truy cập `model/`. Các kiểm thử lịch sử được ghi rõ ngày và phạm vi. Danh sách cần xác minh khi chạy thật nằm trong tài liệu 11. Phần hướng dẫn khởi động là quy trình đề xuất từ code, chưa được chạy lại trong vòng này.
