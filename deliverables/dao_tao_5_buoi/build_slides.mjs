import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "C:/Users/Administrator/Documents/Codespace/aiexam";
const courseDir = path.join(workspaceDir, "deliverables/dao_tao_5_buoi");
const buildRoot = path.join(courseDir, ".slide-build");
const outputDir = path.join(courseDir, "slides");
const skillDir = "C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations";
const runtimePython = "C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href);

const W = 1280;
const H = 720;
const font = "Arial";
const C = {
  bg: "#09090B", surface: "#18181B", line: "#3F3F46", text: "#F4F4F5",
  muted: "#A1A1AA", green: "#10B981", amber: "#F59E0B", rose: "#F43F5E", white: "#FFFFFF"
};

await fs.mkdir(buildRoot, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

function addText(slide, text, x, y, w, h, size = 24, color = C.text, bold = false, align = "left") {
  const s = slide.shapes.add({ geometry: "textbox", position: { left: x, top: y, width: w, height: h }, fill: "none", line: { fill: "none", width: 0 } });
  s.text = text;
  s.text.style = { typeface: font, fontSize: size, color, bold, alignment: align, verticalAlignment: "middle", autoFit: "shrinkText" };
  return s;
}

function addRect(slide, x, y, w, h, fill = C.surface, stroke = C.line, radius = "roundRect") {
  return slide.shapes.add({ geometry: radius, position: { left: x, top: y, width: w, height: h }, fill, line: { fill: stroke, width: 1 } });
}

function baseSlide(p, title, number) {
  const s = p.slides.add();
  s.background.fill = C.bg;
  addText(s, title, 64, 34, 1100, 58, 34, C.text, true);
  addText(s, String(number).padStart(2, "0"), 1180, 40, 48, 34, 14, C.muted, true, "right");
  s.shapes.add({ geometry: "line", position: { left: 64, top: 104, width: 1160, height: 0 }, fill: "none", line: { fill: C.line, width: 1 } });
  return s;
}

function cover(p, deck) {
  const s = p.slides.add();
  s.background.fill = C.bg;
  addText(s, `BUỔI ${deck.n}`, 70, 64, 240, 38, 15, deck.accent, true);
  addText(s, deck.title, 70, 136, 980, 160, 48, C.text, true);
  addText(s, deck.subtitle, 72, 316, 850, 86, 23, C.muted, false);
  s.shapes.add({ geometry: "line", position: { left: 72, top: 454, width: 850, height: 0 }, fill: "none", line: { fill: deck.accent, width: 4 } });
  addText(s, deck.output, 72, 478, 880, 100, 21, C.text, false);
  addText(s, "AI EXAM CONTROL · HỌC QUA ARTIFACT CỦA PROJECT", 72, 642, 800, 26, 12, C.muted, true);
  s.speakerNotes.textFrame.setText(`Mục tiêu buổi học: ${deck.output}\nNguồn nội bộ: deliverables/dao_tao_5_buoi/01_GIAO_AN.md; 11_NGUON_VA_GIOI_HAN.md.`);
}

function goals(p, deck) {
  const s = baseSlide(p, "Câu hỏi dẫn đường", 2);
  addText(s, deck.question, 82, 144, 1110, 118, 34, C.white, true);
  addText(s, "Cuối buổi, học viên tự làm được", 82, 300, 500, 32, 18, deck.accent, true);
  deck.goals.forEach((g, i) => {
    addText(s, String(i + 1), 84, 356 + i * 74, 42, 42, 18, C.bg, true, "center").fill = deck.accent;
    addText(s, g, 148, 344 + i * 74, 990, 64, 22, C.text, false);
  });
  s.speakerNotes.textFrame.setText("Yêu cầu học viên trả lời câu dẫn đường trước khi dạy. Lặp lại cuối buổi để nhìn sự thay đổi trong cách giải thích.");
}

function chain(p, deck) {
  const s = baseSlide(p, deck.chainTitle, 3);
  const items = deck.chain;
  const gap = 16;
  const boxW = Math.floor((1120 - gap * (items.length - 1)) / items.length);
  items.forEach((item, i) => {
    const x = 74 + i * (boxW + gap);
    addRect(s, x, 210, boxW, 176, i === deck.chainFocus ? deck.accent : C.surface, i === deck.chainFocus ? deck.accent : C.line, "roundRect");
    addText(s, String(i + 1), x + 16, 224, 32, 28, 14, i === deck.chainFocus ? C.bg : deck.accent, true);
    addText(s, item[0], x + 16, 260, boxW - 32, 52, 22, i === deck.chainFocus ? C.bg : C.text, true);
    addText(s, item[1], x + 16, 316, boxW - 32, 56, 16, i === deck.chainFocus ? "#052E24" : C.muted, false);
  });
  addText(s, deck.chainNote, 90, 446, 1080, 92, 25, C.text, false, "center");
  s.speakerNotes.textFrame.setText(deck.notes3);
}

async function evidence(p, deck) {
  const s = baseSlide(p, deck.evidenceTitle, 4);
  if (deck.image) {
    addText(s, deck.evidenceBody, 72, 144, 505, 410, 20, C.text, false);
    const img = await fs.readFile(path.join(workspaceDir, deck.image));
    s.images.add({ blob: new Uint8Array(img), contentType: "image/png", alt: deck.imageAlt, fit: "contain", position: { left: 610, top: 140, width: 600, height: 445 } });
  } else {
    addText(s, deck.evidenceBody, 80, 140, 1120, 420, 22, C.text, false);
  }
  addText(s, deck.evidenceFooter, 78, 604, 1110, 44, 16, deck.accent, true);
  s.speakerNotes.textFrame.setText(deck.evidenceNotes);
}

function lab(p, deck) {
  const s = baseSlide(p, "Thực hành trong lớp", 5);
  addText(s, deck.labPrompt, 78, 136, 1120, 72, 27, C.text, true);
  deck.labSteps.forEach((step, i) => {
    const y = 238 + i * 86;
    addText(s, String(i + 1), 82, y, 42, 42, 18, C.bg, true, "center").fill = deck.accent;
    addText(s, step[0], 148, y - 6, 350, 40, 20, C.text, true);
    addText(s, step[1], 508, y - 6, 650, 58, 18, C.muted, false);
  });
  addText(s, `Sản phẩm nộp: ${deck.labOutput}`, 82, 614, 1090, 34, 17, deck.accent, true);
  s.speakerNotes.textFrame.setText(`Dùng phiếu thực hành 12_PHIEU_THUC_HANH.md. Không thao tác trên model, DB hoặc bằng chứng gốc. ${deck.labNotes}`);
}

function misconceptions(p, deck) {
  const s = baseSlide(p, "Ba nhầm lẫn cần sửa", 6);
  deck.misconceptions.forEach((m, i) => {
    const y = 148 + i * 156;
    addText(s, `NHẦM ${i + 1}`, 82, y, 110, 30, 14, C.rose, true);
    addText(s, m[0], 210, y - 8, 930, 45, 23, C.text, true);
    addText(s, m[1], 210, y + 46, 930, 66, 19, C.muted, false);
  });
  s.speakerNotes.textFrame.setText("Cho học viên tự sửa câu sai trước khi hiện cách diễn đạt đúng. Không biến slide thành đáp án học thuộc.");
}

function exitTicket(p, deck) {
  const s = baseSlide(p, "Kiểm tra cuối buổi", 7);
  addText(s, "Không nhìn tài liệu. Giải thích bằng lời của em.", 78, 136, 900, 48, 25, deck.accent, true);
  deck.exit.forEach((q, i) => {
    addText(s, `${i + 1}.`, 84, 222 + i * 82, 40, 44, 20, C.muted, true);
    addText(s, q, 132, 212 + i * 82, 1030, 64, 21, C.text, false);
  });
  addText(s, `Bài nộp: ${deck.labOutput}`, 80, 636, 1080, 30, 15, C.muted, true);
  s.speakerNotes.textFrame.setText("Chấm theo rubric trong 07_KIEM_TRA.md. Một đáp án đúng nhưng không giải thích được ví dụ mới chỉ đạt tối đa một nửa điểm.");
}

const decks = [
  {
    n: 1, file: "BUOI_1_DU_LIEU_VA_NHAN.pptx", accent: C.green,
    title: "Dữ liệu, nhãn và cách máy học từ ví dụ",
    subtitle: "Từ ảnh thô đến dataset có thể dùng để học và đánh giá",
    output: "Tạo một data card nhỏ và đề xuất cách chia train, validation, test tránh rò rỉ theo video hoặc phiên.",
    question: "Nếu máy chưa biết “điện thoại” là gì, ta phải đưa những ví dụ nào và mô tả đáp án ra sao?",
    goals: ["Phân biệt AI, ML, DL và Computer Vision", "Phân biệt sample, label, metadata và hard negative", "Giải thích train, validation, test và data leakage"],
    chainTitle: "Một dataset đáng tin có nhiều lớp", chainFocus: 2,
    chain: [["Thu thập", "Nguồn và quyền dùng"], ["Gán nhãn", "Đáp án nhất quán"], ["Metadata", "Điều kiện của mẫu"], ["Chia tập", "Độc lập theo phiên"], ["Đánh giá", "Đúng protocol"]],
    chainNote: "Nhiều ảnh không bù được nhãn sai hoặc cách chia tập bị rò rỉ.",
    notes3: "Dùng một chuỗi frame gần nhau để minh họa leakage. Metadata không thay thế label.",
    evidenceTitle: "Protocol dữ liệu của project",
    evidenceBody: "PHONE DATASET\n\nPositive: có ít nhất một box class 0\nNegative: file label rỗng\nHard negative: calculator, ví, hộp bút...\nMetadata: session, camera, lighting, occlusion, distance, provenance\n\nHISTORICAL LINEAGE\n2.961 ảnh và 3.706 phone boxes\nUntouched holdout: còn mở",
    evidenceFooter: "Có tập mang tên test chưa đủ chứng minh một holdout độc lập.",
    evidenceNotes: "Nguồn: datasets/README.md; reports/evidence/training_lineage/lineage_manifest.json; REPORT_GAP_REGISTER.md. Các con số là artifact lịch sử.",
    labPrompt: "Thiết kế một bộ dữ liệu nhỏ cho detector điện thoại",
    labSteps: [["Phân loại", "Chọn positive, negative và hard negative"], ["Mô tả", "Ghi nguồn, quyền dùng, ánh sáng, che khuất, khoảng cách"], ["Chia tập", "Tách theo video/session/camera hợp lý"], ["Kiểm tra", "Tìm khả năng trùng và gần trùng"]],
    labOutput: "data card + split plan", labNotes: "Không dùng hình ảnh có mặt hoặc thông tin nhận dạng khi chưa có sự đồng ý.",
    misconceptions: [["Dữ liệu càng nhiều thì tự động càng tốt", "Chất lượng nhãn, độ đại diện và cách chia tập quyết định giá trị của số lượng."], ["Ảnh không có phone thì bỏ đi", "Negative và hard negative giúp model học khi nào không nên báo."], ["Test là dữ liệu dùng để chỉnh đến khi đẹp", "Một tập đã tham gia lựa chọn không còn là untouched holdout."]],
    exit: ["Label khác metadata ở điểm nào?", "Vì sao không chia ngẫu nhiên các frame gần nhau?", "Hard negative giúp kiểm tra điều gì?"]
  },
  {
    n: 2, file: "BUOI_2_COMPUTER_VISION_VA_DETECTION.pptx", accent: C.amber,
    title: "Computer Vision và object detection",
    subtitle: "Pixel, bounding box, confidence và cách ghép prediction với nhãn",
    output: "Gán nhãn YOLO hợp lệ, tính IoU và đếm TP, FP, FN theo một operating point đã cho.",
    question: "Một ảnh biến thành con số thế nào, và model biết một bounding box là đúng bằng cách nào?",
    goals: ["Phân biệt classification với detection", "Đọc và tạo nhãn YOLO chuẩn hóa", "Giải thích confidence, IoU, threshold và NMS"],
    chainTitle: "Từ pixel đến detection", chainFocus: 3,
    chain: [["Ảnh", "Pixel và channel"], ["Resize", "Giữ hoặc mất chi tiết"], ["Model", "Dự đoán box và điểm"], ["Ngưỡng", "Giữ prediction"], ["NMS", "Loại box trùng"]],
    chainNote: "Camera FPS, inference FPS và số kết quả mỗi giây là ba đại lượng cần gọi đúng.",
    notes3: "Phóng to một ảnh để chỉ pixel. Dùng vật nhỏ ở xa để giải thích tác động độ phân giải.",
    evidenceTitle: "Detector điện thoại trong giao diện",
    evidenceBody: "Classification trả một lớp cho toàn ảnh.\n\nDetection trả class, bounding box và confidence.\n\nIoU đo độ chồng khớp giữa prediction và ground truth.\n\nThreshold chọn operating point. NMS giảm box trùng.",
    image: "deliverables/ha_noi/screenshots/live_monitor_multi_cam.png", imageAlt: "Giao diện giám sát đa camera của project",
    evidenceFooter: "Confidence không phải xác suất một người đang gian lận.",
    evidenceNotes: "Ảnh nội bộ: deliverables/ha_noi/screenshots/live_monitor_multi_cam.png. Khái niệm đánh giá đối chiếu scripts/evaluation/evaluate_phone.py.",
    labPrompt: "Gán nhãn, review box và chấm tám prediction giả định",
    labSteps: [["Vẽ box", "Bao sát điện thoại theo guideline"], ["Chuẩn hóa", "Đổi sang class, tâm, rộng, cao"], ["Review", "So nhãn giữa hai người"], ["Đánh giá", "Áp confidence và IoU để đếm TP, FP, FN"]],
    labOutput: "10 nhãn mẫu + phiếu kiểm nhãn", labNotes: "Ảnh negative phải có file label rỗng theo protocol project.",
    misconceptions: [["Box rộng hơn sẽ an toàn hơn", "Box dư nền làm nhãn kém nhất quán và giảm chất lượng định vị."], ["Confidence 0,9 nghĩa là đúng 90%", "Confidence là điểm dự đoán; độ đúng cần đo trên dữ liệu có nhãn."], ["Hạ threshold luôn tốt", "Hạ ngưỡng thường giữ thêm cả true positive và false positive."]],
    exit: ["Detection thêm thông tin gì so với classification?", "IoU đo gì và không đo gì?", "NMS giải quyết vấn đề nào?"]
  },
  {
    n: 3, file: "BUOI_3_POSE_TRACKING_THOI_GIAN.pptx", accent: C.green,
    title: "Pose, tracking và hành vi theo thời gian",
    subtitle: "Từ keypoint của từng frame đến một sự kiện có start và end",
    output: "Vẽ đúng hai pipeline điện thoại/quay đầu và gán nhãn một sự kiện theo khoảng thời gian.",
    question: "Một tư thế trong một frame có đủ để gọi là hành vi quay đầu không?",
    goals: ["Giải thích keypoint và heuristic hình học", "Hiểu track ID là mã tạm thời", "Phân biệt frame prediction với event theo thời gian"],
    chainTitle: "Pipeline quay đầu là hệ lai", chainFocus: 2,
    chain: [["Pose model", "Dự đoán keypoint"], ["Hình học", "Tạo điểm nghi vấn"], ["Tracking", "Nối người qua frame"], ["Temporal rule", "Kiểm tra liên tục"], ["Human", "Duyệt bối cảnh"]],
    chainNote: "Phần learned tạo keypoint. Phần heuristic và state machine tạo cảnh báo nghiệp vụ.",
    notes3: "Yêu cầu học viên tô màu phần learned, rule-based và human decision bằng ba màu khác nhau.",
    evidenceTitle: "Heuristic và gap guard của project",
    evidenceBody: "Mặc định trong temporal tracker:\n\nAlert duration: 1,25 giây\nMinimum samples: 3\nMaximum gap: 0,75 giây\n\nNếu gap vượt mức, chuỗi nghi vấn reset. Track ID gắn với source/session, không phải danh tính.",
    image: "deliverables/ha_noi/screenshots/pose_heuristic_diagram.png", imageAlt: "Sơ đồ heuristic pose của project",
    evidenceFooter: "`turn_deg` không được trình bày như góc đầu 3D đã hiệu chuẩn.",
    evidenceNotes: "Nguồn: backend/services/temporal_tracker.py; datasets/README.md; ảnh nội bộ pose_heuristic_diagram.png.",
    labPrompt: "Gán nhãn interval và mô phỏng state machine bằng timeline",
    labSteps: [["Đặt mốc", "Ghi start, end, direction, target anonymous"], ["Theo dõi", "Nối quan sát theo source, session, track"], ["Kiểm gap", "Reset khi khoảng cách vượt 0,75 s"], ["Phân loại", "Green, yellow hoặc red theo điều kiện"]],
    labOutput: "event labels + sơ đồ hai pipeline", labNotes: "Các timeline trong bài là giả định, không phải dữ liệu đo mới.",
    misconceptions: [["Keypoint đã là kết luận gian lận", "Keypoint chỉ là output hình học; cần quy tắc và người duyệt."], ["Track 4 là thí sinh số 4", "ID có thể đổi khi mất dấu, đổi nguồn hoặc reset phiên."], ["Hai frame cách nhau 1,25 s đủ tạo đỏ", "Chuỗi còn cần tính liên tục và số quan sát tối thiểu."]],
    exit: ["Phần nào học từ dữ liệu, phần nào là heuristic?", "Khi nào track ID có thể đổi?", "Vì sao event label cần start và end?"]
  },
  {
    n: 4, file: "BUOI_4_DEEP_LEARNING_FINE_TUNE.pptx", accent: C.amber,
    title: "Deep Learning, transfer learning và fine-tune",
    subtitle: "Đọc một run huấn luyện lịch sử thay vì học thuộc thuật ngữ",
    output: "Đọc `args.yaml` và `results.csv`, giải thích checkpoint, resume, loss, metric và các kết luận chưa đủ bằng chứng.",
    question: "Fine-tune đã làm gì với một model có sẵn, và nhìn log nào để biết việc học đang diễn ra?",
    goals: ["Kể đúng vòng prediction, loss, gradient, update", "Phân biệt pretrained, fine-tune, checkpoint và inference", "Đọc hyperparameter cùng dấu hiệu overfit"],
    chainTitle: "Vòng lặp training", chainFocus: 3,
    chain: [["Batch", "Input và label"], ["Forward", "Model dự đoán"], ["Loss", "So với ground truth"], ["Gradient", "Hướng điều chỉnh"], ["Update", "Đổi weights"]],
    chainNote: "Inference dừng ở prediction. Fine-tune tiếp tục tính loss và cập nhật weights.",
    notes3: "Dùng ví dụ một batch nhỏ. Không dạy chi tiết đạo hàm nếu học viên chưa có nền toán.",
    evidenceTitle: "Run lịch sử của detector điện thoại",
    evidenceBody: "task: detect · mode: train\nepochs: 60 · batch: 6 · imgsz: 960\noptimizer: auto · seed: 0\nresume: last.pt · close_mosaic: 10\n\nLog có box loss, cls loss, DFL loss, precision, recall, mAP.\nTime reset trước epoch 6 là dấu vết resume.\n\nInitial pretrained checkpoint: UNRESOLVED\nBest checkpoint source epoch: UNRESOLVED",
    evidenceFooter: "Epoch có mAP50 cao nhất không tự chứng minh đó là epoch sinh checkpoint triển khai.",
    evidenceNotes: "Nguồn: reports/evidence/training_lineage/args.yaml, results.csv, lineage_manifest.json. Artifact chỉ phản ánh run lịch sử.",
    labPrompt: "Điền phiếu đọc run và chẩn đoán ba đường cong giả định",
    labSteps: [["Đọc config", "Task, model, epoch, batch, image size, optimizer"], ["Đọc log", "Loss và metric theo epoch"], ["Tìm resume", "Đối chiếu args và time reset"], ["Đặt giới hạn", "Ghi rõ fact, inference và unresolved"]],
    labOutput: "phiếu đọc fine-tune run", labNotes: "Không chạy lại training trong khóa chính và không truy cập thư mục model.",
    misconceptions: [["Mở webcam là fine-tune", "Đó là inference vì weights không được cập nhật."], ["Loss giảm nghĩa thực địa chắc chắn tốt", "Cần validation/test đại diện và phân tích lỗi."], ["Augmentation tạo đủ mọi điều kiện thật", "Biến đổi ảnh không thay thế dữ liệu mục tiêu được thu đúng cách."]],
    exit: ["Fine-tune khác inference ở đâu?", "Resume từ last.pt chứng minh điều gì?", "Loss và metric có vai trò khác nhau thế nào?"]
  },
  {
    n: 5, file: "BUOI_5_DANH_GIA_VA_TRIEN_KHAI.pptx", accent: C.green,
    title: "Đánh giá, inference và ghép thành sản phẩm",
    subtitle: "Từ checkpoint đến cảnh báo có bằng chứng và người duyệt",
    output: "Tính metric ở một operating point, đọc giới hạn benchmark và giải thích đầy đủ pipeline triển khai.",
    question: "Từ model có metric đến hệ thống dùng được còn những lớp nào, và ta được phép kết luận gì?",
    goals: ["Tính precision, recall, F1 từ TP, FP, FN", "Đọc đúng AP/mAP và operating threshold", "Phân biệt lỗi data, model và deployment"],
    chainTitle: "Inference pipeline đầy đủ", chainFocus: 4,
    chain: [["Nguồn", "Camera hoặc video"], ["Model", "Detection và pose"], ["Logic", "Track và thời gian"], ["Evidence", "RingBuffer và DB"], ["Review", "UI và giám thị"]],
    chainNote: "Một metric của model không đại diện cho mọi lỗi của hệ thống triển khai.",
    notes3: "Cho mỗi học viên chọn một lớp và nêu đầu vào, đầu ra, một lỗi có thể xảy ra.",
    evidenceTitle: "Kiến trúc và benchmark lịch sử",
    evidenceBody: "Benchmark 125,1 giây:\nCamera/server nhận khoảng 15,58 FPS\n354 kết quả, khoảng 2,83 kết quả/s\n85,3% frame chờ bị supersede\nMean inference latency 360,4 ms\n\nĐây là phép đo hiệu năng của một cấu hình, không phải accuracy.",
    image: "deliverables/ha_noi/screenshots/architecture_pipeline_diagram.png", imageAlt: "Sơ đồ pipeline kiến trúc AI Exam Control",
    evidenceFooter: "Validation mAP và benchmark latency trả lời hai câu hỏi khác nhau.",
    evidenceNotes: "Nguồn: reports/evidence/report_runtime/e2e_benchmark_result.json; architecture_pipeline_diagram.png; reports/evidence/training_lineage/lineage_manifest.json.",
    labPrompt: "Từ 20 prediction giả định đến một báo cáo đánh giá mini",
    labSteps: [["Khóa phiên bản", "Checkpoint, dataset, threshold và protocol"], ["Tính metric", "TP, FP, FN, precision, recall, F1"], ["Phân nhóm", "Occlusion, distance, lighting hoặc distractor"], ["Kết luận", "Điều đã đo, chưa đo và thí nghiệm tiếp theo"]],
    labOutput: "báo cáo đánh giá mini + giải thích pipeline 2 phút", labNotes: "Phần rehearsal giám khảo chỉ dùng để kiểm tra hiểu, không thay thế bài tập metric.",
    misconceptions: [["mAP50 là xác suất một cảnh báo đúng", "mAP tóm tắt đánh giá detection theo protocol và tập dữ liệu cụ thể."], ["Camera 15 FPS nghĩa AI xử lý 15 FPS", "Capture rate và inference result rate là hai đại lượng khác nhau."], ["Test phần mềm pass chứng minh model tốt ngoài thực tế", "Unit/integration test và model evaluation đo những thuộc tính khác nhau."]],
    exit: ["Khi nào ưu tiên precision, khi nào ưu tiên recall?", "Một model tốt vẫn có thể thất bại ở lớp deployment nào?", "Em còn thiếu bằng chứng gì để nói về phòng thi thật?"]
  }
];

for (const deck of decks) {
  const p = Presentation.create({ slideSize: { width: W, height: H } });
  cover(p, deck);
  goals(p, deck);
  chain(p, deck);
  await evidence(p, deck);
  lab(p, deck);
  misconceptions(p, deck);
  exitTicket(p, deck);

  const deckBuildDir = path.join(buildRoot, `buoi_${deck.n}`);
  await fs.mkdir(deckBuildDir, { recursive: true });
  const candidatePath = path.join(deckBuildDir, "candidate.pptx");
  const finalPath = path.join(outputDir, deck.file);
  await (await PresentationFile.exportPptx(p)).save(candidatePath);
  await finalizePresentation({
    workspaceDir,
    candidatePath,
    finalPath,
    explicitTotalSlideCount: 7,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [],
    fontPolicy: { basis: "design", families: [font] },
    pythonExecutable: runtimePython,
    integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
    layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
    layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-heading-fit"],
    verifyArtifactToolImport: true,
    receiptPath: path.join(deckBuildDir, "validation.json")
  });
}

console.log(JSON.stringify({ outputs: decks.map(d => path.join(outputDir, d.file)) }, null, 2));
