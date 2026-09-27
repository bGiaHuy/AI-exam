# Đáp án mẫu cho 30 câu hỏi

Các câu trả lời dùng bằng chứng nội bộ trong tài liệu 11. Đây là mẫu diễn đạt để luyện, không phải kết quả đánh giá mới. Nếu bản chạy đã thay đổi, cập nhật bằng chứng trước khi đổi câu trả lời.

## Cơ bản

**1. Bài toán và người dùng.** Dự án hỗ trợ giám thị thi giấy chú ý tới tình huống nghi vấn và tìm lại đoạn video liên quan. Người vận hành xem cảnh báo, xem clip rồi duyệt sự cố. Chưa có số liệu để khẳng định giảm bao nhiêu nhân lực. [S01, S02]

**2. Phạm vi.** Hai nhóm chính là điện thoại và quay đầu nghi vấn. Nhận diện danh tính, điểm danh, phao giấy, rời ghế và lập biên bản không thuộc phạm vi hiện tại. Một nhãn từng có trong quy định hoặc tài liệu cũ chưa chứng minh đã có chức năng chạy. [S01]

**3. Cờ đỏ.** Cờ đỏ là kết quả quy tắc cảnh báo và kích hoạt ghi bằng chứng. Trạng thái xác nhận do giám thị cập nhật sau khi xem. Không dùng màu cờ làm kết luận tự động. [S03, S06]

**4. Danh tính.** Không. Track ID là mã bám vết tạm thời, không phải tên hoặc số báo danh. Hình ảnh vẫn có thể cho thấy người thật, vì vậy không gọi dữ liệu video là hoàn toàn vô danh. [S01, S06]

**5. Clip.** Clip cho thấy diễn biến trước và sau cảnh báo, giúp người duyệt có thêm bối cảnh so với một ảnh. Clip vẫn chỉ thể hiện những gì camera nhìn thấy, có thể thiếu hoặc bị che khuất. [S04]

**6. Duyệt.** Mở clip từ danh sách, xem bối cảnh, đóng cửa sổ clip rồi chọn xác nhận hoặc bỏ qua. API lưu trạng thái trong DB, giao diện cập nhật; cần kiểm tra trạng thái thực tế sau thao tác. [S02, S06]

**7. Mạng.** Với webcam/video cục bộ và môi trường đã cài đủ, kiến trúc cho phép xử lý trên máy, không cần dịch vụ AI đám mây trong luồng cốt lõi. Camera RTSP vẫn cần đường mạng tới camera. Chưa có phép thử ngắt mạng trong vòng kiểm toán này để bảo đảm mọi cấu hình đều hoạt động. [S07, S08]

**8. Ba kiểu demo.** Webcam là hình đang thu; video đầu vào là hình ghi trước được AI xử lý; dữ liệu giả lập là danh sách mẫu để minh họa giao diện. Chỉ hai kiểu đầu có thể dùng để quan sát suy luận thật khi backend AI đang chạy. [S02, S09]

**9. Luồng.** Nhận hình, phân tích và giữ bộ đệm, tạo cảnh báo, ghi clip, lưu thông tin sự cố, giám thị xem và duyệt. Bộ đệm chạy trước khi có cảnh báo để giữ được phần trước sự kiện. [S03–S06]

**10. Đóng góp.** Nhóm tích hợp nhận video, hai nhóm phân tích thị giác, kiểm tra thời gian, bộ đệm clip và quy trình người duyệt thành một ứng dụng. Cần phân biệt phần tích hợp của nhóm với mô hình/thuật toán nền kế thừa. Không tuyên bố phát minh YOLO hoặc ByteTrack. [S01, S03–S05]

## Kỹ thuật

**11. Điện thoại.** Theo hồ sơ dự án, mô hình phát hiện vật thể học dấu hiệu hình ảnh của điện thoại và trả kết quả phát hiện. Phần tích hợp dùng kết quả đó để cảnh báo và lưu clip. Vòng này không mở model nên không khẳng định thêm chi tiết nội bộ ngoài hồ sơ. [S03, S10]

**12. Thời gian.** Tầng kiểm tra liên tục mặc định dùng 1,25 giây, ít nhất 3 quan sát nghi vấn và đặt lại chuỗi nếu khoảng cách quan sát vượt 0,75 giây. Phải đọc cấu hình thực dùng; không nói cứ quay đầu đúng 1,25 giây là chắc chắn bị phát hiện. [S11]

**13. Confidence.** Đó là điểm dùng trong xử lý/hiển thị, không phải xác suất gian lận. Nhánh scheduler hiện có bước tổng hợp điểm nên điểm lưu sự cố có thể khác điểm gốc. Muốn nói tỷ lệ đúng cần đánh giá trên dữ liệu có nhãn. [S03, S12]

**14. Ngưỡng.** Hạ ngưỡng có thể bắt thêm tín hiệu yếu nhưng tăng báo nhầm. Chọn ngưỡng cần đo trên dữ liệu phù hợp và giữ tập kiểm thử độc lập để tránh chọn theo những ví dụ đã biết. [S10, S13]

**15. Bộ đệm.** RingBuffer liên tục giữ hình gần nhất trong RAM. Khi có sự kiện, hệ thống lấy phần trước và tiếp tục ghi phần sau. Mặc định 5/10 giây là cửa sổ mong muốn, không bảo đảm luôn đủ nếu vừa khởi động hoặc mất nguồn. [S04]

**16. Tốc độ.** Thu hình và chạy AI là hai công việc có tốc độ khác nhau. Khi máy bận, hệ thống có thể thay khung hình chờ bằng khung mới để giảm trễ. Benchmark lịch sử có 354 kết quả trong 125,1 giây, khoảng 2,83 kết quả/giây, không phải 15 lần suy luận/giây. [S03, S14]

**17. SQLite.** DB lưu thông tin sự cố; WAL hỗ trợ cách đọc/ghi của SQLite, hàng đợi ghi tuần tự hạn chế ghi đồng thời. Những cơ chế này không tự bảo đảm không mất dữ liệu khi ổ đĩa lỗi hoặc mất điện. [S05, S07]

**18. Track.** Không được coi Track ID là danh tính ổn định xuyên camera hoặc phiên. Giáo án chỉ dùng mã này để chỉ đối tượng trong ngữ cảnh nguồn/phiên đang quan sát. [S01, S11]

**19. Clip lỗi.** Có thể file chưa ghi xong, thiếu file, backend không phục vụ được hoặc trình phát gặp vấn đề codec. Kiểm tra từng lớp; không xóa DB để thử chữa. Hồ sơ cũ có ghi nhận đường dẫn thiếu file nhưng chưa xác nhận lại số lượng hiện tại. [S04, S15]

**20. Chỉ số.** Precision nói về độ đúng trong kết quả phát hiện; recall nói về mức tìm được sự kiện thật. mAP tổng hợp chất lượng phát hiện theo quy tắc đánh giá, không phải tỷ lệ người thi bị bắt đúng. Không hoán đổi tên chỉ số. Manifest chỉ gắn số liệu huấn luyện với `TRAINING_VALIDATION_ONLY`. [S10]

## Phản biện

**21. Độ chính xác thực địa.** Nhóm chưa có đủ đánh giá độc lập để công bố một tỷ lệ thực địa. Manifest có giá trị validation lịch sử nhưng không thay thế kiểm thử trên phòng thi đại diện. Cần thu dữ liệu có nhãn và công bố điều kiện, báo nhầm, bỏ sót. [S10, S13]

**22. Ba camera.** Code hiện có chế độ ba nguồn. Hồ sơ nghiệm thu đã đọc vẫn ghi phần cứng đang chờ và có thử synthetic. Em chưa có bằng chứng để khẳng định ba camera vật lý đã nghiệm thu đồng thời. Cần thử đúng thiết bị dự thi và kiểm tra từng nguồn. [S08, S16]

**23. Quay đầu hợp lệ.** Tình huống đó có thể tạo nghi vấn, nên hệ thống giữ vai trò hỗ trợ. Giám thị xem clip và bối cảnh trước khi xác nhận. Cần đánh giá nhóm hành vi hợp lệ để đo báo nhầm. [S01, S11]

**24. Che khuất/cuối phòng.** Nhóm không bảo đảm phát hiện được trong mọi góc nhìn hoặc mức che khuất. Cần thử theo khoảng cách, độ phân giải và cách đặt camera, rồi chỉ công bố phạm vi đã đo. [S13]

**25. Thay giám thị.** Không. Phần mềm cung cấp dấu hiệu và video cho người xem xét. Quyết định xử lý thí sinh không thuộc chức năng tự động của dự án. [S01]

**26. Test đạt.** Test phần mềm kiểm tra một số quy tắc và hợp đồng dữ liệu trong điều kiện đã định. Nó không đo đầy đủ khả năng phát hiện trên tất cả người, góc camera và phòng thi. Phiên bản hiện tại còn có thay đổi so với log cũ. [S13, S16]

**27. Điểm từ 90%.** Nhánh scheduler khởi tạo `red_confidence = 90.0`, sau đó lấy giá trị lớn hơn giữa điểm này và điểm cảnh báo. Đây là giới hạn xử lý điểm đã thấy trong code, không chứng minh mô hình luôn tự tin cao. Cần rà soát ngữ nghĩa và kiểm thử trước khi dùng điểm này trong báo cáo. [S03]

**28. Tập độc lập.** Cần ghi nguồn, thời điểm thu, chia tập theo điều kiện/người/phiên phù hợp và kiểm tra trùng lặp. Dữ liệu đã dùng để chỉnh ngưỡng không còn là tập giữ kín. Hồ sơ hiện ghi chưa đủ đánh giá holdout độc lập và kiểm tra trùng gần còn thiếu. [S10, S13]

**29. Quyền riêng tư.** Lưu cục bộ giảm nhu cầu gửi video ra dịch vụ ngoài, nhưng người có quyền truy cập máy vẫn có thể xem dữ liệu. Cần quy định quyền xem, thời hạn lưu và quyền sử dụng hình ảnh. Dự án chưa được chứng minh bảo đảm quyền riêng tư tuyệt đối. Đây là nguyên tắc vận hành, không phải kết luận tuân thủ pháp lý. [S01, S07]

**30. Demo không bắt được.** Em sẽ ghi nhận đúng lượt thử chưa tạo được kết quả, kiểm tra nguồn và trạng thái xử lý rồi chuyển clip/video dự phòng có công bố. Sau buổi thi cần tái hiện tình huống và ghi điều kiện để phân tích. Không dùng dữ liệu giả lập hoặc tạo sự cố test để tuyên bố AI đã phát hiện. [S02, S09]

## Khi câu hỏi vượt quá bằng chứng

Mẫu ngắn: “Phần đã có bằng chứng là … Nguồn kiểm tra là … Với điều kiện thầy/cô vừa hỏi, nhóm chưa đo nên chưa thể khẳng định. Cách kiểm chứng tiếp theo là …”.

Ví dụ: “Nhóm chưa đo mức tiết kiệm thời gian của giám thị. Để đánh giá cần so sánh cùng nhiệm vụ với và không có phần mềm, ghi thời gian rà soát cùng số sự kiện tìm được.” Đây là đề xuất nghiên cứu, không được kể như thí nghiệm đã làm.
