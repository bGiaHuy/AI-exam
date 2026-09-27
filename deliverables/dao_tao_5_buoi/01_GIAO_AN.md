# Giáo án 5 buổi: học AI/CV qua AI Exam Control

## Cách dạy

Mỗi buổi đi theo vòng lặp: **vật thật hoặc dữ liệu thật → khái niệm → bài tập → đối chiếu project → tự giải thích**. Không mở đầu bằng định nghĩa dài. Người dạy chỉ đưa thuật ngữ sau khi học viên đã mô tả được hiện tượng bằng lời thường.

Mỗi buổi 90 phút: 10 phút truy hồi kiến thức; 25 phút xây khái niệm; 25 phút thực hành trên artifact của project; 20 phút học viên làm độc lập; 10 phút kiểm tra. Tỉ lệ luyện câu hỏi thi chỉ khoảng 10% toàn khóa.

Chuẩn hoàn thành: học viên đạt ít nhất 70% bài kiểm tra kiến thức, nộp đủ năm sản phẩm học tập và giải thích miệng được một chuỗi kỹ thuật không nhìn đáp án. Các bài tập dùng bản sao dữ liệu đào tạo, không sửa model, trọng số, DB vận hành hoặc bằng chứng gốc.

## Buổi 1 · Dữ liệu, nhãn và cách máy học từ ví dụ

**Câu hỏi dẫn đường:** Nếu máy chưa biết “điện thoại” là gì, ta phải đưa cho máy những ví dụ nào và mô tả đáp án ra sao?

**Khái niệm:** AI, ML, DL; sample; input; label/ground truth; supervised learning; positive/negative; hard negative; metadata; train/validation/test; data leakage; domain shift.

**Chuẩn bị:** 12–20 ảnh tự chụp không có dữ liệu nhạy cảm, gồm điện thoại rõ, điện thoại bị che, máy tính bỏ túi, ví, hộp bút và ảnh không có điện thoại; mẫu metadata từ `datasets/README.md`.

| Phút | Hoạt động dạy và học | Kiểm chứng hiểu |
|---|---|---|
| 00–10 | Đưa 6 ảnh, yêu cầu học viên tự đặt quy tắc nhận điện thoại. Thử quy tắc với ảnh khó. | Học viên nhận ra luật thủ công dễ vỡ khi góc nhìn thay đổi. |
| 10–20 | Phân biệt AI là phạm vi rộng, ML học quy luật từ dữ liệu, DL là một nhánh ML dùng mạng nhiều tầng. | Mỗi người đặt ba thuật ngữ vào quan hệ bao-hàm. |
| 20–35 | Tách một bài toán thành input, label và output. So sánh classification “ảnh có điện thoại?” với detection “điện thoại ở đâu?”. | Học viên viết ba trường cho bài toán project. |
| 35–45 | Xem schema metadata và quy tắc negative/hard negative của project. Giải thích vì sao máy tính bỏ túi là ví dụ khó hữu ích. | Chọn được positive, negative và hard negative. |
| 45–55 | Thực hành tạo data card cho bộ ảnh: nguồn, quyền dùng, ánh sáng, che khuất, khoảng cách, loại vật gây nhầm. | Data card không thiếu nguồn và quyền sử dụng. |
| 55–60 | Minh họa chia ngẫu nhiên các frame gần nhau từ cùng video có thể làm test quá dễ. | Nêu được “rò rỉ theo phiên/video”. |
| 60–75 | Nhóm lập cách chia train/val/test theo session/camera, không chia từng ảnh một cách mù quáng. | Giải thích được vì sao test phải đại diện nhưng độc lập. |
| 75–80 | Đối chiếu project: lịch sử có 2.961 ảnh/3.706 boxes, nhưng untouched holdout vẫn mở. | Phân biệt “có test nội bộ” với “holdout độc lập”. |
| 80–90 | Kiểm tra: định nghĩa label, hard negative, leakage; sửa một cách chia sai. | Nộp data card và split plan. |

**Bài về nhà:** thu 10 ảnh hợp lệ từ ít nhất hai điều kiện, kèm metadata; không đưa mặt hoặc thông tin nhận dạng khi chưa có đồng ý.

**Lỗi cần sửa ngay:** “dữ liệu càng nhiều tự động càng tốt”; “test là dữ liệu dùng thử trong khi huấn luyện”; “ảnh không có điện thoại thì bỏ đi”.

## Buổi 2 · Computer Vision và object detection

**Câu hỏi dẫn đường:** Một ảnh biến thành con số thế nào, và model biết một bounding box là đúng bằng cách nào?

**Khái niệm:** pixel, channel, resolution, frame, FPS; classification/detection; bounding box; tọa độ chuẩn hóa; confidence; threshold; IoU; TP/FP/FN; NMS ở mức trực giác; YOLO là một họ detector.

**Chuẩn bị:** ảnh buổi 1; giấy lưới hoặc công cụ gán nhãn; mẫu định dạng YOLO `class xc yc w h`; hai box chồng nhau để tính IoU.

| Phút | Hoạt động dạy và học | Kiểm chứng hiểu |
|---|---|---|
| 00–10 | Ôn input/label/split bằng ba ảnh mới. | Phân loại đúng positive, negative, hard negative. |
| 10–20 | Phóng to ảnh để thấy pixel; giải thích resize làm vật nhỏ mất chi tiết. Video là chuỗi frame, FPS camera khác FPS inference. | Dự đoán đúng ảnh nào khó hơn và nêu lý do. |
| 20–30 | So sánh classification với detection. Vẽ box chặt quanh điện thoại; giải thích box quá rộng đưa thêm nhiễu vào nhãn. | Học viên sửa ba box lỗi. |
| 30–35 | Chuyển box sang tọa độ chuẩn hóa YOLO. Không yêu cầu thuộc công thức nếu chưa hiểu tâm/rộng/cao. | Đọc được một dòng nhãn 5 số. |
| 35–47 | Gán nhãn 5 ảnh có điện thoại và tạo file rỗng cho 3 ảnh negative. | Đúng class 0, box trong biên, negative rỗng. |
| 47–55 | Review chéo: hai học viên so box và thống nhất guideline. | Phân biệt lỗi label với lỗi model. |
| 55–60 | Tính IoU bằng vùng giao/vùng hợp trên hình chữ nhật đơn giản. | Nói được IoU đo độ chồng khớp, không đo “gian lận”. |
| 60–72 | Cho 8 prediction giả định. Áp confidence threshold rồi ghép với ground truth bằng IoU. | Đếm TP, FP, FN đúng theo quy tắc đã cho. |
| 72–80 | Giải thích NMS loại box trùng và vì sao threshold thay đổi số cảnh báo. | Dự đoán tác động khi hạ confidence threshold. |
| 80–90 | Kiểm tra và nộp 10 nhãn mẫu + checklist chất lượng. | Không nhầm confidence với accuracy. |

**Bài về nhà:** tìm ba nguồn báo nhầm có thể xảy ra và đề xuất negative/hard negative để bổ sung.

## Buổi 3 · Pose estimation, tracking và hành vi theo thời gian

**Câu hỏi dẫn đường:** Một tư thế trong một frame có đủ để gọi là hành vi quay đầu không?

**Khái niệm:** keypoint; pose estimation; heuristic; learned component; track ID; association; occlusion; frame-level vs event-level label; onset/offset; gap; temporal smoothing; state machine.

**Chuẩn bị:** sơ đồ cơ thể đơn giản; ba chuỗi timeline; mẫu schema `events.csv`; code `temporal_tracker.py` chỉ để đối chiếu sau khi hiểu quy tắc.

| Phút | Hoạt động dạy và học | Kiểm chứng hiểu |
|---|---|---|
| 00–10 | Ôn detection, confidence và IoU. | Giải thích một FP mà không đổ cho “AI ngu”. |
| 10–22 | Đặt chấm tại mũi, mắt, tai, vai trên hình. Giải thích pose model dự đoán keypoint chứ chưa kết luận hành vi. | Tách output model khỏi luật nghiệp vụ. |
| 22–32 | Dùng hình học 2D để suy ra dấu hiệu quay đầu. So sánh với head pose 3D và nêu hạn chế góc camera. | Không gọi `turn_deg` là góc Euler đã hiệu chuẩn. |
| 32–40 | Theo dõi cùng người qua frame bằng track ID. Minh họa mất dấu, đổi ID và hai người cắt nhau. | Khẳng định track ID không phải nhận diện danh tính. |
| 40–50 | Gán nhãn một video giả định bằng interval: start, end, direction, target. | Tạo được event label thay vì chỉ label từng ảnh. |
| 50–60 | Mô phỏng chuỗi S-S-gap-S. Áp mặc định: đủ 1,25 s, ít nhất 3 mẫu, gap không quá 0,75 s. | Giải thích vì sao hai frame cách xa không thành sự kiện liên tục. |
| 60–70 | Học viên đóng vai “frame”; một người làm state machine quyết định green/yellow/red. | Đi đúng các trạng thái và reset. |
| 70–80 | Vẽ hai pipeline: điện thoại và quay đầu. Đánh dấu phần learned, heuristic và human review. | Sơ đồ không gộp model với toàn hệ thống. |
| 80–90 | Kiểm tra và nộp interval labels + sơ đồ. | Phân biệt detection, tracking, event và decision. |

**Bài về nhà:** viết một tình huống false positive và một false negative cho quay đầu; nêu dữ liệu cần thu để kiểm tra.

## Buổi 4 · Deep Learning, transfer learning và fine-tune

**Câu hỏi dẫn đường:** Fine-tune đã làm gì với một model có sẵn, và nhìn log nào để biết việc học đang diễn ra?

**Khái niệm:** neural network ở mức input–weights–prediction; forward pass; loss; gradient/backpropagation ở mức ý tưởng; optimizer; learning rate; batch; epoch; augmentation; pretrained model; transfer learning; fine-tune; checkpoint; resume; train/validation loss; overfitting; reproducibility.

**Chuẩn bị:** bản sao `reports/evidence/training_lineage/args.yaml`, 10 dòng đầu và 10 dòng cuối của `results.csv`, `lineage_manifest.json`. Không mở hoặc sửa `model/`.

| Phút | Hoạt động dạy và học | Kiểm chứng hiểu |
|---|---|---|
| 00–10 | Ôn learned component và heuristic component. | Xếp đúng YOLO, temporal rule, RingBuffer. |
| 10–22 | Mô hình hóa một lần học: dự đoán, so với nhãn, tính loss, điều chỉnh weights. | Kể lại vòng lặp mà không dùng câu “AI tự hiểu”. |
| 22–32 | Giải thích pretrained model và fine-tune: kế thừa biểu diễn rồi điều chỉnh bằng dữ liệu nhiệm vụ. So sánh training from scratch. | Nêu lợi ích và rủi ro domain mismatch. |
| 32–42 | Giải thích epoch, batch, image size, learning rate, optimizer; augmentation tạo biến thể nhưng không tạo bằng chứng thực địa mới. | Mỗi người giải thích hai hyperparameter bằng ví dụ. |
| 42–52 | Đọc cấu hình project: 60 epoch, batch 6, imgsz 960, optimizer auto, resume từ `last.pt`, close mosaic 10. | Tách fact trong artifact khỏi suy đoán. |
| 52–60 | Đọc các cột box/cls/DFL loss và precision/recall/mAP. Giải thích loss khác metric. | Chỉ đúng cột phục vụ học và cột phục vụ đánh giá. |
| 60–70 | Nhận ra time reset trước epoch 6 là bằng chứng resume. Trạng thái model pretrained ban đầu và epoch tạo best checkpoint vẫn unresolved. | Không suy diễn “epoch 55 sinh best.pt”. |
| 70–80 | Bài tập chẩn đoán ba đường cong giả định: underfit, overfit, ổn định. | Đề xuất thêm dữ liệu/regularization/early stopping phù hợp, không máy móc. |
| 80–90 | Kiểm tra và nộp phiếu đọc run lịch sử. | Trả lời được fine-tune khác inference. |

**Không làm trong khóa chính:** chạy lại training chỉ để “cho xem”. Fine-tune cần GPU/thời gian và một thí nghiệm được thiết kế; chạy lệnh mà không kiểm soát dữ liệu không tạo hiểu biết đáng tin.

## Buổi 5 · Đánh giá, inference và ghép thành sản phẩm

**Câu hỏi dẫn đường:** Từ model có metric đến hệ thống dùng được còn những lớp nào, và ta được phép kết luận gì?

**Khái niệm:** inference; operating threshold; confusion matrix; precision/recall/F1; AP/mAP ở mức đọc đúng; ranking metric vs operational metric; subgroup analysis; latency/throughput; queue; RingBuffer; persistence; API/UI; human in the loop; experiment design.

**Chuẩn bị:** worksheet 20 prediction giả định; báo cáo lineage; benchmark lịch sử; sơ đồ kiến trúc; ứng dụng hoặc ảnh chụp.

| Phút | Hoạt động dạy và học | Kiểm chứng hiểu |
|---|---|---|
| 00–10 | Ôn fine-tune, checkpoint và inference. | Sắp xếp đúng train → checkpoint → inference. |
| 10–22 | Lập confusion matrix từ bài tập và tính precision, recall, F1. | Nói được khi nào ưu tiên giảm FP hoặc FN. |
| 22–30 | Giải thích PR curve/AP/mAP bằng nhiều threshold và nhiều IoU; không biến mAP thành xác suất một cảnh báo đúng. | Đọc đúng nhãn `TRAINING_VALIDATION_ONLY`. |
| 30–35 | Tách ranking metric khỏi operating point đang triển khai. | Biết threshold 0,35/0,50 phải gắn với phiên bản cấu hình. |
| 35–48 | Đi qua inference pipeline: nguồn → frame → model → tracking/time rule → event → RingBuffer → DB → UI → human review. | Mỗi người giải thích một lớp và lỗi có thể xảy ra. |
| 48–58 | Đọc benchmark: camera nhận khoảng 15,58 FPS nhưng kết quả khoảng 2,83/s; frame cũ được thay để giảm backlog. | Không nói hệ thống suy luận 15 FPS. |
| 58–65 | Thảo luận model metric tốt nhưng deployment có thể lỗi do camera, codec, queue, disk, UI. | Phân loại lỗi model, data và system. |
| 65–75 | Nhóm viết báo cáo mini: điều đã đo, điều chưa đo, hai subgroup cần kiểm tra, một thí nghiệm tiếp theo. | Có điều kiện đo và không dùng từ “chính xác” mơ hồ. |
| 75–82 | Mỗi học viên trình bày pipeline 2 phút không nhìn đáp án. | Người dạy hỏi “bằng chứng ở đâu?” một lần. |
| 82–90 | Kiểm tra tổng hợp; dành 3 phút cuối liên hệ cách trả lời giám khảo. | Nộp báo cáo mini và tự đánh giá lỗ hổng. |

## Cách chấm năm sản phẩm

| Tiêu chí | Điểm |
|---|---:|
| Khái niệm đúng và phân biệt được các cặp dễ nhầm | 30 |
| Dùng artifact hoặc phép tính làm bằng chứng | 25 |
| Liên hệ đúng với project | 20 |
| Nêu giới hạn và nguồn sai số | 15 |
| Trình bày rõ bằng lời của mình | 10 |

Không cho điểm phần học thuộc nếu học viên không giải thích được một ví dụ mới. Một câu trả lời “chưa đủ dữ liệu để kết luận” có thể đạt điểm tối đa khi học viên nói rõ thiếu dữ liệu gì và thiết kế cách đo hợp lý.
