# Kịch bản demo đi thi · 7 phút

## Trước khi bắt đầu

Người kỹ thuật chuẩn bị máy đã cài đủ, chế độ 1 camera đã thử, dữ liệu đào tạo, cấu hình ghi lại trên phiếu, một clip điện thoại và một clip quay đầu đã kiểm tra. Để phần mềm chạy ổn định trước khi bấm giờ. Kiểm tra đây là nguồn thật hoặc video thật được AI phân tích, không phải danh sách giả lập. Chỉ dùng đa camera nếu đã có nghiệm thu đúng thiết bị đem đi thi.

Nhóm hai người: A nói, B bấm. Nhóm một người: dừng nói ngắn khi thao tác, không vừa giải thích chi tiết vừa tìm nút. Người đóng vai ngồi tại bàn với giấy làm bài và điện thoại đạo cụ. Không cần dựng phòng thi đông người chưa kiểm tra được.

| Mốc | Lời nói gợi ý | Thao tác và điểm kiểm tra |
|---|---|---|
| 00:00–00:40 | “Dự án hỗ trợ giám thị thi giấy phát hiện tình huống nghi vấn và tìm lại video để xem xét.” | Mở màn hình giám sát. Chỉ nguồn và danh sách sự cố. |
| 00:40–01:10 | “Đây là webcam đang thu trực tiếp. Hai nhóm đang xử lý là điện thoại và quay đầu nghi vấn.” | Người diễn chuyển động tay để chứng minh hình đang thay đổi. Nếu dùng file, thay câu đầu bằng “Đây là video đã ghi, đang được AI phân tích”. |
| 01:10–01:40 | “Máy giữ lại một đoạn hình ảnh trước cảnh báo để người xem có bối cảnh.” | Kiểm tra đã bật giám sát; giữ cảnh bình thường ít nhất bằng pre-roll cấu hình. |
| 01:40–02:20 | “Em đưa điện thoại vào vùng nhìn để minh họa chức năng phát hiện vật thể.” | Diễn chậm như lúc chạy thử. Chỉ cảnh báo nếu thực sự xuất hiện. Không gọi cờ đỏ là kết luận gian lận. |
| 02:20–03:00 | “Sau cảnh báo, máy cần ghi thêm phần sau và hoàn tất file.” | Giữ nguồn chạy qua post-roll; chờ sự cố mới có clip. Sau 30 giây chưa có kết quả usable, chuyển clip đã chuẩn bị. |
| 03:00–04:00 | “Clip giúp xem hành động trước và sau thời điểm bị đánh dấu. Giám thị mới là người xem xét.” | Mở clip, chỉ đúng thời gian/nguồn và nội dung quan sát. Nếu file lỗi, dùng tài liệu 09. |
| 04:00–04:30 | “Em xác nhận thao tác duyệt trên dữ liệu phục vụ trình diễn.” | Đóng modal, bấm xác nhận hoặc bỏ qua theo tình huống đã chuẩn bị. Kiểm tra trạng thái; không bấm lặp liên tục. |
| 04:30–05:20 | “Với quay đầu, hệ thống còn xét chuỗi quan sát theo thời gian.” | Dùng clip quay đầu chuẩn bị hoặc tình huống trực tiếp đã chạy thử. Nêu rõ loại nguồn. Không cố tạo cảnh báo nhiều lần để lấp thời gian. |
| 05:20–06:10 | “Cấu hình cho phép chỉnh độ nhạy và cửa sổ clip. Các giá trị đang dùng được ghi trước buổi demo.” | Mở cấu hình để chỉ ngưỡng/pre/post, không lưu thay đổi giữa bài thi. Nếu màn hình bị khóa, nói rõ chế độ đang dùng và bỏ bước này. |
| 06:10–07:00 | “Nhóm chưa có đủ đánh giá độc lập để công bố độ chính xác thực địa. Bước tiếp theo là thu dữ liệu có nhãn, đánh giá báo nhầm và bỏ sót trên điều kiện đại diện.” | Quay lại giám sát. Kết thúc đúng giờ, sẵn sàng phản biện. |

## Câu chuyển dự phòng

“Lượt trực tiếp này chưa tạo được kết quả cần minh họa trong thời gian trình bày. Em chuyển sang clip đã ghi và kiểm tra trước để giải thích chức năng xem bằng chứng. Clip này không chứng minh lần chạy trực tiếp vừa rồi thành công.”

Nếu chuyển từ webcam sang video đầu vào: “Camera đang gặp lỗi. Em dùng video ghi trước làm đầu vào để tiếp tục minh họa AI xử lý.” Nếu backend dừng, chỉ trình chiếu clip bằng trình phát độc lập, không nói AI đang chạy.

## Phiếu rehearsal

- Ngày/giờ: __________; người nói: __________; người bấm: __________.
- Nguồn thật hoặc video đầu vào: __________; cấu hình: __________.
- Clip điện thoại đã mở được: __________; clip quay đầu đã mở được: __________.
- Thời lượng bài: __________; có phải chuyển dự phòng: __________.
- Điều nói sai hoặc thao tác cần sửa: __________.

Thử ít nhất một lượt có lỗi giả định. Không dùng endpoint tạo sự cố test để chứng minh mô hình phát hiện. Không chỉnh model hoặc dọn/xóa DB trong lúc trình bày.
