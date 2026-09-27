# Khung kiến thức chuyên ngành quanh project

## Mục tiêu thật của khóa học

Khóa học không đào tạo kỹ sư ML trong 7,5 giờ. Mục tiêu khả thi là tạo **năng lực hiểu và lập luận kỹ thuật**: học viên nhìn một thành phần của AI Exam Control, gọi đúng khái niệm, giải thích được vì sao nó tồn tại, đọc được bằng chứng cơ bản và nhận ra điều chưa được chứng minh.

Đầu ra cuối khóa gồm năm sản phẩm học tập:

1. Một data card nhỏ mô tả 12–20 mẫu dữ liệu và cách chia tập.
2. Một bộ nhãn bounding box mẫu có kiểm tra chất lượng.
3. Một sơ đồ giải thích object detection, pose estimation, tracking và luật thời gian.
4. Một phiếu đọc cấu hình cùng log fine-tune lịch sử của project.
5. Một báo cáo đánh giá nhỏ gồm confusion matrix, precision, recall, giới hạn và đề xuất thí nghiệm tiếp theo.

## Bản đồ từ khái niệm đến project

| Kiến thức | Câu hỏi học viên phải trả lời | Thành phần trong project |
|---|---|---|
| AI, ML, DL | Phần nào là luật do người viết, phần nào học từ dữ liệu? | Mô hình phát hiện/pose so với luật thời gian, RingBuffer và API |
| Sample, feature, label | Một ảnh/video đưa vào, nhãn đúng và đầu ra mong muốn là gì? | Ảnh điện thoại, bounding box; video quay đầu, khoảng thời gian sự kiện |
| Dataset split | Vì sao không đánh giá bằng chính dữ liệu đã học? | train/valid/test; blocker về untouched holdout |
| Computer Vision | Máy “nhìn” ảnh dưới dạng gì? | Khung hình camera, resize, độ phân giải và FPS |
| Object detection | Khác classification ở đâu? | YOLO tìm vị trí điện thoại bằng bounding box |
| Pose estimation | Keypoint dùng làm gì? | Các điểm mốc cơ thể/khuôn mặt đầu vào cho heuristic quay đầu |
| Tracking | Vì sao cần nối đối tượng giữa các frame? | `track_id` tạm thời, không phải danh tính |
| Temporal logic | Một frame khác một hành vi kéo dài thế nào? | Chuỗi nghi vấn, thời gian 1,25 s, gap guard |
| Transfer learning / fine-tune | Vì sao không huấn luyện từ đầu? | Run YOLO11s lịch sử, resume và checkpoint triển khai |
| Hyperparameter | Epoch, batch, image size và learning rate ảnh hưởng gì? | `epochs=60`, `batch=6`, `imgsz=960`, optimizer auto |
| Loss và metric | Loss dùng để học; metric dùng để đánh giá khác nhau thế nào? | box/cls/DFL loss, precision, recall, mAP |
| Overfitting, leakage | Mô hình “nhớ” dữ liệu có biểu hiện gì? | kiểm tra hash đã có; near duplicate/session leakage còn chưa loại trừ |
| Inference | Sau huấn luyện, model được dùng thế nào? | Nhận frame, trả detection/pose, áp ngưỡng |
| Deployment | Model tốt có đủ tạo sản phẩm tốt không? | WebSocket, scheduler, RingBuffer, DB queue, SQLite, UI |
| Human in the loop | AI đề xuất, con người quyết định ở đâu? | `pending`, `confirmed`, `dismissed` |

## Chuỗi nhân quả cần nhớ

`Bài toán đúng → dữ liệu đại diện → nhãn nhất quán → chia tập sạch → fine-tune có kiểm soát → đánh giá đúng → chọn ngưỡng → triển khai ổn định → con người duyệt`

Hỏng ở một mắt xích có thể làm kết luận phía sau yếu đi. Ví dụ, code chạy không lỗi chưa chứng minh mô hình chính xác. mAP validation cao chưa chứng minh hoạt động tốt ở phòng thi mới. Model tốt nhưng pipeline chậm vẫn có thể bỏ qua hành vi ngắn.

## Phạm vi 5 buổi

| Buổi | Trục kiến thức | Sản phẩm học tập |
|---|---|---|
| 1 | Dữ liệu, nhãn, supervised learning, split và leakage | Data card + kế hoạch chia tập |
| 2 | Ảnh/video, object detection, bounding box, confidence, IoU, NMS | 10 nhãn mẫu + phiếu kiểm nhãn |
| 3 | Pose, keypoint, tracking và sự kiện theo thời gian | Sơ đồ hai pipeline + nhãn interval |
| 4 | Deep learning, transfer learning, fine-tune, loss, epoch, overfit | Phiếu đọc `args.yaml` và `results.csv` |
| 5 | Đánh giá, inference, kiến trúc triển khai và lập luận khoa học | Báo cáo mini + giải thích hệ thống |

## Hai buổi thực hành mở rộng nếu có thời gian

**Lab A, 120 phút:** gán nhãn 50–100 ảnh do nhóm tự thu, review chéo, kiểm tra negative/hard negative và xuất thống kê chất lượng nhãn.

**Lab B, 120 phút:** chạy một thí nghiệm đánh giá trên tập đã gán nhãn, cố định model version và threshold, lập bảng TP/FP/FN theo ánh sáng, che khuất và khoảng cách. Đây là hướng mở rộng; chưa được tính là thí nghiệm đã thực hiện.
