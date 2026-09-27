# BỘ SLIDE THUYẾT TRÌNH & KỊCH BẢN CHI TIẾT (SPEAKER SCRIPT)
## DỰ ÁN NGHIÊN CỨU KHOA HỌC KỸ THUẬT DÀNH CHO HỌC SINH TRUNG HỌC
**Đề tài:** Hệ Thống Hỗ Trợ Giám Sát Phòng Thi Bằng Thị Giác Máy Tính & Trích Xuất Video Bằng Chứng  
**Lĩnh vực:** Phần mềm hệ thống (System Software)  
**Đối tượng người nghe:** Học sinh THPT (Cấp 3) chưa có kiến thức chuyên sâu về Trí tuệ nhân tạo (AI)  
**Thời lượng thuyết trình chuẩn:** 10 – 12 phút (+ 5 phút Hỏi - Đáp Q&A)

---

# PHẦN 1: BỐ CỤC TỔNG THỂ BỘ SLIDE (SLIDE DECK BLUEPRINT)

| Slide | Tiêu đề Slide | Thông điệp cốt lõi | Ẩn dụ đời thường (Dành cho HS Cấp 3) |
| :---: | :--- | :--- | :--- |
| **01** | Bìa: AI Giám Sát Phòng Thi | Giới thiệu dự án & Nhóm nghiên cứu | "Người bạn đồng hành công nghệ trong phòng thi" |
| **02** | Vấn đề: 1 Thầy Cô vs 30 Bạn | Giám thị cũng là con người, mắt cũng mỏi | "Thử nhìn đồng hồ kim giây 30 phút không chớp mắt" |
| **03** | Giải pháp: Hệ Thống Của Chúng Em | AI là Trợ lý hỗ trợ, không thay thế con người | "Trợ lý đắc lực mang kính lúp cho giám thị" |
| **04** | Tổng quan: 4 Bước Hệ Thống Vận Hành | Thu nhận → Phát hiện → Cắt clip làm bằng chứng | "Cơ chế giống Camera hành trình xe ô tô / Instant Replay" |
| **05** | Mắt thần 1: Bắt Quả Tang Điện Thoại | Nhận diện vật thể thông minh (YOLO) | "Trò chơi tìm đồ vật siêu tốc trong 0,03 giây" |
| **06** | Mắt thần 2: Thấy Cả Tư Thế Quay Đầu | Ước lượng tư thế 17 điểm mốc xương | "Vẽ Người Que (Stickman) từ cử động thực tế" |
| **07** | Bí quyết 1: Chống Báo Động Oan | Phân biệt quay đầu mỏi cổ vs Nhìn bài bạn | "Quy tắc 1,25 giây: Hắt xì hơi thì không bị phạt" |
| **08** | Bí quyết 2: Camera Hành Trình RingBuffer | Cắt clip 15 giây (5s trước + 10s sau sự kiện) | "Bộ nhớ quay vòng: Giữ khoảnh khắc đắt giá nhất" |
| **09** | Đột phá Kỹ thuật: Luồng Đôi Không Giật Lag | Kiến trúc 2 luồng: Quay phim & Thám tử | "Cameraman quay 15fps, Thám tử soi ảnh mới nhất" |
| **10** | Trực quan: Bảng Điều Khiển Giám Thị | Giao diện tối giản, hiện đại, xem lại clip tức thì | "Nút bấm Xem Clip & Phê duyệt trong 1 cú nhấp chuột" |
| **11** | Con số Biết Nói: Thử Nghiệm Thực Tế | 83/83 bài test vượt qua, 439 sự cố được ghi nhận | "Sản phẩm chạy thật, đo thật, không chém gió" |
| **12** | Đạo đức Công nghệ: Văn Hóa Học Đường | 100% Offline, Không quét mặt, Tôn trọng học sinh | "AI công tâm, bảo vệ quyền riêng tư tuyệt đối" |
| **13** | Tổng Kết & Hướng Đi Tương Lai | Đóng góp cho kỳ thi công bằng & Nghiêm túc | "Từ phòng thi trường mình đến kỳ thi quốc gia" |
| **14** | Lời Cảm Ơn & Sẵn Sàng Trả Lời Câu Hỏi | Kết thúc bài nói, mở đầu phần tương tác | "Mời thầy cô và các bạn cùng đặt câu hỏi!" |

---

# PHẦN 2: CHI TIẾT TỪNG SLIDE & KỊCH BẢN THUYẾT TRÌNH (WORD-FOR-WORD SCRIPT)

---

### SLIDE 01: TRANG TIÊU ĐỀ (TITLE SLIDE)
- **Tiêu đề lớn:** HỆ THỐNG HỖ TRỢ GIÁM SÁT PHÒNG THI BẰNG THỊ GIÁC MÁY TÍNH VÀ TRÍCH XUẤT VIDEO BẰNG CHỨNG
- **Tiêu đề phụ:** Ứng dụng Trí tuệ Nhân tạo hỗ trợ kỳ thi công bằng, minh bạch và nhân văn
- **Thông tin nhóm:**
  - Nhóm tác giả: [Họ và tên thí sinh 1 & Thí sinh 2]
  - Giáo viên hướng dẫn: [Họ và tên GVHD]
  - Đơn vị: Trường THPT [Tên Trường], Đoàn dự thi TP. Hà Nội
- **Gợi ý hình ảnh/bố cục:** Nền tối xám than công nghiệp lịch lãm (Dark Charcoal), biểu tượng chiếc khiên bảo vệ công bằng và chiếc camera AI viền xanh ngọc bích (Emerald).

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~45 giây)
> *"Kính thưa quý thầy cô trong Ban Giám khảo, thưa toàn thể các bạn học sinh thân mến!*
>
> *Là học sinh cấp 3, chắc hẳn mỗi chúng ta ở đây đều đã từng bước qua rất nhiều kỳ thi quan trọng: thi học kỳ, thi chọn học sinh giỏi, và sắp tới là kỳ thi Tốt nghiệp THPT. Chúng ta đều hiểu rằng, cảm giác tuyệt vời nhất sau một kỳ thi là biết rằng mọi sự nỗ lực chân chính của mình đều được đền đáp một cách công bằng nhất.*
>
> *Thế nhưng, làm thế nào để đảm bảo một phòng thi thực sự minh bạch mà không tạo ra bầu không khí nặng nề, căng thẳng? Hôm nay, nhóm chúng em rất vinh dự được đại diện mang đến Dự án nghiên cứu khoa học: **'Hệ thống hỗ trợ giám sát phòng thi bằng thị giác máy tính và trích xuất video bằng chứng'**. Em xin phép được bắt đầu bài thuyết trình ngay sau đây!"*

---

### SLIDE 02: BÀI TOÁN THỰC TẾ TRONG PHÒNG THI
- **Tiêu đề:** TẠI SAO GIÁM THỊ CẦN MỘT TRỢ LÝ CÔNG NGHỆ?
- **Bố cục 3 khối so sánh:**
  1. **Áp lực thị giác của Thầy Cô:** Một phòng 24–30 thí sinh, kéo dài 90–120 phút. Khoa học chứng minh: Sau 30 phút tập trung cao độ, mắt người bắt đầu mỏi và giảm khả năng chú ý (Hiệu ứng Mackworth Clock).
  2. **Hành vi vi phạm diễn ra chớp nhoáng:** Thò tay mở điện thoại hay nghiêng đầu liếc bài bạn bên cạnh chỉ mất đúng 1 đến 2 giây.
  3. **Khó khăn khi xử lý:** "Lời nói gió bay" — nếu không có chứng cứ hình ảnh rõ ràng trước và sau sự việc, việc nhắc nhở hay lập biên bản rất dễ gây tranh cãi và áp lực tâm lý cho cả thầy lẫn trò.
- **Gợi ý hình ảnh:** Bức ảnh minh họa phòng thi quen thuộc với dãy bàn gỗ, hình ảnh một chiếc đồng hồ đếm ngược và hình vẽ góc khuất tầm nhìn của mắt người.

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~1 phút)
> *"Các bạn hãy thử tưởng tượng: Trong một phòng thi tiêu chuẩn có khoảng 24 đến 30 bạn học sinh ngồi ngay ngắn làm bài suốt 90 đến 120 phút. Chỉ có 2 thầy cô giám thị phải đứng bao quát toàn bộ căn phòng rộng lớn ấy.*
>
> *Theo nghiên cứu tâm lý học nổi tiếng của tiến sĩ Mackworth, sau 30 phút nhìn chăm chú, mắt con người sẽ bị mỏi và khả năng phát hiện các cử động bất thường sẽ tụt giảm rất nhanh. Trong khi đó, các hành vi vi phạm như lén rút điện thoại xem tài liệu, hay ngoái đầu sang bàn bên cạnh chép bài, thường chỉ diễn ra chớp nhoáng trong vòng 1 đến 2 giây ở góc khuất.*
>
> *Nếu thầy cô bắt gặp bằng mắt thường, khi nhắc nhở, học sinh có thể phản xạ chối: 'Em đâu có làm gì, em chỉ mỏi cổ thôi mà!'. Nếu không có bằng chứng quay lại rõ ràng, giám thị sẽ rơi vào tình thế rất khó xử. Đó chính là lý do chúng em đặt câu hỏi: **Tại sao không chế tạo một trợ lý thông minh giúp thầy cô quan sát liên tục và lưu lại bằng chứng khách quan?**"*

---

### SLIDE 03: MỤC TIÊU VÀ NGUYÊN TẮC "CON NGƯỜI LÀ TRUNG TÂM"
- **Tiêu đề:** TRIẾT LÝ DỰ ÁN: HỖ TRỢ, TUYỆT ĐỐI KHÔNG THAY THẾ CON NGƯỜI
- **Bố cục 3 điểm nhấn:**
  - **Trợ lý 'Mắt thần' (AI Assistant):** Tự động phát hiện 2 hành vi nguy cơ cao nhất: Sử dụng điện thoại & Quay đầu nghi vấn kéo dài.
  - **Bằng chứng khách quan (15s Video Clip):** Cắt tự động đoạn video gồm 5 giây trước và 10 giây sau khi có sự cố.
  - **Quyền quyết định 100% thuộc về Thầy Cô (Human-in-the-Loop):** AI chỉ đưa ra gợi ý và video; chính giám thị mới là người xem lại và bấm 'Xác nhận' hoặc 'Bỏ qua'.
- **Gợi ý hình ảnh:** Biểu tượng sự phối hợp nhịp nhàng giữa Bàn tay con người và Mạch vi xử lý công nghệ (Human-AI Collaboration), không có hình ảnh người máy phán xét rùng rợn.

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~50 giây)
> *"Để giải quyết vấn đề đó, chúng em xây dựng một hệ thống phần mềm chạy ngay trên máy tính của thầy cô giám thị.*
>
> *Nhưng trước khi đi vào kỹ thuật, em muốn nhấn mạnh triết lý cốt lõi của đề tài: **Hệ thống này sinh ra để làm TRỢ LÝ, chứ tuyệt đối không thay thế con người.**
>
> *Nhiều bạn học sinh nghe đến 'AI giám thị' thì sợ hãi nghĩ rằng máy tính sẽ tự động trừ điểm hay đuổi mình ra khỏi phòng thi. Không hề có chuyện đó! Hệ thống của chúng em tuân thủ nguyên tắc 'Human-in-the-Loop' — nghĩa là AI chỉ đóng vai trò người phụ tá soi kính lúp: khi thấy dấu hiệu bất thường, nó cắt ngay một đoạn video bằng chứng dài 15 giây gửi lên màn hình. Thầy cô giám thị sẽ trực tiếp mở video lên xem, cân nhắc bối cảnh thực tế và là người duy nhất đưa ra quyết định cuối cùng."*

---

### SLIDE 04: BỨC TRANH TOÀN CẢNH: HỆ THỐNG HOẠT ĐỘNG THẾ NÀO?
- **Tiêu đề:** NGUYÊN LÝ HOẠT ĐỘNG: GIỐNG NHƯ CAMERA HÀNH TRÌNH Ô TÔ
- **Sơ đồ chu trình 4 bước đơn giản:**
  1. **Bước 1 - Ghi hình:** Camera phòng thi quay liên tục ở tốc độ ~15 khung hình/giây.
  2. **Bước 2 - Phân tích AI:** Mô hình thông minh quét tìm điện thoại và đo hướng quay đầu.
  3. **Bước 3 - Cảnh báo & Trích xuất:** Khi có dấu hiệu vi phạm kéo dài, hệ thống lập tức xuất video MP4 dài 15 giây.
  4. **Bước 4 - Thẩm tra:** Giám thị xem video phát lại đúng tốc độ thực và phê duyệt trên màn hình.
- **Gợi ý hình ảnh:** Sơ đồ dòng chảy (Flowchart) trực quan với 4 biểu tượng hoạt họa dễ thương, mũi tên chuyển động mượt mà.

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~50 giây)
> *"Để các bạn dễ hình dung, hệ thống của chúng em hoạt động hệt như một chiếc **Camera hành trình trên xe ô tô** hay **tính năng Instant Replay quay chậm trong các trận đấu bóng đá**.*
>
> *Quy trình diễn ra theo 4 bước khép kín:
> Đầu tiên, camera gắn trên bục giảng thu lại toàn cảnh phòng thi.
> Tiếp theo, 'bộ não' AI sẽ liên tục quan sát từng khung hình để phát hiện xem có chiếc điện thoại nào xuất hiện trên bàn hay bạn nào đang ngoái đầu sang bài bạn bên cạnh hay không.
> Nếu phát hiện hành vi nghi vấn kéo dài, chuông cảnh báo âm thầm nổi lên trên màn hình thầy cô, đồng thời hệ thống tự động 'lùi thời gian' để cắt lại đoạn video 5 giây trước đó và quay tiếp 10 giây sau đó.
> Cuối cùng, thầy cô chỉ việc bấm vào xem lại clip để biết chính xác sự thật vừa diễn ra. Rất nhanh gọn và minh bạch!"*

---

### SLIDE 05: "MẮT THẦN" 1: PHÁT HIỆN ĐIỆN THOẠI TRONG 0,03 GIÂY
- **Tiêu đề:** THỊ GIÁC MÁY TÍNH LÀ GÌ? LÀM SAO MÁY NHẬN RA ĐIỆN THOẠI?
- **Giải thích khái niệm cơ bản:**
  - *Thị giác máy tính (Computer Vision):* Dạy máy tính 'hiểu' bức ảnh như mắt người.
  - *Mô hình YOLO (You Only Look Once):* Thuật toán quét nhanh như chớp. Thay vì xem từng góc, nó nhìn toàn bộ bức ảnh trong 1 lần duy nhất để tìm ra đồ vật.
  - *Huấn luyện:* Máy tính đã được học qua gần 3.000 bức ảnh chụp điện thoại ở mọi tư thế: để trên bàn, cầm dưới ngăn bàn, nghiêng ngửa, ngược sáng...
- **Kết quả:** Đạt độ chính xác nhận diện trên tập kiểm thử nội bộ khoảng ~80% (Precision: 80,4%, mAP@0.5 = 78,58%).
- **Gợi ý hình ảnh:** Một bức ảnh mô phỏng có khung viền đỏ (Bounding Box) ôm khít chiếc smartphone trên mặt bàn gỗ kèm chỉ số `phone: 0.89`.

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~1 phút 15 giây)
> *"Bây giờ, chúng ta hãy cùng khám phá xem: Làm sao một chiếc máy tính vô tri lại có thể 'nhìn' thấy chiếc điện thoại thông minh?
>
> *Các bạn biết đấy, đối với máy tính, một bức ảnh chụp từ camera chỉ là một ma trận gồm hàng triệu con số pixel khô khốc. Để máy tính 'hiểu' được bức ảnh, chúng em ứng dụng một công nghệ gọi là **Thị giác máy tính** với mô hình mạng nơ-ron mang tên **YOLO** — viết tắt của cụm từ 'You Only Look Once' nghĩa là 'Bạn chỉ cần nhìn một lần'.
>
> *Nó giống như khi các bạn chơi trò 'Tìm đồ vật bị giấu': Thay vì phải lấy kính lúp soi từng centimet vuông, mắt các bạn chỉ cần lướt qua cả bức tranh một lần là định vị được ngay món đồ cần tìm.
>
> *Chúng em đã cho máy tính học gần 3.000 bức ảnh chụp điện thoại ở đủ mọi góc độ: từ điện thoại màn hình đen đặt trên bàn gỗ, điện thoại giấu nửa phần dưới tờ giấy nháp, cho đến điện thoại cầm nghiêng trong lòng bàn tay. Nhờ vậy, chỉ mất khoảng 0,03 giây cho một khung hình, mô hình đã có thể khoanh một chiếc hộp màu đỏ chính xác quanh chiếc điện thoại và báo ngay cho giám thị!"*

---

### SLIDE 06: "MẮT THẦN" 2: MÔ HÌNH "NGƯỜI QUE" PHÁT HIỆN QUAY ĐẦU
- **Tiêu đề:** TƯ THẾ QUAY ĐẦU: VẼ "NGƯỜI QUE" (STICKMAN) ĐỂ BẮT HÀNH VI
- **Giải thích trực quan:**
  - *Ước lượng tư thế (Pose Estimation):* Máy tính tự động chấm 17 điểm khớp xương chính trên cơ thể thí sinh (Mũi, 2 Mắt, 2 Tai, 2 Vai, Khuỷu tay...).
  - *Quy tắc hình học thông minh:* 
    - Khi nhìn thẳng vào bài thi: Mũi nằm ở chính giữa hai tai; khoảng cách từ Mũi tới Tai Trái bằng Mũi tới Tai Phải.
    - Khi quay đầu nhìn bài bạn: Mũi sẽ lệch hẳn về một bên tai; đồng thời trục Mắt bị xoay chéo so với trục Vai.
- **Gợi ý hình ảnh:** Hình ảnh đồ họa trực quan: Bên trái là bạn học sinh ngồi làm bài được nối các đường line xương màu xanh lá (Normal); bên phải là bạn học sinh quay ngoắt sang phải, khung xương chuyển sang màu đỏ rực (Alert).

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~1 phút 15 giây)
> *"Nhận diện điện thoại đã khó, nhưng phát hiện hành vi quay đầu nhìn bài bạn còn tinh tế hơn rất nhiều. Làm sao máy tính phân biệt được bạn đang nhìn bài thi của mình hay đang nhìn bài thi của bạn ngồi cạnh?
>
> *Để giải bài toán này, chúng em không dùng các cảm biến gắn lên người, mà sử dụng thuật toán **Ước lượng tư thế (Pose Estimation)**. Mô hình sẽ biến hình ảnh của mỗi thí sinh thành một **'Người Que' (Stickman)** thông minh bằng cách chấm 17 điểm mốc quan trọng: đỉnh mũi, 2 mắt, 2 tai và 2 bờ vai.
>
> *Nguyên lý hình học cực kỳ đơn giản mà thú vị:
> Khi chúng mình chăm chú nhìn thẳng xuống bài thi, chóp mũi sẽ nằm ngay chính giữa hai tai. Khoảng cách từ mũi đến tai trái và tai phải là hoàn toàn cân xứng.
> Nhưng khi một bạn ngoái đầu sang trái để xem bài bạn bên cạnh, chóp mũi lập tức dịch chuyển áp sát vào tai trái, trong khi tai phải bị che khuất hoặc lệch xa ra. Đồng thời, đường nối hai con mắt sẽ bị vặn chéo so với đường nối hai bờ vai.
>
> *Từ độ lệch hình học này, hệ thống sẽ tính ra một 'điểm số nghi vấn' theo thời gian thực. Càng quay đầu mạnh, điểm số càng tăng vọt!"*

---

### SLIDE 07: BÍ QUYẾT 1: LÀM SAO KHÔNG BÁO ĐỘNG OAN?
- **Tiêu đề:** BÀI TOÁN HẮT XÌ HƠI: BỘ LỌC CHỐNG BÁO ĐỘNG GIẢ
- **Vấn đề thực tế:** Làm bài thi căng thẳng, thí sinh có thể mỏi cổ xoay đầu qua lại 0,5 giây, hoặc quay sang hắt xì hơi, cúi nhặt bút rơi. Nếu máy cứ thấy quay đầu là báo động thì sẽ gây hoảng loạn!
- **Giải pháp kỹ thuật của nhóm:**
  - **Cờ VÀNG (Cảnh báo nhẹ):** Khi điểm nghi vấn vượt ngưỡng nhưng chưa đủ thời gian → Chỉ hiện nhẹ trên màn hình.
  - **Cờ ĐỎ (Vi phạm thực sự):** Hành vi quay đầu phải **duy trì liên tục từ 1,25 giây trở lên** (khoảng gián đoạn không quá 0,75 giây).
  - **Bộ lọc làm mượt EMA:** Lọc bỏ các rung lắc ngẫu nhiên của camera và ánh sáng.
- **Gợi ý hình ảnh:** Đồ thị trực quan dạng sóng: Sóng ngắn < 1.25s (Nhãn: 'Chỉ mỏi cổ - Bỏ qua'); Sóng dài kéo dài > 1.25s (Nhãn: 'Nhìn bài bạn - BẬT CỜ ĐỎ').

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~1 phút)
> *"Tuy nhiên, trong thực tế, các bạn học sinh làm bài thi rất hay ngọ nguậy: Có bạn ngồi lâu mỏi cổ quá thì xoay đầu sang hai bên thư giãn mất nửa giây; có bạn quay sang góc để hắt xì hơi; có bạn quay đầu nhìn đồng hồ treo tường. Nếu hệ thống cứ thấy đầu lệch đi là rú còi báo vi phạm, thì đó là một hệ thống tồi tệ và gây phiền hà!
>
> *Để giải quyết vấn đề này, nhóm chúng em đã lập trình một cơ chế gọi là **'Bộ lọc thời gian chống báo động oan'**.
>
> *Quy tắc rất nhân văn:
> Nếu bạn chỉ xoay đầu thoáng qua dưới 1,25 giây rồi quay lại làm bài ngay, hệ thống chỉ ghi nhận một tín hiệu 'Cờ Vàng' âm thầm và tự động xóa sau 0,75 giây. Không có bất kỳ cảnh báo nào làm phiền thầy cô cả.
> Nhưng nếu góc quay đầu nghi vấn ấy bị giữ bất động liên tục từ **1,25 giây trở lên** — khoảng thời gian đủ để đọc lén đáp án trắc nghiệm câu A, B, C của bạn bên cạnh — hệ thống mới chính thức leo thang thành **'Cờ Đỏ'** và kích hoạt quy trình lưu bằng chứng.
> Nhờ vậy, hệ thống hoàn toàn loại bỏ được những hiểu lầm không đáng có!"*

---

### SLIDE 08: BÍ QUYẾT 2: TRÍCH XUẤT VIDEO "QUAY NGƯỢC THỜI GIAN"
- **Tiêu đề:** CƠ CHẾ RINGBUFFER: CẮT CLIP CẢ QUÁ KHỨ VÀ TƯƠNG LAI
- **Câu hỏi hóc búa:** Khi phát hiện vi phạm ở giây thứ *t*, nếu lúc đó mới bắt đầu bấm quay phim thì đã quá muộn (học sinh đã kịp cất tài liệu đi rồi)!
- **Sáng tạo kỹ thuật:** **Bộ đệm vòng (Time-based RingBuffer):**
  - Luôn lưu sẵn 5 giây video trong bộ nhớ RAM (Quá khứ - Pre-roll).
  - Khi Cờ Đỏ kích hoạt tại *t*<sub>event</sub>: Lấy ngay 5 giây quá khứ + quay thêm 10 giây tương lai (Post-roll).
  - Kết quả: Đoạn clip trọn vẹn 15 giây ghi lại từ lúc chuẩn bị thò tay lấy điện thoại đến khi thực hiện và kết thúc hành vi.
  - Thuật toán tái lấy mẫu (Resampling) giúp video phát mượt chuẩn tốc độ 1.0x, không bị tua nhanh giật cục.
- **Gợi ý hình ảnh:** Sơ đồ dòng thời gian trực quan: Khung màu xanh (-5s đến 0s: Bắt đầu lấy máy), Mốc đỏ (0s: AI bắt quả tang), Khung màu vàng (0s đến +10s: Cất máy hoặc tiếp tục sử dụng).

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~1 phút 15 giây)
> *"Một câu hỏi thú vị đặt ra là: Nếu tại thời điểm này AI mới nhìn thấy chiếc điện thoại, thì làm sao quay lại được cảnh bạn đó vừa thò tay vào hộc bàn rút điện thoại ra từ 3 giây trước? Chẳng lẽ máy tính biết 'quay ngược thời gian'?
>
> *Đúng là như vậy đấy các bạn ạ! Nhóm chúng em đã thiết kế một giải pháp kỹ thuật gọi là **Bộ đệm vòng (RingBuffer)** trong bộ nhớ RAM của máy tính.
>
> *Bộ đệm này giống như một chiếc băng chuyền tròn luôn chuyển động: Nó liên tục giữ lại những thước phim của 5 giây vừa trôi qua. Khung hình mới đi vào thì khung hình quá 5 giây sẽ tự rơi ra ngoài.
>
> *Ngay khoảnh khắc AI kích hoạt Cờ Đỏ, hệ thống lập tức 'đóng băng' 5 giây quá khứ quý giá đó lại, rồi thong thả quay tiếp 10 giây tiếp theo của tương lai. Sau đó, nó ráp hai nửa lại thành một đoạn clip hoàn chỉnh dài đúng 15 giây.
>
> *Khi mở clip này lên, thầy cô sẽ thấy trọn vẹn cả một câu chuyện: từ lúc bạn thí sinh ngó nghiêng xung quanh, thò tay xuống ngăn bàn lấy điện thoại ra, cho đến phản ứng sau đó. Bằng chứng rõ ràng đến mức không thể chối cãi!"*

---

### SLIDE 09: ĐỘT PHÁ TỐC ĐỘ: KIẾN TRÚC 2 LUỒNG ĐỘC LẬP
- **Tiêu đề:** GIẢI QUYẾT TẮC NGHẼN: BÀI TOÁN "QUAY PHIM VÀ THÁM TỬ"
- **Nghịch lý phần cứng:**
  - Camera quay rất nhanh: 15 bức ảnh/giây.
  - Mô hình AI trên máy tính thường suy nghĩ chậm hơn: chỉ soi được khoảng 3 bức ảnh/giây (mất ~360ms mỗi ảnh).
  - *Nếu làm theo cách thông thường:* Hàng đợi sẽ bị ùn tắc, camera sẽ bị lag trễ hàng chục giây so với thực tế!
- **Giải pháp của nhóm (Kiến trúc Dual-Stream):**
  - **Luồng 1 (Người quay phim):** Chạy độc lập, gom liên tục 15 ảnh/giây ném thẳng vào RingBuffer để không bỏ sót bất kỳ khoảnh khắc nào.
  - **Luồng 2 (Thám tử AI):** Cứ mỗi khi soi xong một bức ảnh, thám tử sẽ bỏ qua các ảnh cũ và **bốc ngay bức ảnh MỚI NHẤT trên bàn** để phân tích.
- **Gợi ý hình ảnh:** Hình ảnh ẩn dụ một anh Cameraman quay phim thoăn thoắt và một bác Thám tử cầm kính lúp soi ảnh; hai người làm việc song song không chờ đợi nhau.

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~1 phút 15 giây)
> *"Trong quá trình lập trình, chúng em đã đụng phải một bức tường kỹ thuật rất lớn: Đó là hiện tượng giật lag và trễ hình.
>
> *Camera thông thường thu nhận tới 15 khung hình mỗi giây. Nhưng máy tính trong phòng thi thường là máy tính văn phòng bình thường, chip AI phải mất khoảng 0,36 giây mới phân tích xong một hình — tức là một giây nó chỉ soi được khoảng 3 hình.
> Nếu cứ bắt camera phải đứng đợi AI phân tích xong mới được quay tiếp, thì chỉ sau 1 phút, hình ảnh trên màn hình sẽ bị trễ cả chục giây so với đời thực!
>
> *Để giải bài toán này, nhóm chúng em đã sáng tạo ra **Kiến trúc hai luồng phân tách (Dual-Stream)**, ví như sự phối hợp giữa một **Anh thợ quay phim** và một **Bác thám tử**:
> - Anh thợ quay phim làm việc độc lập: Cứ 1 giây anh quay đủ 15 khung hình ném thẳng vào kho lưu trữ RingBuffer. Anh không bao giờ dừng lại chờ ai.
> - Còn Bác thám tử AI: Bác cứ bình tĩnh soi kỹ từng bức ảnh. Soi xong bức ảnh này, bác không nhìn lại những ảnh cũ đã trôi qua, mà bốc ngay bức ảnh mới nhất đang xuất hiện trước mắt để phân tích.
>
> *Nhờ tách rời hai nhiệm vụ này, hệ thống vừa ghi trọn vẹn từng khoảnh khắc video mượt mà, vừa đảm bảo cảnh báo AI luôn bám sát theo thời gian thực mà không bao giờ bị nghẽn mạng!"*

---

### SLIDE 10: GIAO DIỆN GIÁM THỊ: TRỰC QUAN & DỄ SỬ DỤNG
- **Tiêu đề:** BẢNG ĐIỀU KHIỂN EXAMVISION: ĐƠN GIẢN, RÕ RÀNG, CHUYÊN NGHIỆP
- **Đặc điểm giao diện:**
  - Thiết kế theo chuẩn hiện đại **Anti-Slop**: Nền tối bảo vệ mắt, không màu mè hoa mỹ, thông tin hiển thị dày dặn, tập trung.
  - **Khu vực Trái:** Lưới theo dõi camera trực tiếp kèm thanh đo nhịp tim hệ thống (Acquisition FPS, AI FPS).
  - **Khu vực Phải:** Danh sách sự cố vi phạm cờ Đỏ xuất hiện tức thời.
  - **Hộp thoại xem lại Clip:** Bấm một nút là xem lại đoạn video 15s với tính năng lặp lại (Loop) và 2 nút bấm quyết định: **[Xác nhận]** hoặc **[Bỏ qua]**.
- **Gợi ý hình ảnh:** Ảnh chụp màn hình thực tế của giao diện Dashboard (`live_monitor_multi_cam.png` hoặc `video_evidence_modal.png`) sắc nét, chuyên nghiệp.

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~50 giây)
> *"Trên màn hình lúc này là giao diện thực tế của phần mềm do chính chúng em thiết kế bằng công nghệ React 19 mới nhất.
>
> *Chúng em tuân thủ triết lý thiết kế tối giản công nghiệp: Tông màu tối Slate dịu mắt giúp thầy cô không bị chói khi ngồi trực phòng thi suốt nhiều giờ liền.
>
> *Màn hình chia làm hai khu vực rất trực quan:
> - Bên trái là màn hình truyền hình trực tiếp từ các camera gắn trong phòng. Trên góc mỗi camera có đồng hồ đo tốc độ thực tế.
> - Khi có sự cố, một thẻ cảnh báo màu đỏ sẽ xuất hiện ngay ở cột bên phải. Thầy cô chỉ cần bấm vào nút 'Xem Clip'. Một cửa sổ sẽ hiện lên phát đi phát lại đoạn video bằng chứng 15 giây quay cận cảnh hành vi đó.
> - Sau khi xem xong, thầy cô có thể bấm nút 'Xác nhận' để lưu vào biên bản, hoặc bấm 'Bỏ qua' nếu thấy bạn thí sinh không hề có ý đồ xấu. Mọi thao tác chỉ diễn ra trong vòng 5 giây!"*

---

### SLIDE 11: KẾT QUẢ THỰC NGHIỆM: NHỮNG CON SỐ BIẾT NÓI
- **Tiêu đề:** THỬ NGHIỆM KHOA HỌC: SẢN PHẨM CHẠY THẬT, SỐ LIỆU THẬT
- **Bảng số liệu kiểm chứng tự động:**
  - **83/83 bài kiểm thử phần mềm:** Vượt qua 100% (Backend Unit Tests Pass tuyệt đối).
  - **Đo tải liên tục 125,1 giây:** Thu nhận thành công 1.952 khung hình (Tốc độ ổn định 15,6 FPS).
  - **Bộ nhớ RAM ổn định:** Thử nghiệm kịch bản camera Full HD (1080p), RAM giữ mức cân bằng ~380 MB, không hề bị rò rỉ hay tràn bộ nhớ.
  - **439 sự cố thực tế:** Đã được ghi nhận vào cơ sở dữ liệu SQLite an toàn (WAL Mode), lưu trữ 382 clip bằng chứng kiểm toán hợp lệ trên đĩa cứng.
- **Gợi ý hình ảnh:** Biểu đồ tròn thể hiện 100% Test Pass và bảng số liệu đo đạc kỹ thuật gọn gàng, minh bạch.

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~1 phút)
> *"Kính thưa Ban Giám khảo, một nghiên cứu khoa học chân chính phải được chứng minh bằng những con số thực nghiệm cụ thể chứ không thể nói suông.
>
> *Chúng em đã xây dựng một bộ kiểm thử tự động toàn diện với **83 bài kiểm tra đơn vị** và kết quả đạt **83/83 bài test đỗ tuyệt đối**.
>
> *Trong phiên chạy thử nghiệm đo tải liên tục hơn 2 phút:
> - Hệ thống đã tiếp nhận 1.952 khung hình từ camera ở tốc độ cực kỳ ổn định là 15,6 khung hình/giây.
> - Trí tuệ nhân tạo đã thực hiện 354 lượt suy luận chuyên sâu và phát hiện thành công các tình huống vi phạm giả định.
> - Khi thử nghiệm với camera độ phân giải cao Full HD 1080p, mức tiêu thụ bộ nhớ RAM tự động dừng lại ở mức cân bằng khoảng 380MB, hoàn toàn không bị nóng máy hay tràn RAM.
>
> *Hiện tại, trong cơ sở dữ liệu thực nghiệm của hệ thống đã lưu trữ an toàn 439 bản ghi sự cố cùng hàng trăm đoạn video MP4 bằng chứng sẵn sàng truy xuất bất kỳ lúc nào!"*

---

### SLIDE 12: ĐẠO ĐỨC CÔNG NGHỆ: BẢO VỆ TỐI ĐA QUYỀN HỌC SINH
- **Tiêu đề:** ĐẠO ĐỨC AI & QUYỀN RIÊNG TƯ: NGUYÊN TẮC "3 KHÔNG"
- **3 Cam kết an toàn tuyệt đối:**
  1. **KHÔNG quét khuôn mặt (No Face ID):** Hệ thống chỉ nhìn nhận hình dạng cử động cơ thể và đồ vật, tuyệt đối không thu thập sinh trắc học khuôn mặt hay danh tính cá nhân.
  2. **KHÔNG gửi dữ liệu lên mạng (100% Offline):** Hoạt động hoàn toàn trên máy tính cục bộ trong phòng thi, không cần cắm mạng Internet, không sợ lộ lọt dữ liệu ra ngoài.
  3. **KHÔNG tự động kỷ luật (Human Decides):** AI không bao giờ có quyền phán xét hạnh kiểm của học sinh.
- **Gợi ý hình ảnh:** Biểu tượng ổ khóa bảo mật dữ liệu màu xanh ngọc (Zero Cloud Leakage) và dấu gạch chéo đỏ trên biểu tượng quét khuôn mặt khuôn mẫu.

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~1 phút)
> *"Khi làm đề tài này, một trong những điều mà nhóm chúng em trăn trở nhiều nhất chính là: **Vấn đề đạo đức công nghệ và quyền riêng tư của các bạn học sinh.**
>
> *Liệu một hệ thống camera thông minh có biến phòng thi thành một nơi bị soi xét ngột ngạt hay làm lộ dữ liệu cá nhân của các bạn không?
>
> *Câu trả lời của chúng em là: **TUYỆT ĐỐI KHÔNG**, nhờ bộ nguyên tắc '3 KHÔNG' nghiêm ngặt:
> - **Thứ nhất, KHÔNG nhận diện khuôn mặt:** Hệ thống chỉ phân tích tọa độ các khớp xương và hình dạng chiếc điện thoại. AI hoàn toàn không biết bạn là ai, tên gì, hay số báo danh bao nhiêu.
> - **Thứ hai, KHÔNG gửi dữ liệu ra Internet:** Hệ thống chạy offline 100% trên máy tính của giám thị. Không có một khung hình nào bị gửi lên đám mây, triệt tiêu hoàn toàn nguy cơ rò rỉ hình ảnh học sinh ra ngoài.
> - **Và thứ ba, KHÔNG tự động kỷ luật:** Công nghệ chỉ cung cấp lăng kính trung thực nhất để bảo vệ sự công bằng cho tất cả các bạn học sinh làm bài nghiêm túc, ngăn chặn sự gian lận và tránh mọi quyết định oan sai từ cảm quan nhất thời."*

---

### SLIDE 13: KẾT LUẬN & HƯỚNG PHÁT TRIỂN TƯƠNG LAI
- **Tiêu đề:** TỔNG KẾT DỰ ÁN & BƯỚC ĐI TIẾP THEO
- **Kết quả đạt được hôm nay:**
  - Chế tạo thành công nguyên mẫu phần mềm chạy mượt mà trên máy tính phổ thông với chi phí 0 đồng tiền bản quyền đám mây.
  - Tích hợp trọn vẹn 7 chức năng cốt lõi (từ thu nhận đa camera đến trích xuất video 15s).
- **Kế hoạch phát triển ngày mai:**
  - Mở rộng thêm tính năng phát hiện hành vi chuyền giấy nháp dưới ngăn bàn.
  - Ứng dụng mô hình không gian 3 chiều (3D Pose) để đo góc quay đầu chính xác đến từng độ.
  - Kết nối liên thông nhiều phòng thi về phòng Hội đồng thi của nhà trường.
- **Gợi ý hình ảnh:** Hình ảnh bản đồ phát triển tương lai (Roadmap) từ một phòng thi nhỏ hướng tới một kỳ thi quy mô toàn trường văn minh, hiện đại.

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~1 phút)
> *"Kính thưa Ban Giám khảo và các bạn,
>
> *Sau quá trình nghiên cứu và thực nghiệm nghiêm túc, nhóm chúng em đã hoàn thành trọn vẹn nguyên mẫu phần mềm với 7 chức năng cốt lõi. Điểm sáng lớn nhất của dự án là khả năng vận hành trơn tru ngay trên những máy tính văn phòng sẵn có trong trường học kết hợp với các camera phổ thông, giúp tiết kiệm chi phí tối đa cho ngành giáo dục.
>
> *Trong giai đoạn tiếp theo, nhóm chúng em ấp ủ dự định sẽ nâng cấp thêm thuật toán ước lượng tư thế 3D trong không gian để đo độ nghiêng đầu chính xác hơn nữa, cũng như nghiên cứu nhận diện cử chỉ chuyền phao giấy dưới gầm bàn.
>
> *Chúng em tin rằng, công nghệ chỉ thực sự có ý nghĩa khi nó phục vụ cuộc sống và mang lại sự công bằng, văn minh cho mái trường."*

---

### SLIDE 14: LỜI CẢM ƠN & PHẦN HỎI ĐÁP (Q&A)
- **Tiêu đề:** LỜI CẢM ƠN VÀ TRAO ĐỔI Ý KIẾN
- **Thông điệp:** "Khoa học bắt đầu từ những câu hỏi nhỏ — Công nghệ hoàn thiện vì sự công bằng của học đường"
- **Thông tin liên hệ & Mã nguồn dự án:** Hệ thống sẵn sàng cho phần chạy Demo trực tiếp (Live Demonstration).
- **Gợi ý hình ảnh:** Logo trường học, thông tin tác giả và mã QR liên kết tài liệu nghiên cứu.

#### 🎙️ Kịch bản thuyết trình (Thời lượng: ~30 giây)
> *"Bài thuyết trình của nhóm chúng em đến đây là kết thúc. Chúng em xin được gửi lời cảm ơn chân thành nhất tới quý thầy cô trong Ban Giám khảo đã chú ý lắng nghe và hướng dẫn chúng em trong suốt quá trình hoàn thiện đề tài.
>
> *Sau đây, chúng em rất mong nhận được những lời nhận xét, góp ý quý báu của quý thầy cô, và chúng em đã sẵn sàng cho phần chạy thử nghiệm trực tiếp (Live Demo) cũng như trả lời các câu hỏi phản biện.
>
> *Em xin trân trọng cảm ơn!"*

---

# PHẦN 3: BỘ CÂU HỎI PHẢN BIỆN DỰ PHÒNG & KỊCH BẢN TRẢ LỜI CHO HỌC SINH (Q&A DEFENSE CHEATSHEET)

Khi thuyết trình trước Ban Giám khảo hoặc các bạn học sinh, các bạn rất dễ nhận được những câu hỏi hóc búa. Dưới đây là 4 câu hỏi điển hình nhất kèm kịch bản trả lời thông minh, tự tin và khiêm tốn:

---

### ❓ Câu hỏi 1: *"Nếu phòng thi thiếu ánh sáng hoặc học sinh mặc áo khoác dày, mô hình nhận diện tư thế người que có bị sai lệch không?"*
- **🎙️ Kịch bản trả lời tự tin:**
  > *"Em xin cảm ơn câu hỏi rất thực tế của thầy/cô!
  > Dạ đúng là đối với thị giác máy tính, ánh sáng quá tối hoặc quần áo quá thùng thình sẽ làm giảm độ rõ nét của các khớp vai và khuỷu tay. Tuy nhiên, trong thuật toán của chúng em, hành vi quay đầu chủ yếu dựa vào **tam giác khuôn mặt gồm: Mũi, Hai Mắt và Hai Tai**. Thí sinh khi làm bài thi thường không che kín mặt, nên các điểm mốc này vẫn được mô hình YOLO Pose bắt rất nhạy.
  > Đồng thời, hệ thống có thanh trượt cho phép thầy cô **điều chỉnh độ nhạy AI** ngay trên màn hình để thích ứng với ánh sáng phòng thi hôm đó mà không cần phải khởi động lại phần mềm ạ."*

---

### ❓ Câu hỏi 2: *"Tại sao nhóm không dùng AI để nhận diện luôn khuôn mặt và số báo danh của thí sinh vi phạm cho tiện?"*
- **🎙️ Kịch bản trả lời thông minh:**
  > *"Dạ đây là một quyết định thiết kế mà nhóm chúng em đã cân nhắc rất kỹ lưỡng ngay từ đầu ạ!
  > Thứ nhất, về mặt **Quyền riêng tư học đường**: Việc quét khuôn mặt (Face Recognition) thu thập dữ liệu sinh trắc học rất nhạy cảm của học sinh, dễ gây tranh cãi về mặt pháp lý và bảo mật.
  > Thứ hai, về mặt **Hiệu năng**: Quét khuôn mặt 30 thí sinh liên tục đòi hỏi máy tính phải có card đồ họa GPU cực kỳ đắt tiền.
  > Trong khi đó, mục tiêu của dự án là tạo ra một phần mềm **nhẹ, chạy được trên máy tính bình thường của trường** và **tập trung duy nhất vào việc cung cấp đoạn video bằng chứng 15 giây**. Khi xem video, thầy cô giám thị nhìn số bàn là biết ngay bạn học sinh nào, nên việc nhận diện khuôn mặt tự động là không cần thiết và tốn kém tài nguyên ạ!"*

---

### ❓ Câu hỏi 3: *"Nếu bạn học sinh chỉ quay sang mượn cục tẩy hay mượn cây thước kẻ thì hệ thống có bắt oan không?"*
- **🎙️ Kịch bản trả lời nhân văn:**
  > *"Dạ thưa thầy cô, quy chế thi hiện hành quy định thí sinh không được phép trao đổi đồ dùng trong giờ làm bài.
  > Tuy nhiên, hệ thống của chúng em không bao giờ tự động kết tội bạn học sinh đó. Khi bạn quay sang mượn tẩy quá 1,25 giây, hệ thống sẽ cắt lại một đoạn clip 15 giây.
  > Thầy cô giám thị mở clip lên xem, thấy bạn chỉ mượn cục tẩy chứ không phải xem bài, thầy cô chỉ việc bấm nút **'Bỏ qua' (Dismiss)** và có thể đi xuống bàn nhắc nhở nhẹ nhàng. Video bằng chứng sinh ra là để thầy cô có cái nhìn khách quan nhất, tránh việc nghi ngờ oan cho học sinh ạ!"*

---

### ❓ Câu hỏi 4: *"Trong báo cáo thấy nhóm ghi 'Nghiệm thu đồng thời hai camera vật lý đang chờ phần cứng' (Hardware Acceptance Pending), điều này nghĩa là sao?"*
- **🎙️ Kịch bản trả lời trung thực & khoa học:**
  > *"Dạ, nhóm chúng em muốn giữ thái độ trung thực khoa học tuyệt đối trong báo cáo:
  > Toàn bộ logic phần mềm xử lý đa camera (Dual-Camera Pipeline) và bộ lập lịch luân chuyển Fair Scheduler đã được kiểm thử hoàn tất 100% bằng 01 webcam vật lý kết hợp các luồng video mô phỏng thực tế.
  > Để chuẩn bị cho vòng thi chính thức, nhóm chúng em đã đặt mua thêm 2 chiếc webcam chuyên dụng ngoài (EYD PC02). Ngay khi nhận được thiết bị trong vài ngày tới, chúng em sẽ cắm vào cổng USB để hoàn thiện bước đo đạc phần cứng cuối cùng. Việc ghi rõ trạng thái này giúp hồ sơ nghiên cứu của chúng em luôn minh bạch và chuẩn xác nhất ạ!"*
