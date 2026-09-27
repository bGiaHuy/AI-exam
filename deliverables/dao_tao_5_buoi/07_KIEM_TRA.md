# Bộ kiểm tra kiến thức 5 buổi

Mỗi buổi 10 điểm. Ưu tiên câu giải thích và bài tập mới; không chấm điểm vì trùng câu chữ sổ tay. Đáp án nằm cuối tài liệu, người dạy tách phần đó trước khi phát.

## Buổi 1: dữ liệu và nhãn

1. Vẽ quan hệ AI, ML, DL và CV. CV có bắt buộc luôn là DL không? (2 điểm)
2. Với ảnh có máy tính Casio nhưng không có điện thoại, label detector một lớp `phone` phải thế nào? Metadata nào nên ghi? (2 điểm)
3. Phân biệt label với metadata bằng một ví dụ trong project. (2 điểm)
4. 100 frame liên tiếp của cùng video được chia ngẫu nhiên 80 frame train và 20 frame test. Nêu rủi ro và cách chia tốt hơn. (2 điểm)
5. Vì sao “có thư mục test” chưa đủ chứng minh đó là untouched holdout? (2 điểm)

## Buổi 2: computer vision và detection

1. Classification và object detection trả lời hai câu hỏi khác nhau nào? (2 điểm)
2. Ảnh 1000×500 px có box từ (200,100) đến (600,300). Viết nhãn YOLO chuẩn hóa `class xc yc w h` với class 0. (2 điểm)
3. Box A có diện tích 100, box B có diện tích 80, vùng giao 60. Tính IoU. (2 điểm)
4. Hạ confidence threshold thường làm precision và recall thay đổi theo hướng nào? Vì sao vẫn cần đo? (2 điểm)
5. Một vật có ba box dự đoán chồng nhau. NMS giải quyết vấn đề gì? (2 điểm)

## Buổi 3: pose và thời gian

1. Keypoint là output gì? Vì sao keypoint chưa phải kết luận quay đầu? (2 điểm)
2. Track 4 có phải là thí sinh số 4 không? Nêu hai tình huống ID có thể đổi. (2 điểm)
3. Chuỗi nghi vấn tại t=0; 0,5; 1,0; 1,4 giây. Với alert 1,25 s, min 3 mẫu, max gap 0,75 s, có đạt đỏ tại t=1,4 không? Giải thích. (2 điểm)
4. Thay điểm t=1,0 bằng t=1,4 rồi có thêm t=1,8. Chuỗi đầu có tiếp tục không? (2 điểm)
5. Viết một event label tối thiểu cho hành vi quay đầu trong video. (2 điểm)

## Buổi 4: fine-tune

1. Fine-tune khác inference thế nào về weights? (2 điểm)
2. Giải thích epoch, batch và checkpoint bằng lời của em. (2 điểm)
3. Training loss giảm nhưng validation loss tăng nhiều. Đây có thể là dấu hiệu gì? Cần kiểm tra thêm gì? (2 điểm)
4. `args.yaml` ghi resume từ `last.pt`. Ta được phép kết luận gì và chưa được kết luận gì? (2 điểm)
5. Vì sao augmentation không thay thế dữ liệu thực từ camera/phòng thi mục tiêu? (2 điểm)

## Buổi 5: đánh giá và hệ thống

1. Có TP=18, FP=6, FN=2. Tính precision, recall và F1. (2 điểm)
2. Vì sao mAP50 validation không được nói thành “xác suất phát hiện đúng ngoài thực tế”? (2 điểm)
3. Camera gửi 15 FPS, model trả 3 kết quả/s. Điều này cho biết gì và chưa cho biết gì? (2 điểm)
4. Nêu một lỗi data, một lỗi model và một lỗi deployment có thể cùng gây bỏ sót. (2 điểm)
5. Thiết kế một đánh giá nhỏ theo hai subgroup cho điện thoại và ghi rõ model/threshold nào phải khóa. (2 điểm)

## Đáp án và rubric

**B1.1:** AI bao trùm ML, ML bao trùm DL; CV là lĩnh vực bài toán, có thể dùng DL hoặc phương pháp khác. **B1.2:** file label rỗng; metadata `has_phone=False`, `has_distractor=True`, loại calculator cùng điều kiện. **B1.3:** box là label; lighting/camera/session là metadata. **B1.4:** leakage do frame gần trùng; chia theo video/session/camera hoặc subject phù hợp. **B1.5:** cần chứng minh chưa dùng để chỉnh và độc lập theo nguồn/phiên.

**B2.1:** classification nói lớp toàn ảnh; detection nói lớp và vị trí. **B2.2:** tâm (400,200), rộng 400, cao 200; chuẩn hóa: `0 0.4 0.4 0.4 0.4`. **B2.3:** union=100+80−60=120, IoU=0,5. **B2.4:** thường recall tăng, precision có thể giảm do thêm prediction; phải đo vì phân bố điểm và dữ liệu quyết định. **B2.5:** loại box dư quanh cùng vật dựa trên điểm và chồng lấp.

**B3.1:** tọa độ/điểm keypoint; cần quy tắc hình học và thời gian. **B3.2:** không; occlusion/mất dấu/rời khung/reset phiên là ví dụ. **B3.3:** có, elapsed 1,4 s, 4 mẫu, mỗi gap ≤0,75. **B3.4:** gap từ 0,5 đến 1,4 là 0,9 nên reset; chuỗi mới chưa nối chuỗi cũ. **B3.5:** video_id, target anonymous, start/end, behavior; direction/review/split theo protocol.

**B4.1:** fine-tune cập nhật weights; inference không. **B4.2:** chấm theo ý nghĩa, không theo câu chữ. **B4.3:** có thể overfit; cần xem dữ liệu, metric, nhiều epoch/run và lỗi nhãn. **B4.4:** được nói run tiếp tục từ checkpoint; chưa biết checkpoint khởi tạo ban đầu hay epoch trực tiếp tạo best triển khai. **B4.5:** augmentation chỉ biến đổi dữ liệu hiện có, không tái tạo đầy đủ domain mới.

**B5.1:** precision=18/24=0,75; recall=18/20=0,90; F1=2×0,75×0,90/(1,65)≈0,818. **B5.2:** khác tập, metric và ý nghĩa xác suất; validation đã tham gia phát triển. **B5.3:** pipeline có sampling/drop/supersede; chưa biết detection accuracy nếu không có nhãn. **B5.4:** ví dụ thiếu ca bị che; model chưa tổng quát; scheduler bỏ frame quan trọng. **B5.5:** cần subgroup có ý nghĩa như khoảng cách/occlusion, ground truth, checkpoint hash, confidence/IoU threshold và protocol.

Mỗi câu 2 điểm: 2 = đúng và có lý do; 1 = đúng một phần hoặc thiếu điều kiện; 0 = sai khái niệm. Nếu tính toán sai số học nhưng thiết lập đúng, cho 1 điểm. Nếu học viên nói đúng kết quả nhưng không giải thích, tối đa 1 điểm.
