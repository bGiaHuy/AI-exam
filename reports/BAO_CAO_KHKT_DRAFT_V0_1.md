# BÁO CÁO NGHIÊN CỨU KHOA HỌC KỸ THUẬT (BẢN THẢO V0.1)

---

**TÊN ĐỀ TÀI DỰ KIẾN:**  
# HỆ THỐNG THỊ GIÁC MÁY TÍNH GIÁM SÁT PHÒNG THI: PHÁT HIỆN HÀNH VI SỬ DỤNG ĐIỆN THOẠI, TƯ THẾ QUAY ĐẦU VÀ TỰ ĐỘNG TRÍCH XUẤT VIDEO BẰNG CHỨNG TRÊN MÁY TRẠM CỤC BỘ

---

**Thông tin tác giả và đơn vị dự thi:**
- **Học sinh thực hiện 1:** `[CẦN NGƯỜI DÙNG XÁC NHẬN: Họ và tên học sinh 1]` — Trường: `[CẦN NGƯỜI DÙNG XÁC NHẬN: Tên trường THPT]`
- **Học sinh thực hiện 2:** `[CẦN NGƯỜI DÙNG XÁC NHẬN: Họ và tên học sinh 2]` — Trường: `[CẦN NGƯỜI DÙNG XÁC NHẬN: Tên trường THPT]`
- **Người hướng dẫn khoa học:** `[CẦN NGƯỜI DÙNG XÁC NHẬN: Họ và tên giáo viên hướng dẫn]` — Đơn vị công tác: `[CẦN NGƯỜI DÙNG XÁC NHẬN: Tên đơn vị]`
- **Lĩnh vực nghiên cứu:** Hệ thống nhúng và Trí tuệ nhân tạo (Robotics and Intelligent Machines / Systems Software)
- **Năm thực hiện:** 2026

---

## MỤC LỤC

1. [Tóm tắt](#1-tóm-tắt)
2. [Đặt vấn đề](#2-đặt-vấn-đề)
3. [Mục tiêu nghiên cứu](#3-mục-tiêu-nghiên-cứu)
4. [Đối tượng và phạm vi nghiên cứu](#4-đối-tượng-và-phạm-vi-nghiên-cứu)
5. [Cơ sở lý thuyết](#5-cơ-sở-lý-thuyết)
6. [Phương pháp nghiên cứu](#6-phương-pháp-nghiên-cứu)
7. [Thiết kế hệ thống](#7-thiết-kế-hệ-thống)
8. [Xây dựng và tích hợp](#8-xây-dựng-và-tích-hợp)
9. [Thực nghiệm và kết quả](#9-thực-nghiệm-và-kết-quả)
10. [Hạn chế và rủi ro tồn dư](#10-hạn-chế-và-rủi-ro-tồn-dư)
11. [Đạo đức và bảo vệ quyền riêng tư](#11-đạo-đức-và-bảo-vệ-quyền-riêng-tư)
12. [Kết luận](#12-kết-luận)
13. [Hướng phát triển](#13-hướng-phát-triển)
14. [Tài liệu tham khảo](#14-tài-liệu-tham-khảo)
15. [Phụ lục](#15-phụ-lục)

---

## 1. TÓM TẮT

*(Mức độ sẵn sàng văn bản: `DRAFTABLE_WITH_CAVEAT`)*

Công tác giám sát phòng thi trong các kỳ thi trực tiếp trên giấy đòi hỏi sự tập trung cao độ liên tục từ giám thị, trong khi các hành vi gian lận như sử dụng điện thoại di động hay quay đầu nhìn bài thường diễn ra chớp nhoáng và khó thu thập tài liệu/video bằng chứng hỗ trợ thẩm định. Nghiên cứu này phát triển một hệ thống thị giác máy tính được thiết kế để xử lý cục bộ trên máy trạm của giám thị nhằm phát hiện sớm hai hành vi vi phạm phổ biến và tự động trích xuất clip bằng chứng video hỗ trợ người giám sát xem xét và thẩm định.

Hệ thống đề xuất kiến trúc hai pipeline bất đồng bộ: Pipeline 1 (RingBuffer, dung lượng mặc định 150 slot) thu nhận luồng video liên tục ở tốc độ danh định 15 FPS; Pipeline 2 (SingleSlotInferenceBuffer) khống chế độ sâu hàng đợi suy luận $\le 1$, đưa khung hình mới nhất vào mô hình YOLO11s (phát hiện điện thoại) và mô hình YOLO11m-Pose kết hợp giải thuật điểm nghi vấn tư thế đầu được chuẩn hóa từ quan hệ hình học giữa các keypoint COCO và bộ đếm thời gian liên tục ($\ge 1.25$ giây) để phát hiện hành vi quay đầu kéo dài. Khi phát hiện dấu hiệu vi phạm mức Cờ Đỏ, hệ thống tự động trích xuất clip bằng chứng MP4 dài khoảng 15 giây (~5 giây trước và ~10 giây sau thời điểm kích hoạt) và ghi bản ghi vào cơ sở dữ liệu SQLite ở chế độ Write-Ahead Logging (WAL).

Thực nghiệm đo đạc E2E trong phiên truyền phát 125,1 giây qua WebSocket nhị phân: Counter `client_backpressure_drops` (map sang `transport_dropped_frames`) không ghi nhận frame bị loại bởi điều kiện socket chưa mở, bufferedAmount > 64KB hoặc lỗi gửi `ws.send()`. Tốc độ thu nhận toàn phiên đạt 15,60 FPS (1.952 frame / 125,1s; giá trị cửa sổ trượt telemetry trung bình 15,88 FPS, P50: 15,00 FPS, P95: 19,00 FPS), và tốc độ suy luận AI toàn phiên đạt 2,29 FPS (287 frame / 125,1s; giá trị cửa sổ telemetry trung bình 2,77 FPS với độ trễ tính toán trung bình 360,4 ms). Cơ chế Single-Slot Inference Buffer chủ động thay thế 1.662 frame trung gian (85,27% số frame nạp) để ngăn ngừa tích lũy trễ hàng đợi, thỏa mãn đẳng thức bảo toàn $287 + 1.662 + 0 = 1.949$. Tại thời điểm kết thúc phép đo, bộ đếm phía client ghi nhận 1.952 frame đã gửi và bộ đếm phía server ghi nhận 1.949 frame đã nhận, chênh lệch 3 frame; artifact hiện có không đủ để xác định nguyên nhân chính xác của chênh lệch này. Hệ thống đã vượt qua 31/31 bài kiểm thử hồi quy backend và 22/22 bài kiểm thử harness đánh giá trong các trường hợp đã cấu hình. Incident schema không yêu cầu tên, SBD, CCCD hoặc email. Runtime không thực hiện nhận diện danh tính và không tạo face embedding. Tuy nhiên, frame và clip có thể chứa hình ảnh nhận dạng được của người dự thi nên vẫn phải được quản lý như dữ liệu cá nhân phù hợp với quy định áp dụng. Các giới hạn về tập kiểm thử độc lập (Khóa chặn D-02) và dữ liệu video thực tế gán nhãn sự kiện (Khóa chặn D-03) được ghi nhận minh bạch làm cơ sở hoàn thiện trong tương lai.

---

## 2. ĐẶT VẤN ĐỀ

Trong các kỳ thi trực tiếp tập trung tại các trường trung học và đại học, tính công bằng và nghiêm túc là yếu tố sống còn để đánh giá đúng năng lực người học. Tuy nhiên, việc giám sát phòng thi hiện nay phần lớn phụ thuộc vào mắt thường của giám thị con người. Mô hình giám sát truyền thống này bộc lộ những thách thức cố hữu:
1. **Sự suy giảm tập trung thị giác (Vigilance Decrement):** Nhiều nghiên cứu tâm lý học lao động đã chứng minh con người không thể duy trì mức độ tập trung thị giác tối đa sau 20–30 phút thực hiện tác vụ giám sát lặp lại `[CẦN TRÍCH DẪN — CHƯA XÁC MINH: Mackworth, 1948; Warm et al., 2008]`. Giám thị rất dễ bỏ sót các hành vi che giấu tinh vi trong phòng thi từ 24 đến 40 thí sinh.
2. **Tính chất chớp nhoáng của hành vi gian lận:** Việc lén sử dụng điện thoại di động dưới ngăn bàn hoặc nghiêng đầu liếc nhìn bài của thí sinh bên cạnh thường chỉ diễn ra trong vài giây khi giám thị di chuyển hoặc quan sát hướng khác.
3. **Thiếu dữ liệu video ghi nhận thời gian thực để đối soát:** Khi giám thị bắt quả tang bằng mắt thường nhưng không có ghi hình lại mốc thời gian vi phạm, việc lập biên bản thường dẫn đến tranh cãi, khiếu nại kéo dài từ phía thí sinh và phụ huynh.
4. **Mối lo ngại về quyền riêng tư và an toàn dữ liệu:** Các giải pháp camera thông minh dựa trên điện toán đám mây (Cloud AI) hoặc nhận diện danh tính sinh trắc học khuôn mặt tiềm ẩn nguy cơ rò rỉ hình ảnh nhạy cảm của học sinh và vi phạm các quy định bảo vệ dữ liệu cá nhân.

Từ thực tiễn trên, việc nghiên cứu một giải pháp phần mềm hỗ trợ giám thị ứng dụng thị giác máy tính được thiết kế cho mô hình triển khai cục bộ (On-Premise / Offline-First), không lưu trữ danh tính cá nhân, và tự động trích xuất clip bằng chứng ngắn hỗ trợ người giám sát xem xét là một bài toán khoa học và thực tiễn có ý nghĩa cấp thiết.

---

## 3. MỤC TIÊU NGHIÊN CỨU

### 3.1. Mục tiêu Tổng quát
Nghiên cứu, thiết kế và phát triển thử nghiệm một hệ thống thị giác máy tính hỗ trợ giám thị phát hiện hành vi sử dụng điện thoại và tư thế quay đầu nhìn bài trong phòng thi giấy, tự động trích xuất clip bằng chứng video, vận hành thời gian thực trên máy trạm cục bộ theo mô hình phối hợp Người - Máy.

### 3.2. Mục tiêu Cụ thể
1. Tích hợp và đánh giá mô hình học sâu phát hiện thiết bị di động trong khu vực làm bài thi.
2. Xây dựng giải thuật phân tích hình học dựa trên điểm mốc tư thế (Pose Keypoints) kết hợp bộ lọc thời gian để phân biệt cử động vô thức với hành vi quay đầu nhìn bài kéo dài.
3. Thiết kế kiến trúc hai pipeline bất đồng bộ giải quyết bài toán mâu thuẫn giữa tốc độ thu nhận luồng video (15 FPS) và tốc độ suy luận của mô hình AI trên phần cứng máy trạm.
4. Xây dựng cơ chế trích xuất clip bằng chứng tự động (~5 giây trước và ~10 giây sau) và lưu trữ dữ liệu ẩn danh an toàn trên cơ sở dữ liệu SQLite cục bộ.
5. Phát triển giao diện trực quan cho giám thị theo dõi trực tiếp, thẩm định clip bằng chứng và thực hiện hành động Xác nhận hoặc Bỏ qua.

---

## 4. ĐỐI TƯỢNG VÀ PHẠM VI NGHIÊN CỨU

### 4.1. Đối tượng Nghiên cứu
- Luồng dữ liệu video giám sát từ camera quan sát thí sinh trong phòng thi.
- Dấu hiệu hình ảnh của thiết bị di động (điện thoại thông minh) trong không gian bàn thi.
- Tư thế phần thân trên và điểm nghi vấn chuyển động đầu của thí sinh qua các khung hình liên tiếp.

### 4.2. Phạm vi Nghiên cứu
- **Bối cảnh áp dụng:** Phòng thi trực tiếp trên giấy (in-person paper exams).
- **Môi trường thực thi:** Runtime hiện tại được thiết kế để xử lý cục bộ và không có phụ thuộc cloud được xác định trong luồng chính (On-Premise / localhost), không kết nối mạng diện rộng.
- **Nguồn video đầu vào:** Một luồng camera (webcam hoặc file video mô phỏng phòng thi) được truyền từ trình duyệt qua WebSocket.

### 4.3. Giới hạn Không Thuộc Phạm vi Nghiên cứu (Explicit Out-of-Scope)
Để đảm bảo tính khả thi và đạo đức nghiên cứu, hệ thống **tuyệt đối không thực hiện**:
- Không nhận diện danh tính thí sinh (không có thông tin Họ tên, Số báo danh, Số CCCD).
- Không nhận diện khuôn mặt hay trích xuất vector sinh trắc học (không sử dụng FaceNet).
- Không sử dụng mô hình ngôn ngữ lớn (LLM), RAG hay chatbot tra cứu quy chế.
- Không tự động lập văn bản biên bản kỷ luật hay chữ ký số.
- Không tự động ra quyết định đình chỉ thi (quyền quyết định thuộc về giám thị con người).
- Không quản lý tập trung nhiều phòng thi trên máy chủ đám mây.

---

## 5. CƠ SỞ LÝ THUYẾT

*(Mức độ sẵn sàng văn bản: `DRAFTABLE_PENDING_CITATIONS`)*

### 5.1. Mô hình Học sâu và Framework YOLO trong Phát hiện Vật thể
Họ mô hình YOLO (You Only Look Once) được khởi xướng bởi Redmon et al. (2016) `[CẦN TRÍCH DẪN — CHƯA XÁC MINH: Redmon et al., 2016]`, chuyển bài toán phát hiện vật thể từ mô hình phân loại theo vùng đề xuất sang bài toán hồi quy điểm ảnh đơn lẻ. Trong nghiên cứu này, framework Ultralytics YOLO `[CẦN TRÍCH DẪN — CHƯA XÁC MINH: Jocher et al., Ultralytics]` được sử dụng cho cả bài toán phát hiện vật thể (YOLO11s) và ước lượng tư thế (YOLO11m-Pose). Kiến trúc mạng áp dụng cơ chế Anchor-Free kết hợp bộ gán nhãn Task-Aligned Assigner, giúp mô hình cải thiện khả năng dự đoán bounding box cho các vật thể kích thước nhỏ như điện thoại di động ngay cả khi bị che khuất một phần bởi bàn tay hoặc tài liệu thi.

### 5.2. Ước lượng Điểm Mốc Cơ thể Người (Pose Keypoints Estimation)
Mô hình ước lượng tư thế xác định tọa độ không gian hai chiều $(x_i, y_i)$ và độ tin cậy $c_i$ của 17 điểm mốc giải phẫu cơ thể người theo định dạng chuẩn COCO Keypoints `[CẦN TRÍCH DẪN — CHƯA XÁC MINH: Lin et al., 2014; Cao et al., 2017]`. Trong bài toán phòng thi, các điểm mốc vùng đầu và vai đóng vai trò quyết định để suy diễn hướng nhìn:
$$\mathcal{K}_{\text{head}} = \{ \text{Mũi (0)}, \text{Mắt trái (1)}, \text{Mắt phải (2)}, \text{Tai trái (3)}, \text{Tai phải (4)}, \text{Vai trái (5)}, \text{Vai phải (6)} \}$$

### 5.3. Thuật toán Bám vết Đối tượng Ẩn danh (ByteTrack)
Để duy trì nhận diện một thí sinh qua các khung hình mà không cần nhận diện khuôn mặt, thuật toán ByteTrack thực hiện liên kết đối tượng dựa trên độ tương đồng không gian (Intersection over Union - IoU) của bounding box kết hợp bộ lọc Kalman Filter `[CẦN TRÍCH DẪN — CHƯA XÁC MINH: Zhang et al., 2022]`. ByteTrack tận dụng cả các phát hiện có điểm tin cậy thấp để hạn chế đứt quãng vết (track fragmentation) khi thí sinh cúi người viết bài.

### 5.4. Tính Bền vững Giao dịch CSDL với Chế độ Write-Ahead Logging (WAL)
Trong các hệ thống thị giác máy tính ghi dữ liệu sự cố liên tục, cơ chế khóa truyền thống của SQLite dễ gây ra lỗi khóa bàn cờ (`database is locked`). Chế độ Write-Ahead Logging (WAL) giải quyết vấn đề này bằng cách ghi các thay đổi vào tệp nhật ký riêng biệt `cheating_system.db-wal`, cho phép các tiến trình đọc (Reader) và một tiến trình ghi (Writer) hoạt động đồng thời mà không chặn lẫn nhau `[CẦN TRÍCH DẪN — CHƯA XÁC MINH: Owens, 2006; SQLite Consortium]`.

---

## 6. PHƯƠNG PHÁP NGHIÊN CỨU

### 6.1. Dữ liệu Huấn luyện và Truy vết Nguồn gốc (Dataset Lineage)
Mô hình phát hiện điện thoại `phone_detector_v5.pt` kế thừa từ quá trình huấn luyện có kiểm soát trên tập dữ liệu tổng hợp `phone_merged`. Dựa trên kết quả đối soát bằng chứng Pass 1.3 tại `reports/evidence/training_lineage/`:
- **Quy mô tập dữ liệu:** Gồm **2.961 ảnh** và **3.706 nhãn bounding box điện thoại**.
- **Phân chia tập dữ liệu:**
  - Tập Huấn luyện (Train): 2.434 ảnh (3.042 nhãn).
  - Tập Kiểm định (Validation): 382 ảnh (490 nhãn).
  - Tập Kiểm thử Nội bộ (Internal Test): 145 ảnh (174 nhãn).
- **Nguồn gốc dữ liệu nguồn:** Tương ứng theo tên tệp và cấu trúc phân chia từ 3 gói Roboflow mở thuộc tác giả `du-tran` (giấy phép CC BY 4.0): `mobilephone` v3 (963 ảnh), `mobilephone2` v1 (1.000 ảnh), `mobilephone3` v1 (998 ảnh).
- **Siêu tham số huấn luyện của run cuối:**
  - Kiến trúc: `YOLO11s`, single class `{0: 'phone'}`.
  - Kích thước ảnh (`imgsz`): $960 \times 960$ pixel.
  - Kích thước lô (`batch`): 6, trình tối ưu hóa `optimizer: auto`.
  - Hạt giống ngẫu nhiên: `seed = 0`, `deterministic: True`, `close_mosaic = 10`.
- **Dấu vết tiếp tục huấn luyện:** Tệp `args.yaml` ghi nhận `resume: last.pt` và cột thời gian trong `results.csv` reset từ 1.219,98s về 119,816s tại epoch 6, chứng minh quá trình huấn luyện đã được resume ít nhất một lần trước epoch 6.
- **Đối chiếu mã băm artifact:** Tệp trọng số triển khai `phone_detector_v5.pt` (19.245.082 byte) có cùng mã băm SHA-256 (`23fa698727a49cb8ba7d260c1ac13f01d4d27e8726e97aa3d8fef992ad5e19c2`) với artifact `best.pt` được xác định trong run `phone_detector_v5`.
- *Caveat khoa học:* Checkpoint tiền huấn luyện ban đầu mang trạng thái `UNRESOLVED`; epoch trực tiếp sinh ra `best.pt` mang trạng thái `UNRESOLVED`. Kiểm tra rò rỉ xác nhận 0 va chạm mã băm exact-hash giữa các tập, nhưng rò rỉ gần giống (near-duplicate) cấp video session chưa được kiểm tra.

### 6.2. Giải thuật Điểm Nghi vấn Tư thế Đầu Chuẩn hóa từ Hình học Keypoint COCO

Hệ thống tính toán điểm nghi vấn tư thế đầu được chuẩn hóa từ quan hệ hình học 2D giữa các keypoint COCO của mô hình `yolo11m-pose.pt`, hoàn toàn không ước lượng góc quay vật lý 3D trong không gian:

1. **Điều kiện Độ tin cậy Điểm mốc (Keypoint Confidence Thresholds):**
   - Vai trái ($k_5$), vai phải ($k_6$): $\text{conf} > 0.25$.
   - Mắt trái ($k_1$), mắt phải ($k_2$): $\text{conf} > 0.25$.
   - Tai trái ($k_3$), tai phải ($k_4$): $\text{conf} > 0.25$.
   - Mũi ($k_0$): $\text{conf} > 0.25$.
   - Cổ tay trái ($k_9$), cổ tay phải ($k_{10}$): $\text{conf} > 0.30$.
   - Điều kiện có mặt khuôn mặt (`face_present`): $\text{has\_eyes} \lor (\text{has\_nose} \land (\text{has\_left\_ear} \lor \text{has\_right\_ear}))$.

2. **Làm mượt Tọa độ Điểm mốc (`KeypointSmoother`):**
   Tọa độ pixel $(x, y)$ của các điểm mốc giữa các khung hình liên tiếp có độ tin cậy $> 0.15$ được làm mượt bằng bộ lọc Exponential Moving Average (EMA) với hệ số $\alpha = 0.75$:
   $$\mathbf{p}_t = \alpha \cdot \mathbf{p}_t^{\text{raw}} + (1 - \alpha) \cdot \mathbf{p}_{t-1}, \quad \text{với } \alpha = 0.75$$
   *Lưu ý liêm chính khoa học:* Bộ lọc EMA chỉ áp dụng trên tọa độ pixel $(x, y)$ nhằm giảm hiện tượng rung giật điểm mốc (landmark jitter) theo ý đồ thiết kế, chưa có nghiên cứu thực nghiệm định lượng (ablation study) trên tập nhãn chuẩn.

3. **Trích xuất Đặc trưng Hình học Chiếu 2D:**
   - **Góc nghiêng thân người (`body_score`):**  
     Góc vai $\theta_{\text{sh}} = \text{atan2}(y_{\text{l\_sh}} - y_{\text{r\_sh}}, x_{\text{l\_sh}} - x_{\text{r\_sh}})$. Độ lệch chuẩn với baseline thân người: $\text{dev} = |\theta_{\text{sh}} - \theta_{\text{baseline}}|$ (chuẩn hóa về $[0, \pi]$).  
     Nếu $\text{dev} \ge 18^\circ$: $\text{body\_score} = \min((\text{dev} - 18.0) / 18.0, 1.0)$, ngược lại $= 0.0$.
   - **Đặc trưng quay đầu (`head_turn_score`):**  
     - *Trường hợp A (Đầy đủ mũi và hai mắt, $d_{\text{eye}} > 5.0$ px):*  
       Vector mắt $\hat{\mathbf{v}}_{\text{eyes}} = (\mathbf{p}_{\text{l\_e}} - \mathbf{p}_{\text{r\_e}}) / d_{\text{eye}}$, vector mũi $\mathbf{v}_n = \mathbf{p}_{\text{nose}} - \mathbf{m}_{\text{eyes}}$.  
       Độ lệch tâm: $\text{symmetry\_offset} = |\mathbf{v}_n \cdot \hat{\mathbf{v}}_{\text{eyes}}| / (d_{\text{eye}} / 2)$.  
       Tỷ lệ khoảng cách: $\text{sym\_ratio} = \min(d_l, d_r) / \max(d_l, d_r)$ với $d_l = \|\mathbf{p}_{\text{nose}} - \mathbf{p}_{\text{l\_e}}\|, d_r = \|\mathbf{p}_{\text{nose}} - \mathbf{p}_{\text{r\_e}}\|$.  
       Nếu $\text{symmetry\_offset} < 0.24 \land \text{sym\_ratio} \ge 0.58$: tư thế nhìn thẳng trực diện, $\text{yaw\_score} = 0.0, \text{detected\_yaw\_deg} = 0.0$.  
       Nếu $\text{symmetry\_offset} \ge 0.28 \lor \text{sym\_ratio} < 0.52$:  
       $s_{\text{off}} = \min(\max(\text{symmetry\_offset} - 0.28, 0.0) / 0.35, 1.0)$; $s_{\text{rat}} = \min(\max(0.52 - \text{sym\_ratio}, 0.0) / 0.28, 1.0)$.  
       $\text{yaw\_score} = \max(s_{\text{off}}, s_{\text{rat}})$; $\text{detected\_yaw\_deg} = \max(\text{symmetry\_offset} \times 60.0, (1.0 - \text{sym\_ratio}) \times 60.0)$.  
     - *Trường hợp B (Đeo khẩu trang che mũi, có hai mắt và hai tai):*  
       $\text{ear\_eye\_offset} = \|\mathbf{m}_{\text{eyes}} - \mathbf{m}_{\text{ears}}\| / d_{\text{eye}}$.  
       Nếu $\text{ear\_eye\_offset} \ge 0.35$: $\text{yaw\_score} = \min((\text{ear\_eye\_offset} - 0.35) / 0.30, 1.0)$; $\text{detected\_yaw\_deg} = \text{ear\_eye\_offset} \times 50.0$.  
     - *Trường hợp C (Bất đối xứng che khuất tai):*  
       Khi có mặt nhưng không nhìn thẳng, nếu một bên tai có $\text{conf} > 0.35$ và tai đối diện $< 0.15$: $\text{ear\_asym\_score} = 0.65$.  
     $\text{head\_turn\_score} = \max(\text{yaw\_score}, \text{ear\_asym\_score})$.
   - **Chỉ số trực quan hóa `turn_deg`:**  
     $$\text{turn\_deg} = \begin{cases} \text{detected\_yaw\_deg} & \text{nếu } \text{head\_turn\_score} > 0.15 \land \text{detected\_yaw\_deg} > 0 \\ \text{head\_turn\_score} \times 45.0 & \text{nếu } \text{head\_turn\_score} > 0.15 \land \text{detected\_yaw\_deg} = 0 \\ 0.0 & \text{nếu } \text{head\_turn\_score} \le 0.15 \end{cases}$$  
     *Lưu ý kỹ thuật:* Tên trường `turn_deg` là tên trường tương thích giao diện; giá trị là chỉ số trực quan hóa suy ra từ heuristic, không phải phép đo góc vật lý.
   - **Độ lệch ngang đầu (`lateral_drift_score`):**  
     Hình chiếu vector từ tâm vai tới tâm đầu lên trục vai $\text{proj}_x$. Tỷ số $\text{lateral\_ratio} = |\text{proj}_x| / (d_{\text{sh}} / 2)$.  
     Nếu $\text{lateral\_ratio} \ge 0.38$: $\text{lateral\_drift\_score} = \min((\text{lateral\_ratio} - 0.38) / 0.25, 1.0)$.
   - **Mất mặt trước (`face_lost_score`):**  
     Nếu $\neg \text{face\_present}$: $\text{face\_lost\_score} = 0.80$ (quay lưng nhìn lại - TurnBack) nếu $\text{body\_score} \ge 0.30$; hoặc $= 0.70$ (nhìn nghiêng - SideView) nếu $\text{lateral\_ratio} \ge 0.30 \lor \text{body\_score} \ge 0.20$ hoặc góc nghiêng hai tai lệch trục vai $\ge 22^\circ$.
   - **Vươn tay bất thường (`wrist_score`):**  
     Nếu khoảng cách cổ tay tới tâm vai $> 1.30 \cdot d_{\text{sh}}$: $\text{wrist\_score} = \min((\text{ratio} - 1.30) / 0.45, 1.0)$.

4. **Logic Phán quyết Phân tầng Đồng thuận (Tiered Consensus Scoring):**  
   $$\text{primary\_violation} = \max(\text{head\_turn\_score}, \text{face\_lost\_score}, \text{wrist\_score})$$  
   $$\text{final\_score} = \begin{cases} \text{primary\_violation} & \text{nếu } \text{primary\_violation} \ge 0.55 \\ 0.65 & \text{nếu } \text{head\_turn\_score} \ge 0.35 \land \text{body\_score} \ge 0.30 \\ 0.60 & \text{nếu } \text{head\_turn\_score} \ge 0.35 \land \text{lateral\_drift\_score} \ge 0.40 \\ 0.65 & \text{nếu } \text{head\_turn\_score} \ge 0.35 \land \text{wrist\_score} \ge 0.35 \\ 0.60 & \text{nếu } \text{body\_score} \ge 0.65 \\ 0.0 & \text{các trường hợp còn lại} \end{cases}$$

5. **Quy tắc Chuyển trạng thái Thời gian Thực (Temporal State Transition):**  
   - Ngưỡng kích hoạt tức thời: $\text{is\_instant\_suspicious} = (\text{final\_score} \ge \text{suspicion\_threshold})$ (mặc định 0.50).  
   - Cập nhật bộ đếm:  
     $$\text{suspicion\_count}_{t} = \begin{cases} \text{suspicion\_count}_{t-1} + 1 & \text{nếu } \text{is\_instant\_suspicious} \\ \max(0, \text{suspicion\_count}_{t-1} - 3) & \text{ngược lại} \end{cases}$$  
   - Điều kiện leo thang Cờ Đỏ (`is_cheating_sustained`):  
     $$\text{suspicion\_count} \ge \text{alert\_frames} \quad (\text{với } \text{alert\_frames} = \text{int}(\text{fps} \times \text{posture\_alert\_seconds}) = \text{int}(15 \times 1.25) \approx 18 \text{ frames})$$  
   - **Điều kiện tạo sự cố và xuất clip:**  
     - **Cờ Vàng:** $\text{is\_instant\_suspicious} == \text{True}$ (chỉ gửi tín hiệu HUD, không tạo clip).  
     - **Cờ Đỏ:** $\text{is\_cheating\_sustained} == \text{True}$ HOẶC phát hiện điện thoại $\text{has\_phone} == \text{True}$ (tạo incident trong SQLite và trích xuất clip bằng chứng ~15s từ RingBuffer).

6. **Phân định Mức độ Kiểm chứng:**  
   Giải thuật đã được kiểm chứng qua rà soát mã nguồn (code inspection) và bài kiểm thử giả lập (synthetic tests trong `backend/tests/test_refactored_system.py`). Việc đo đạc định lượng trên tập video phòng thi thực tế gán nhãn sự kiện chưa được thực hiện và đang được quản lý dưới dạng Khóa chặn độc lập **`D-03 OPEN`**.

---

## 7. THIẾT KẾ HỆ THỐNG

### 7.1. Kiến trúc Hai Pipeline Bất đồng bộ (Decoupled Dual-Pipeline Architecture)
Trong xử lý video thời gian thực kết hợp học sâu, tốc độ suy luận của mô hình (Inference FPS) thường biến động và chậm hơn tốc độ thu nhận của camera (Acquisition FPS). Nếu dùng kiến trúc đơn luồng tuần tự, hệ thống sẽ bị rớt khung hình video bằng chứng hoặc gây trễ tích lũy hàng đợi. Nghiên cứu đề xuất giải pháp tách rời thành hai pipeline độc lập:

1. **Pipeline 1 — Thu nhận Video Không Mất mát (RingBuffer):**  
   - Hàng đợi vòng tròn (circular buffer) với dung lượng mặc định 150 slot trong RAM (tương ứng khoảng 10 giây khung hình ở tốc độ danh định 15 FPS, có thể cấu hình khi khởi tạo).
   - Hoạt động tách rời với pipeline AI, đảm bảo video bằng chứng luôn đầy đủ, mượt mà và không bị giật lag.
2. **Pipeline 2 — Hàng đợi Suy luận Khung hình Mới nhất (SingleSlotInferenceBuffer):**  
   - Hàng đợi suy luận được giới hạn độ sâu tối đa: $\text{Backlog Depth} \le 1$.
   - Các frame trung gian được thay thế có chủ đích trong single-slot inference buffer để worker luôn xử lý frame mới nhất; đây không phải lỗi truyền tải.
   - Giải pháp này đảm bảo worker AI không tích lũy trễ sau thời gian vận hành dài.

### 7.2. Giao thức Truyền vận WebSocket Nhị phân (Binary Ingestion Protocol)
Luồng video từ trình duyệt được gửi qua kết nối WebSocket nhị phân với cấu trúc gói tin tối ưu kích thước 16-byte header:
```
[Bytes 0-7: Sequence Uint64 (Big-Endian)] [Bytes 8-15: Client Monotonic Timestamp Double (Big-Endian)]
[Bytes 16...: JPEG Image Data]
```
Tại máy chủ, mốc thời gian nhận thực tế được gắn bằng đồng hồ đơn điệu `time.monotonic()` của server để đảm bảo tính tăng đơn điệu, không bị ảnh hưởng bởi hiện tượng lệch đồng hồ Client.

### 7.3. Quy trình Trích xuất Video Bằng chứng Tự động (Evidence Extraction Workflow)
- Khi sự cố Cờ Đỏ phát sinh (phát hiện điện thoại hoặc quay đầu $\ge 1.25$s), bộ quản lý gửi lệnh yêu cầu cắt clip tới `RingBuffer` kèm mã định danh sự cố duy nhất: `inc_{timestamp_ms}_{hex}.mp4`.
- `RingBuffer` khóa các khung hình quá khứ (mặc định cấu hình ~5 giây pre-roll, tức 75 frame ở 15 FPS) và tiếp tục thu thập các khung hình kế tiếp (mặc định cấu hình ~10 giây post-roll, tức 150 frame ở 15 FPS), kèm thời gian giãn cách `cooldown_seconds` (mặc định 6.0 giây).
- *Lưu ý về tính khả biến cấu hình:* Các mốc pre-roll (5.0s), post-roll (10.0s), cooldown (6.0s), phone confidence threshold (0.35 - 0.50) và posture alert duration (1.25s) là các tham số cấu hình thời gian chạy (`AISettingsSchema`, có thể tùy biến qua `/api/settings/ai`), không phải hằng số cứng bất biến của mã nguồn.
- Thuật toán tái tạo mẫu trên lưới thời gian (time-grid resampling) tính toán khoảng thời gian thực tế giữa các frame để ghi tệp MP4 H.264 với tốc độ phát tự nhiên 1.0x.
- Tệp video được kiểm tra tính hợp lệ bằng OpenCV trước khi lưu đường dẫn vào cơ sở dữ liệu.

### 7.4. Lược đồ Cơ sở Dữ liệu và Concurrency An toàn Luồng
- Bảng `incidents` trong SQLite:
  - `id` (Khóa chính, chuỗi ký tự ngẫu nhiên duy nhất).
  - `student_id` (Track ID ẩn danh tạm thời, ví dụ: "Track 3").
  - `violation_type` (Thuộc tập giá trị chuẩn hóa: `PHONE`, `HEAD_TURNING`).
  - `severity` (`red` hoặc `yellow`).
  - `timestamp` (Thời gian UTC theo định dạng ISO 8601).
  - `status` (`pending`, `confirmed`, `dismissed`).
  - `evidence_url` (Đường dẫn tệp video, ví dụ: `./data/evidence/inc_*.mp4`).
  - `confidence` (Điểm số tin cậy trong đoạn $[0.0, 1.0]$).
- Cơ chế ghi bất đồng bộ qua `DBWriteQueue`: Các sự cố từ pipeline AI được đẩy vào hàng đợi bộ nhớ luồng an toàn. Một tác vụ nền tuần tự hóa các truy vấn INSERT/UPDATE vào SQLite ở chế độ WAL, giảm thiểu nguy cơ tranh chấp khóa ghi trong các trường hợp đã kiểm thử.

---

## 8. XÂY DỰNG VÀ TÍCH HỢP

### 8.1. Backend API (FastAPI)
- Nền tảng Python 3.12, framework FastAPI, phục vụ các endpoint RESTful và luồng WebSocket:
  - `WS /api/ws/video-feed`: Điểm thu nhận luồng video nhị phân.
  - `GET /api/incidents`: Trả về danh sách sự cố phục vụ giao diện giám thị.
  - `PATCH /api/incidents/{id}`: Cập nhật trạng thái sự cố sang `confirmed` hoặc `dismissed`.
  - `GET /evidence/{filename}`: Static route phục vụ video bằng chứng với cơ chế chống tấn công duyệt thư mục trái phép (`Path Traversal`).
  - `GET /api/session/telemetry`: Cung cấp các thông số hiệu năng và bảo toàn bất biến thời gian thực.
- Các endpoint kiểm thử (`POST /api/test/trigger_incident`) và ingest Base64 cũ (`POST /api/detect/frame`) được cô lập sau các cờ môi trường (`ENABLE_TEST_ENDPOINTS=false`, `ENABLE_DEPRECATED_INGEST=false`), mặc định trả về 404 và ẩn khỏi tài liệu OpenAPI.
- Tuyến đường cũ `/api/clips/{filename}` được chuyển vào `legacy_clips_router`, mặc định vô hiệu hóa qua cờ `ENABLE_LEGACY_CLIPS=false`.

### 8.2. Giao diện Giám thị (Streamlined Proctor Dashboard)
- Xây dựng bằng React 19 (`19.0.1`), ngôn ngữ TypeScript với chế độ kiểm tra kiểu tĩnh nghiêm ngặt (`tsc --noEmit`).
- Thiết kế giao diện tuân thủ quy chuẩn Anti-Slop: bảng màu trung tính tối (Zinc-950 / Zinc-900), phông chữ hệ thống tiêu chuẩn, độ mật dữ liệu cao, các đường viền sắc nét 1px (`border-zinc-800`).
- Tích hợp Canvas overlay vẽ trực tiếp bounding box điện thoại và khung xương tư thế 17 điểm mốc trên luồng camera.
- Hộp thoại xem lại video bằng chứng (Video Evidence Review Modal) cho phép phát lại clip MP4 15 giây từ endpoint `/evidence/{filename}` và thực hiện hai thao tác:
  - **Xác nhận (`Confirm`):** Lưu trạng thái `confirmed`, bảo toàn tệp MP4 trên đĩa.
  - **Bỏ qua (`Dismiss`):** Lưu trạng thái `dismissed`, tệp evidence được xóa trong workflow dismiss ở trường hợp đã kiểm thử.

---

## 9. THỰC NGHIỆM VÀ KẾT QUẢ

### 9.1. Thực nghiệm Hiệu năng Thu nhận và Truyền vận End-to-End (E2E Benchmark)
Bài đo đạc chuẩn hóa đã được thực thi trên môi trường máy trạm cục bộ trong thời gian 125,1 giây liên tục với luồng video mô phỏng webcam mục tiêu 15 FPS. Dưới đây là bảng phân tích toàn bộ chỉ số từ artifact thô (`e2e_benchmark_result.json`), phân định rõ giữa tốc độ trung bình toàn phiên và telemetry cửa sổ trượt:

| Nhóm chỉ số | Tên chỉ số | Trường dữ liệu thô / Công thức | Giá trị ghi nhận | Diễn giải kỹ thuật và Ngữ nghĩa |
| :--- | :--- | :--- | :--- | :--- |
| **Toàn phiên (Global)** | Thời gian phiên đo | `session_duration_seconds` | **125,1 s** | Tổng thời gian truyền phát liên tục của phiên thử nghiệm |
| **Toàn phiên (Global)** | Khung hình thu nhận | `total_capture_frames` | **1.952 frames** | Toàn bộ khung hình video được trích xuất từ camera phía client |
| **Toàn phiên (Global)** | Tốc độ thu nhận toàn phiên | $1952 / 125,1\text{ s}$ | **15,60 FPS** | Tốc độ capture trung bình thực tế toàn phiên phía client |
| **Toàn phiên (Global)** | Khung hình đã gửi | `total_sent_frames` | **1.952 frames** | Client đóng gói nhị phân và gửi đi toàn bộ 1.952 frame đã capture |
| **Toàn phiên (Global)** | Tốc độ gửi toàn phiên | $1952 / 125,1\text{ s}$ | **15,60 FPS** | Tốc độ gửi trung bình qua WebSocket phía client |
| **Toàn phiên (Global)** | Khung hình máy chủ nhận | `total_server_received_frames` | **1.949 frames** | Máy chủ nhận và giải mã JPEG thành công |
| **Toàn phiên (Global)** | Tốc độ nhận toàn phiên | $1949 / 125,1\text{ s}$ | **15,58 FPS** | Tốc độ nhận và xử lý nhị phân trung bình tại máy chủ |
| **Toàn phiên (Global)** | Khung hình đưa vào suy luận | `inference_submitted_frames` | **1.949 frames** | Khung hình được nạp vào Single-Slot Inference Buffer |
| **Toàn phiên (Global)** | Khung hình thay thế an toàn | `inference_superseded_frames` | **1.662 frames** (85,27%) | Frame trung gian bị ghi đè có chủ đích trong buffer đơn slot |
| **Toàn phiên (Global)** | Khung hình hoàn thành tại server | `inference_processed_frames` | **287 frames** | $1949 - 1662 = 287$ frame hoàn thành xử lý tại worker |
| **Toàn phiên (Global)** | Tốc độ suy luận toàn phiên | $287 / 125,1\text{ s}$ | **2,29 FPS** | Thông lượng xử lý suy luận AI thực tế toàn phiên trên CPU |
| **Toàn phiên (Global)** | Khung hình chờ xử lý | `inference_pending_frames` | **0 frames** | Hàng đợi rỗng tại thời điểm kết thúc phiên |
| **Toàn phiên (Global)** | Kết quả detection nhận tại client | `detection_results_received` | **354 kết quả** | Số thông điệp kết quả detection nhận được tại client qua WebSocket |
| **Tầng truyền vận** | Khung hình loại bỏ phía client | `client_backpressure_drops` (map: `transport_dropped_frames`) | **0 frames** (`0.00%`) | Counter `client_backpressure_drops` (map sang `transport_dropped_frames`) không ghi nhận frame bị loại bởi điều kiện socket chưa mở, bufferedAmount > 64KB hoặc lỗi ws.send() trong phiên kiểm thử |
| **Cửa sổ trượt (Rolling)** | Tốc độ thu nhận Client (Mean) | `acquisition_fps_mean` | **15,88 FPS** | Tốc độ capture tính trên sliding window 15 frame của client |
| **Cửa sổ trượt (Rolling)** | Tốc độ thu nhận Client (P50/P95)| `acquisition_fps_p50` / `_p95` | **15,00 / 19,00 FPS** | Phân vị P50 và P95 của chu kỳ capture phía client |
| **Cửa sổ trượt (Rolling)** | Tốc độ suy luận AI (CPU Window) | `inference_fps_mean` | **2,77 FPS** | Trung bình của các mẫu tức thời tốc độ suy luận worker trên CPU |
| **Cửa sổ trượt (Rolling)** | Độ trễ khứ hồi E2E | `mean_latency_ms` | **360,4 ms** | Độ trễ tính toán tức thời từ mốc gửi client đến nhận kết quả |

**Các nhận định và phân tích kỹ thuật chuẩn mực:**
1. **Chênh lệch giữa số frame gửi và nhận:**  
   Tại thời điểm kết thúc phép đo, bộ đếm phía client ghi nhận 1.952 frame đã gửi và bộ đếm phía server ghi nhận 1.949 frame đã nhận, chênh lệch 3 frame. Artifact hiện có không đủ để xác định nguyên nhân chính xác của chênh lệch này.
2. **Ngữ nghĩa của counter dropped:**  
   Counter `client_backpressure_drops` (map sang `transport_dropped_frames`) không ghi nhận frame bị loại bởi điều kiện socket chưa mở, bufferedAmount > 64KB hoặc lỗi ws.send() trong phiên kiểm thử.
3. **Đẳng thức bảo toàn số học:**  
   Toàn bộ khung hình đưa vào pipeline suy luận tuân thủ nghiêm ngặt đẳng thức bảo toàn:
   $$\text{processed } (287) + \text{superseded } (1662) + \text{pending } (0) = \text{submitted } (1949)$$
   Cơ chế thay thế khung hình (`superseded`, chiếm 85,27% số frame nạp) là thiết kế chủ động của `SingleSlotInferenceBuffer` nhằm ngăn ngừa tích lũy trễ hàng đợi khi worker AI trên CPU có thông lượng (~2,29 FPS) thấp hơn tốc độ nạp (15,58 FPS), đảm bảo worker luôn xử lý khung hình mới nhất; đây không phải lỗi hệ thống hay mất gói mạng.
4. **Bảo toàn 4 bất biến telemetry (Inv 4, 5, 6, 7):** Đạt tỷ lệ thỏa mãn tuyệt đối trong suốt phiên kiểm thử, tuân thủ nghiêm ngặt các đẳng thức bảo toàn số học.

### 9.2. Kết quả Kiểm thử Tự động Phần mềm
Hệ thống đã được kiểm chứng qua các bộ kiểm thử tự động độc lập:
1. **Bộ Kiểm thử Hồi quy Backend (`test_refactored_system.py`):**
   - Số bài kiểm thử: **31 / 31 tests PASS** trong thời gian 9,59 giây.
   - Nội dung kiểm chứng: Kích hoạt sự cố, cập nhật trạng thái, an toàn luồng `DBWriteQueue`, chế độ SQLite WAL, quản lý tệp MP4, bảo toàn bất biến telemetry, cô lập phiên làm việc, ngăn chặn tấn công duyệt thư mục (`Path Traversal`) với các payload `..%2F`, `..\..\`.
2. **Bộ Kiểm thử Đánh giá Độc lập (`test_evaluation_harness.py`):**
   - Số bài kiểm thử: **22 / 22 tests PASS** trong thời gian 0,27 giây.
   - Nội dung kiểm chứng: Tính hợp lệ cấu hình YAML, kiểm tra rò rỉ dữ liệu, giải thuật tính Average Precision (AP), thuật toán bóc tách hợp khoảng sự kiện vi phạm (event interval union) và khớp sự kiện 1-1 theo thời gian.
3. **Bộ Kiểm thử Hợp đồng Telemetry Frontend (`test_telemetry_contract.ts`):**
   - Kết quả: **10 / 10 assertions PASS**, bảo đảm phân giải chính xác các trường telemetry từ backend.
4. **Kiểm tra Kiểu Tĩnh và Đóng gói Xuất xưởng:**
   - `npx tsc --noEmit`: 0 lỗi biên dịch kiểu tĩnh.
   - `npm run build`: Đóng gói ứng dụng thành công trong 1,97 giây, `dist/index.html` 0,88 kB, không có tài nguyên legacy.

### 9.3. Kết quả Mô hình Huấn luyện Lịch sử (`TRAINING_VALIDATION_ONLY`)
Trích xuất từ nhật ký huấn luyện 60 epoch của mô hình YOLO11s (`results.csv` tại `reports/evidence/training_lineage/`):
- Điểm mAP@0.5 cao nhất trên tập validation nội bộ lịch sử: **78,58%** (đạt được tại Epoch 55).
- Điểm mAP@0.5 tại Epoch 60: **76,92%**.
- Điểm mAP@0.5:0.95 tại Epoch 60: **47,16%**.
- Độ chính xác (Precision) tại Epoch 60: **76,22%**.
- Độ nhạy (Recall) tại Epoch 60: **68,37%**.
- Kích thước mô hình: **19,25 MB** (phù hợp triển khai nhẹ trên thiết bị biên).
- *Lưu ý khoa học:* Các chỉ số trên phản ánh kết quả trên tập validation nội bộ trong điều kiện huấn luyện; hiệu năng tổng quát ngoài đời thực đang chờ tập kiểm thử độc lập **`[CHỜ D-02]`**.

### 9.4. Đánh giá Mô hình trên Tập Kiểm thử Độc lập (Blocker D-02)
- **Trạng thái:** **`[CHỜ D-02]`** (Chưa thực hiện).
- Hệ thống chưa có tập kiểm thử độc lập ngoài quá trình huấn luyện để đo đạc mAP, Precision và Recall khách quan. Báo cáo không công bố các con số giả định.

### 9.5. Đánh giá Định lượng Phát hiện Quay đầu trên Video Thực tế (Blocker D-03)
- **Trạng thái:** **`[CHỜ D-03]`** (Chưa thực hiện).
- Giải thuật hình học điểm mốc và Temporal Continuity Guard $\ge 1.25$s đã được kiểm chứng bằng code inspection và bài test synthetic. Việc đo đạc các chỉ số định lượng sự kiện thời gian (tIoU, Event F1, Onset Error) trên video phòng thi thực tế gán nhãn ground-truth đang được mở để nghiên cứu tiếp theo.

---

## 10. HẠN CHẾ VÀ RỦI RO TỒN DƯ

Nghiên cứu ghi nhận một cách trung thực các hạn chế kỹ thuật sau:
1. **Khoảng trống Đánh giá Mô hình Độc lập (Khóa chặn D-02):** Chưa đánh giá mô hình phát hiện điện thoại trên tập dữ liệu holdout độc lập chưa từng qua huấn luyện.
2. **Khoảng trống Đánh giá Sự kiện Thực tế (Khóa chặn D-03):** Chưa benchmark định lượng thuật toán phát hiện quay đầu trên video phòng thi thực tế có gán nhãn mốc thời gian vi phạm chuẩn.
3. **Khả năng Rò rỉ Dữ liệu Cấp Phiên (Session-level Leakage):** Kiểm tra mã băm nội dung xác nhận 0 va chạm exact-hash, nhưng chưa loại trừ khả năng các frame liền kề cùng một clip nguồn nằm rải rác giữa tập train và valid của bộ dữ liệu mở.
4. **Không Thể Phục hồi Toàn bộ Lịch sử Huấn luyện Ban đầu:** Thiếu các file log của 5 epoch đầu tiên, trạng thái checkpoint khởi đầu mang nhãn `UNRESOLVED` và epoch sinh `best.pt` mang nhãn `UNRESOLVED`.
5. **Rủi ro Ngữ nghĩa Chuẩn hóa Confidence (`GAP-SEM-01`):** Nhánh tương thích ngược tự động chia 100 cho các giá trị $(1.0, 100.0]$ khiến cho một giá trị lỗi nhỏ như `2.0` sẽ bị hiểu thành `0.02` thay vì bị từ chối.
6. **Công cụ Linter Frontend Chưa Có AST Rule (`GAP-TOOL-01`):** Dự án hiện chỉ chạy kiểm tra kiểu dữ liệu tĩnh `tsc`, chưa cấu hình bộ quy chuẩn linter chuyên biệt như ESLint.
7. **Độ nhạy Môi trường:** Hiệu năng thị giác máy tính phụ thuộc vào điều kiện ánh sáng phòng thi (dễ nhầm lẫn khi ngược sáng mạnh), góc đặt camera (góc nghiêng quá lớn làm biến dạng tỷ lệ hình học), và hiện tượng che khuất bàn tay/tài liệu thi.
8. **Giới hạn Trợ lý Quyết định:** Hệ thống không thể và không được phép thay thế con người; mọi quyết định xử lý kỷ luật bắt buộc phải do giám thị và Hội đồng thi xác nhận.

---

## 11. ĐẠO ĐỨC VÀ BẢO VỆ QUYỀN RIÊNG TƯ

Incident schema không yêu cầu tên, SBD, CCCD hoặc email. Runtime không thực hiện nhận diện danh tính và không tạo face embedding. Tuy nhiên, frame và clip có thể chứa hình ảnh nhận dạng được của người dự thi nên vẫn phải được quản lý như dữ liệu cá nhân phù hợp với quy định áp dụng.

Trường `track_id` là định danh kỹ thuật trong luồng xử lý để liên kết các detection qua thời gian, không đại diện cho danh tính thực tế của thí sinh.

Vòng đời dữ liệu tuân thủ đúng hiện trạng triển khai kỹ thuật: trong phiên giám sát, khung hình được luân chuyển trong bộ đệm vòng (`RingBuffer`) và hàng đợi đơn slot (`SingleSlotInferenceBuffer`). Clip bằng chứng chỉ được trích xuất và ghi ra tệp MP4 khi phát sinh sự cố. Nếu giám thị chọn Bỏ qua (`Dismiss`), tệp clip bằng chứng tương ứng được xóa trong quy trình xử lý sự cố đã kiểm thử; nếu chọn Xác nhận (`Confirm`), tệp clip được lưu giữ tại `./data/evidence/` trên máy trạm cục bộ phục vụ công tác đối soát của Hội đồng thi.

Các giải pháp trên là những lựa chọn thiết kế kỹ thuật nhằm giảm thiểu dữ liệu thu thập và xử lý, không cấu thành một chứng nhận tuân thủ pháp lý chính thức (như GDPR hay chứng chỉ an toàn thông tin chuyên biệt) do chưa qua quy trình thẩm định của cơ quan quản lý độc lập.

---

## 12. KẾT LUẬN

*(Mức độ sẵn sàng văn bản: `DRAFTABLE_WITH_CAVEAT`)*

Đề tài đã nghiên cứu, thiết kế và tích hợp một hệ thống thị giác máy tính hỗ trợ giám thị phòng thi trực tiếp, được thiết kế để vận hành cục bộ trên máy trạm. Bằng việc đề xuất kiến trúc hai pipeline bất đồng bộ giữa `RingBuffer` (thu nhận liên tục 15 FPS) và `SingleSlotInferenceBuffer` (độ sâu hàng đợi $\le 1$), hệ thống đã giải quyết bài toán trễ tích lũy hàng đợi và mâu thuẫn tốc độ giữa thu nhận video và suy luận AI trên phần cứng máy trạm thông thường.

Hệ thống kết hợp mô hình YOLO11s phát hiện điện thoại với giải thuật điểm nghi vấn tư thế đầu từ hình học keypoint COCO và Temporal Continuity Guard ($\ge 1.25$s) để nhận diện các hành vi vi phạm chớp nhoáng, tự động cắt clip bằng chứng 15 giây hỗ trợ người giám sát xem xét và thẩm định. Toàn bộ 31 bài kiểm thử hồi quy backend, 22 bài kiểm thử harness và thực nghiệm E2E 125,1s qua WebSocket nhị phân đều đạt kết quả tốt trong các trường hợp đã kiểm thử (counter `client_backpressure_drops` bằng 0 trong phiên kiểm thử, các bất biến kỹ thuật được bảo toàn).

Tuy nhiên, nghiên cứu khẳng định rõ ràng rằng hệ thống đóng vai trò công cụ trợ lý hỗ trợ giám sát, không thay thế giám thị con người. Để đưa hệ thống vào áp dụng thực tế trên quy mô rộng, cần tiếp tục thực hiện các bài đánh giá độc lập trên tập holdout (D-02) và bộ video phòng thi thực tế gán nhãn mốc thời gian (D-03).

---

## 13. HƯỚNG PHÁT TRIỂN

1. **Đóng Khóa chặn D-02:** Thu thập, dán nhãn và khóa mã băm một tập dữ liệu kiểm thử độc lập (D-02: tập đánh giá độc lập, chưa từng tham gia train, validation, điều chỉnh threshold hoặc kiểm thử thủ công trước đó, đồng thời đại diện hợp lý cho bối cảnh sử dụng dự kiến) với nhiều bối cảnh bàn thi, ánh sáng và loại thiết bị di động khác nhau để công bố mAP khách quan. OOD evaluation là một đánh giá bổ sung, tách biệt với D-02.
2. **Đóng Khóa chặn D-03:** Ghi hình và dán nhãn mốc thời gian (onset/offset intervals) cho các video mô phỏng phòng thi thực tế nhằm đo đạc Event F1-score, tIoU và sai số phát hiện thời gian đầu.
3. **Tăng tốc Phần cứng Biên (Edge AI Acceleration):** Tối ưu hóa mô hình với TensorRT hoặc ONNX Runtime trên các thiết bị tính toán biên nhỏ gọn (như NVIDIA Jetson Orin Nano) để nâng tốc độ suy luận AI lên 15–30 FPS.
4. **Nâng cấp CSDL Chuẩn hóa:** Di chuyển toàn bộ dữ liệu cũ để khóa cứng hợp đồng `confidence` chỉ nhận $[0.0, 1.0]$, loại bỏ nhánh tương thích phần trăm trong logic xử lý chính để đóng khiếm khuyết `GAP-SEM-01`.

---

## 14. TÀI LIỆU THAM KHẢO

### 14.1. Thành phần Công nghệ và Giao thức Đã Xác minh Thực tế Mã nguồn (`IMPLEMENTATION_VERIFIED`)
1. **SQLite Write-Ahead Logging (WAL):** `[IMPLEMENTATION_VERIFIED: SQLite 3 Consortium. Write-Ahead Logging. Triển khai trong backend/database.py với PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;]`
2. **FastAPI Framework:** `[IMPLEMENTATION_VERIFIED: Tiangolo, S. (2018). FastAPI framework. Triển khai trong backend/main.py và routers]`
3. **React 19 & TypeScript Frontend:** `[IMPLEMENTATION_VERIFIED: React 19.0.1, TypeScript 5.x. Triển khai trong frontend/src/]`
4. **OpenCV Video Processing:** `[IMPLEMENTATION_VERIFIED: Bradski, G. (2000). The OpenCV Library. Triển khai ghi clip MP4 trong backend/services/video_ring_buffer.py]`
5. **Ultralytics YOLO Engine:** `[IMPLEMENTATION_VERIFIED: Jocher, G., et al. (2024). Ultralytics YOLO. Triển khai nạp mô hình yolo11s / yolo11m-pose trong backend/services/ai_model_service.py và model/exam_analyzer.py]`

### 14.2. Danh mục Tài liệu Học thuật Cơ sở Chờ Chuẩn hóa Trích dẫn (`BIBLIOGRAPHY_PENDING_VERIFICATION`)
*(Tác giả sẽ chuẩn hóa trích dẫn theo định dạng IEEE/APA khi nộp báo cáo chính thức)*:
1. **Nguồn Lịch sử Phát triển YOLO:**  
   `[BIBLIOGRAPHY_PENDING_VERIFICATION: Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). You only look once: Unified, real-time object detection. In Proceedings of the IEEE conference on computer vision and pattern recognition (CVPR), pp. 779-788.]`
2. **Nguồn Điểm Mốc Cơ thể COCO:**  
   `[BIBLIOGRAPHY_PENDING_VERIFICATION: Lin, T. Y., et al. (2014). Microsoft COCO: Common objects in context. In European conference on computer vision (ECCV), pp. 740-755.]`
3. **Nguồn Thuật toán Ước lượng Điểm Mốc Tư thế:**  
   `[BIBLIOGRAPHY_PENDING_VERIFICATION: Cao, Z., Simon, T., Wei, S. E., & Sheikh, Y. (2017). Realtime multi-person 2d pose estimation using part affinity fields. In CVPR, pp. 7291-7299.]`
4. **Nguồn Thuật toán Bám vết ByteTrack:**  
   `[BIBLIOGRAPHY_PENDING_VERIFICATION: Zhang, Y., et al. (2022). ByteTrack: Multi-object tracking by associating every detection box. In European Conference on Computer Vision (ECCV), pp. 1-21.]`
5. **Nguồn Nghiên cứu Suy giảm Tập trung Thị giác (Vigilance Decrement):**  
   - `[BIBLIOGRAPHY_PENDING_VERIFICATION: Mackworth, N. H. (1948). The breakdown of vigilance during prolonged visual search. Quarterly Journal of Experimental Psychology, 1(1), 6-21.]`
   - `[BIBLIOGRAPHY_PENDING_VERIFICATION: Warm, J. S., Parasuraman, R., & Matthews, G. (2008). Vigilance requires hard mental work and is stressful. Human factors, 50(3), 433-441.]`
6. **Nguồn Chuyên khảo Cơ sở Dữ liệu SQLite:**  
   `[BIBLIOGRAPHY_PENDING_VERIFICATION: Owens, M. (2006). The Definitive Guide to SQLite. Apress.]`

---

## 15. PHỤ LỤC

### Phụ lục A: Bảng Đối Soát Mã Băm Gói Bằng Chứng Huấn Luyện Lịch Sử (Pass 1.3)
| Tên Tệp Bằng Chứng | Kích thước | Mã băm SHA-256 |
|---|---|---|
| `README_mobilephone_v3.txt` | 1.040 B | `bb5e34c4a52b49f13c3e153a857f9c2947566b459ef044d5d0876906216d102e` |
| `README_mobilephone2_v1.txt` | 1.041 B | `84a26eb48b0dd3647af1abdc46be319d0bb051f876ef95f7fb726f21e01f38d3` |
| `README_mobilephone3_v1.txt` | 1.033 B | `24859b68bce0dd403ee4edd3a3765ebc6ecd4117eeb97f51db8edd8798866053` |
| `results.csv` | 7.179 B | `107d3c7ba661d679274e5f01c51e6c1373afac53fb36a85815c61e9bc4cb857c` |
| `SPRINT_2_2A_CORRECTED_REPORT.md` | 22.003 B | `a12bcbb9d2aa4d3147b9791e671b0fbe24b69ad187a42e6f0f40505ad003a763` |
| `training_data_phone.redacted.yaml` | 460 B | `23c9b7d1918ffcefb12b95e646d6c571507c2f7495b5094f0b95711d6de14ed0` |
| `args.yaml` | 1.801 B | `1c5e63a7c2af544ddc3dadefb9aede99fedbe03c6421a3f001f2630f2d8a4fa5` |
| `HANDOFF_README.md` | 4.117 B | `7addcde2aa0d43335f383303b6d436e784b61c1c0fa4b9fa22fef98647373045` |
| `lineage_manifest.json` | 5.812 B | `deceb7ae00ff0e0405b4cc666e059868dc86d176291ac23eed5e75adbda5cbb3` |
| `artifact_hashes.csv` | 875 B | `61c78a5340955c41357146361684da698610270ff3cafaa36db8cf93e08243e1` |

### Phụ lục B: Định Nghĩa 4 Bất Biến Telemetry Toán Học
- **Bất biến 4 (Inv 4):** $\text{server\_frames\_decoded} \le \text{server\_packets\_received}$.
- **Bất biến 5 (Inv 5):** $\text{inference\_submitted} \le \text{server\_frames\_decoded}$.
- **Bất biến 6 (Inv 6):** $\text{inference\_processed} + \text{inference\_superseded} + \text{inference\_pending} = \text{inference\_submitted}$.
- **Bất biến 7 (Inv 7):** $\text{result\_messages\_sent} \le \text{inference\_processed}$.

---
**HẾT BẢN THẢO BÁO CÁO KHKT V0.1**
