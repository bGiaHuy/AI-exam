# Sổ tay học viên: hiểu AI/CV qua project

## 1. Bức tranh lớn

AI là tên chung cho các hệ thống thực hiện công việc thường cần trí tuệ. Machine Learning là cách tạo hành vi bằng việc học quy luật từ dữ liệu. Deep Learning là một nhánh ML dùng mạng nơ-ron nhiều tầng. Computer Vision là lĩnh vực giúp máy xử lý ảnh và video; CV có thể dùng DL nhưng hai từ này không đồng nghĩa.

AI Exam Control chứa cả phần **học từ dữ liệu** và phần **do lập trình viên viết luật**:

- Mô hình phát hiện điện thoại và mô hình pose tạo dự đoán từ ảnh.
- Quy tắc thời gian quyết định chuỗi quay đầu có liên tục không.
- RingBuffer, API, SQLite và giao diện là kỹ thuật phần mềm, không phải model ML.
- Giám thị quyết định xác nhận hoặc bỏ qua sự cố.

Gọi toàn bộ hệ thống là “một mô hình AI” sẽ làm mất những lớp quan trọng này.

## 2. Dữ liệu và nhãn

Một **sample** là một đơn vị dữ liệu đem học hoặc đánh giá, chẳng hạn một ảnh. **Input** là dữ liệu đưa vào model. **Label** hoặc ground truth là đáp án dùng để dạy/đối chiếu. Với object detection, label gồm class và bounding box. Với hành vi theo thời gian, label có thể là một khoảng `start_seconds` đến `end_seconds`.

| Sample | Label | Vai trò |
|---|---|---|
| Ảnh có điện thoại rõ | Box class `phone` | Positive |
| Ảnh không có điện thoại | File nhãn rỗng | Negative |
| Ảnh có máy tính Casio nhưng không có phone | File nhãn rỗng + metadata distractor | Hard negative |
| Ảnh điện thoại bị che một phần | Box theo guideline | Ca khó về occlusion |

Negative không phải dữ liệu “vô ích”. Nếu model chỉ thấy ảnh có điện thoại, nó thiếu ví dụ để học khi nào không nên báo. Hard negative là vật/cảnh dễ gây nhầm, giúp đánh giá và cải thiện model có mục tiêu.

Metadata mô tả điều kiện của sample: camera, phiên, ánh sáng, che khuất, khoảng cách, nguồn và quyền sử dụng. Không nhầm metadata với label. Label nói đáp án nhiệm vụ; metadata giúp tổ chức, chia tập và phân tích nhóm.

## 3. Train, validation, test và leakage

- **Train:** dữ liệu dùng để điều chỉnh weights.
- **Validation:** dữ liệu theo dõi trong phát triển, chọn epoch/hyperparameter/threshold.
- **Test/holdout:** dữ liệu dùng để ước lượng kết quả sau khi đã khóa lựa chọn.

Nếu đã xem kết quả test nhiều lần rồi chỉnh model theo nó, test đó không còn “chưa từng thấy”. Nếu cắt các frame liên tiếp của một video vào cả train và test, hai tập có thể gần giống nhau và tạo kết quả quá lạc quan. Đó là leakage theo session/video. Chỉ kiểm tra hash giống hệt chưa loại trừ ảnh gần trùng.

Project có bằng chứng lịch sử 2.961 ảnh và 3.706 phone boxes, nhưng hồ sơ vẫn ghi thiếu untouched holdout đủ điều kiện. Hai ý này không mâu thuẫn: có tập mang tên test chưa chắc đáp ứng tiêu chuẩn đánh giá độc lập.

## 4. Ảnh, video và object detection

Ảnh là lưới pixel. Ảnh màu thường có nhiều channel. Resolution cho biết số pixel; vật thể ở xa chỉ chiếm ít pixel nên khó giữ chi tiết. Resize về kích thước model có thể làm thay đổi tỷ lệ và chi tiết. Video là chuỗi frame, nhưng camera gửi 15 FPS không có nghĩa model suy luận 15 lần mỗi giây.

Classification trả lời “ảnh này thuộc lớp gì?”. Detection trả lời thêm “vật ở đâu?” bằng bounding box. Dòng nhãn YOLO thường có dạng:

`class_id  x_center  y_center  width  height`

Bốn tọa độ được chuẩn hóa theo chiều rộng/cao ảnh, thường nằm từ 0 đến 1. Với project, class 0 là `phone`. Ảnh negative cần file nhãn rỗng theo protocol, không được bịa box cho calculator hoặc wallet.

**IoU** là diện tích giao chia diện tích hợp của hai box. IoU cao nghĩa hai box chồng khớp tốt hơn. Để gọi một prediction là true positive, quy trình đánh giá cần quy tắc confidence threshold, IoU threshold và ghép một prediction với một ground truth. IoU không đo xác suất gian lận.

**Confidence** dùng để xếp hạng/lọc prediction. Hạ ngưỡng thường giữ nhiều prediction hơn, có thể tăng recall và tăng false positive. Kết quả thực tế phải đo. **NMS** là bước loại các box dự đoán trùng nhau quanh cùng vật thể dựa trên độ chồng lấp và điểm.

## 5. Pose, tracking và hành vi

Pose estimation dự đoán keypoint như mũi, mắt, tai, vai. Keypoint chỉ là tọa độ và điểm tin cậy; chúng chưa tự mang nghĩa “gian lận”. Project dùng dấu hiệu hình học 2D từ pose rồi áp quy tắc thời gian. Vì vậy pipeline quay đầu là hệ lai giữa learned model và heuristic.

Tracking cố nối cùng đối tượng qua các frame và gán `track_id`. ID này có thể mất hoặc đổi khi che khuất, rời khung hay bắt đầu phiên mới. Nó không phải nhận diện khuôn mặt, tên hoặc số báo danh; cũng không nên dùng để đồng nhất một người xuyên camera khi chưa có cơ chế re-identification.

Một frame nghi vấn khác một **event** kéo dài. Tầng thời gian hiện được mô tả với ba điều kiện mặc định:

- tổng thời gian liên tục đạt ít nhất 1,25 giây;
- có ít nhất 3 quan sát nghi vấn;
- khoảng cách giữa hai quan sát liên tiếp không quá 0,75 giây, nếu quá thì reset.

Đây là luật của phần mềm, không phải định nghĩa đạo đức hoặc pháp lý về gian lận. Thay threshold sẽ đổi hành vi hệ thống và phải được đánh giá lại.

## 6. Deep Learning và fine-tune

Mạng nơ-ron nhận input, dùng weights tạo prediction. Khi training, prediction được so với label để tính **loss**. Optimizer dùng gradient để điều chỉnh weights nhằm giảm loss. Cách mô tả này đủ để hiểu vòng lặp; “model tự suy nghĩ” là cách nói sai.

**Pretrained model** đã học trước trên một bộ dữ liệu khác. **Transfer learning** tận dụng những biểu diễn đã học. **Fine-tuning** tiếp tục training model pretrained bằng dữ liệu nhiệm vụ mới. **Inference** chỉ dùng weights đã học để dự đoán, không cập nhật weights. Mở camera chạy model là inference, không phải fine-tune.

| Thuật ngữ | Ý nghĩa |
|---|---|
| Epoch | Một lượt đi qua tập train theo cách loader quy định |
| Batch | Số sample xử lý trước một lần cập nhật gradient |
| Learning rate | Mức bước cập nhật weights |
| Optimizer | Thuật toán dùng gradient để cập nhật weights |
| Augmentation | Biến đổi dữ liệu train để tạo đa dạng hợp lý |
| Checkpoint | Trạng thái weights được lưu tại một thời điểm |
| Resume | Tiếp tục một run từ checkpoint, giữ lại trạng thái phù hợp |
| Overfitting | Học tốt dữ liệu phát triển nhưng tổng quát kém sang dữ liệu mới |
| Underfitting | Mô hình chưa học đủ quy luật ngay cả trên dữ liệu phát triển |

Artifact lịch sử của project ghi `epochs=60`, `batch=6`, `imgsz=960`, optimizer `auto`, có resume từ `last.pt` và `close_mosaic=10`. Đây là bằng chứng về cấu hình run, không phải hướng dẫn mặc định cho mọi lần train. Hồ sơ chưa xác định checkpoint pretrained ban đầu và chưa chứng minh epoch nào trực tiếp sinh ra checkpoint `best.pt` triển khai.

Loss và metric có vai trò khác nhau. Loss là tín hiệu tối ưu trong training. Precision, recall, AP và mAP là cách đo prediction theo protocol. Loss thấp hơn không tự động bảo đảm hiệu quả thực tế tốt hơn, nhất là khi dữ liệu đánh giá không đại diện.

## 7. Đánh giá đúng

Với một operating point đã cố định:

- TP: có sự kiện/vật thể theo nhãn và hệ thống ghép đúng.
- FP: hệ thống báo nhưng không có ground truth phù hợp.
- FN: ground truth có nhưng hệ thống bỏ sót.
- Precision = TP / (TP + FP).
- Recall = TP / (TP + FN).
- F1 là trung bình điều hòa của precision và recall.

Ví dụ học tập: 10 phone thật, tìm đúng 8, báo nhầm 4. Precision = 8/12 ≈ 66,7%; recall = 8/10 = 80%. Đây không phải số liệu project.

AP tóm tắt đường precision–recall khi quét confidence. mAP tổng hợp AP theo lớp hoặc theo nhiều mức IoU tùy protocol. `mAP50 = 0,78578` trong artifact lịch sử mang nhãn `TRAINING_VALIDATION_ONLY`; không được đổi thành “hệ thống chính xác 78,578% trong phòng thi”.

Đánh giá tốt cần phân nhóm: ánh sáng, occlusion, khoảng cách, camera, scene và distractor. Một con số trung bình có thể che khuất nhóm hoạt động kém. Với event quay đầu còn cần quy tắc ghép khoảng thời gian, event precision/recall, onset error hoặc tIoU.

## 8. Từ model đến hệ thống

`camera/video → frame → model → tracking/temporal rule → incident → RingBuffer → file evidence + SQLite → API/UI → human review`

RingBuffer giữ các frame gần nhất để lấy phần trước sự kiện và tiếp tục ghi phần sau. SQLite giữ metadata và đường dẫn, file MP4 giữ video. Queue suy luận ưu tiên dữ liệu mới để tránh backlog; queue DB tuần tự hóa ghi. Model có metric tốt vẫn có thể cho trải nghiệm kém nếu camera, độ trễ, codec, ổ đĩa hoặc UI có lỗi.

Benchmark lịch sử ghi camera/server nhận khoảng 15,58 FPS, nhưng chỉ nhận 354 kết quả trong 125,1 giây, khoảng 2,83 kết quả/giây. Cơ chế thay frame chờ là lựa chọn giảm độ trễ, đồng thời có nghĩa không phải mọi frame đều được suy luận.

## 9. Cách chứng minh mình hiểu

Không cần đọc thuộc lòng. Hãy trả lời bốn lớp:

1. Khái niệm là gì?
2. Nó nằm ở đâu trong project?
3. Bằng chứng nào cho biết project đang làm như vậy?
4. Điều gì còn chưa được đo hoặc chứng minh?

Ví dụ: “Fine-tune là tiếp tục cập nhật weights từ một checkpoint bằng dữ liệu nhiệm vụ. Artifact `args.yaml` cho thấy run lịch sử được resume từ `last.pt`. Tuy nhiên hồ sơ chưa xác định checkpoint pretrained ban đầu, nên em không khẳng định chắc nguồn khởi tạo trước các epoch đầu.”
