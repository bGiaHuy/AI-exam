# Nguồn nội bộ và giới hạn sử dụng

Tài liệu khóa học dựa trên source/artifact hiện có ngày 26/09/2026. Đây là chỉ mục để người dạy kiểm tra lại khi project thay đổi. Không dùng đường dẫn dòng cố định làm bằng chứng vĩnh viễn; kiểm tra nội dung và Git diff trước khóa mới.

| Mã | Nguồn | Dùng để dạy | Giới hạn |
|---|---|---|---|
| S01 | `reports/SYSTEM_SCOPE_FREEZE.md` | Phạm vi, non-goal, human review | Có thể chậm hơn code đang sửa |
| S02 | `src/App.tsx`, `StreamlinedProctorDashboard.tsx` | Màn hình, nguồn, demo mode, duyệt | Worktree đang có thay đổi chưa commit |
| S03 | `backend/services/fair_scheduler.py` | Detection, scheduler, confidence | Nhánh confidence khởi tạo 90 cần rà soát ngữ nghĩa |
| S04 | `backend/services/ring_buffer.py` | Pre/post roll và evidence | Clip thực tế phụ thuộc dữ liệu/codec |
| S05 | `backend/services/db_queue.py`, `database.py` | Queue, SQLite WAL | Không chứng minh chống mất dữ liệu tuyệt đối |
| S06 | `backend/routers/incidents.py`, `models.py` | Incident và trạng thái duyệt | Không phải quy trình kỷ luật pháp lý |
| S07 | `backend/main.py`, `src/services/api.ts` | API local, static evidence | Launcher bind `0.0.0.0`; cần kiểm tra cấu hình mạng thực |
| S08 | `camera_manager.py`, `acceptance_summary.json` | Nhiều nguồn camera | Hồ sơ đã đọc còn ghi hardware acceptance pending |
| S09 | `demoConfig.ts`, `mockDemoData.ts` | Phân biệt dữ liệu giả lập | Không dùng để chứng minh AI |
| S10 | `reports/evidence/training_lineage/*` | Dataset, fine-tune, metric lịch sử | Initial checkpoint và source epoch của best unresolved; metric validation only |
| S11 | `temporal_tracker.py`, `datasets/README.md` | Gap/min samples/event labels | Heuristic và threshold có thể đổi theo version |
| S12 | `backend/confidence.py`, schemas | Chuẩn hóa confidence | Tương thích legacy có ngữ nghĩa mơ hồ với giá trị >1 |
| S13 | `REPORT_GAP_REGISTER.md` | Holdout, posture ground truth, gaps | Trạng thái gap cần cập nhật khi có bằng chứng mới |
| S14 | `e2e_benchmark_result.json` | Latency, acquisition, result rate | Một benchmark lịch sử trên cấu hình cụ thể |
| S15 | `deliverables/ha_noi/EVIDENCE_MAP.md` | Kiểm toán DB/clip lịch sử | Vòng soạn khóa học không mở DB/clip để xác minh lại |
| S16 | `git status`, `git diff --stat` ngày kiểm toán | Cảnh báo version hiện tại khác log cũ | Không phải kết luận code sai; chỉ là trạng thái chưa tái nghiệm thu |

## Những câu không được dạy như sự thật đã chứng minh

- “Mô hình đạt 99% trong phòng thi thật.”
- “mAP50 0,78578 nghĩa là phát hiện đúng 78,578% mọi trường hợp.”
- “Checkpoint triển khai chắc chắn sinh ở epoch 55.”
- “Model chắc chắn bắt đầu từ checkpoint pretrained cụ thể.”
- “Không có bất kỳ leakage nào.”
- “Ba camera vật lý đã được nghiệm thu đồng thời.”
- “Track ID xác định một thí sinh.”
- “Cờ đỏ chứng minh gian lận.”

## Khi cập nhật khóa học

1. Khóa version code, model hash, dataset version và cấu hình.
2. Kiểm tra artifact mới có thay đổi dataset split, metric hoặc gap không.
3. Chạy nghiệm thu phù hợp trên bản đó; không tái dùng log cũ cho code mới nếu phạm vi đã đổi.
4. Cập nhật sổ tay, slide, đề kiểm tra và đáp án cùng lúc.
5. Ghi ngày và người duyệt thay đổi.
