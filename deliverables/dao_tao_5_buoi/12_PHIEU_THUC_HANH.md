# Phiếu thực hành học viên

In mỗi mẫu theo số học viên. Không điền bằng dữ liệu thật có thông tin nhận dạng.

## Phiếu 1 · Data card nhỏ

- Tên bộ dữ liệu: __________
- Bài toán: __________
- Input: __________; label: __________; output mong muốn: __________
- Nguồn và quyền sử dụng: __________
- Số positive: ___; negative: ___; hard negative: ___
- Điều kiện có trong dữ liệu: ánh sáng ___; che khuất ___; khoảng cách ___; camera ___
- Điều kiện còn thiếu: __________
- Đơn vị chia tập: ảnh / video / session / camera / subject: __________
- Train: ___; validation: ___; test: ___
- Cách phòng leakage: __________

## Phiếu 2 · Review nhãn detection

| Sample | Có phone? | Box sát vật? | Trong biên? | Class đúng? | Negative rỗng? | Người review | Sửa gì? |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |

Guideline do nhóm thống nhất: khi điện thoại bị che __________; khi chạm mép ảnh __________; vật phản chiếu/hình điện thoại __________.

## Phiếu 3 · Nhãn sự kiện thời gian

| video_id | target_id_anonymous | behavior | start_s | end_s | direction | annotator | review_status |
|---|---|---|---:|---:|---|---|---|
| | | | | | | | |
| | | | | | | | |

Tình huống gây bất đồng giữa hai người gán nhãn: __________. Quy tắc thống nhất: __________.

## Phiếu 4 · Đọc fine-tune run

- Task/mode: __________
- Model/checkpoint đầu vào được artifact ghi: __________
- Có resume không? Bằng chứng: __________
- Epoch: ___; batch: ___; imgsz: ___; optimizer: __________
- Ba loss được log: __________
- Bốn metric được log: __________
- Epoch có mAP50 cao nhất trong bảng: ___; giá trị: ___
- Điều trên có chứng minh checkpoint triển khai sinh từ epoch đó không? Vì sao? __________
- Dấu hiệu cần xem để phát hiện overfit: __________
- Thông tin lineage còn unresolved: __________

## Phiếu 5 · Báo cáo đánh giá mini

- Model/checkpoint/hash: __________
- Dataset version/split: __________
- Confidence threshold: ___; IoU threshold: ___
- TP: ___; FP: ___; FN: ___
- Precision: ___; Recall: ___; F1: ___
- Subgroup 1: __________; kết quả: __________
- Subgroup 2: __________; kết quả: __________
- Ba lỗi cần review thủ công: __________
- Kết luận được phép nói: __________
- Kết luận chưa được phép nói: __________
- Thí nghiệm tiếp theo: __________

## Phiếu giải thích 2 phút

Chủ đề bốc thăm: data split / bounding box / fine-tune / pose / metric / RingBuffer.

- Định nghĩa bằng lời của em: __________
- Ví dụ trong project: __________
- Artifact/code chứng minh: __________
- Giới hạn hoặc câu hỏi mở: __________
