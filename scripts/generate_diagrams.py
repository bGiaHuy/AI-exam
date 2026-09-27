import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

diagram_dir = r"deliverables\ha_noi\screenshots"
os.makedirs(diagram_dir, exist_ok=True)

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#27272a'
plt.rcParams['axes.linewidth'] = 1.0

# -------------------------------------------------------------
# 1. Pipeline Architecture Diagram (Hai luong xu ly doc lap)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
ax.set_facecolor('#ffffff')
ax.axis('off')

# Title
ax.text(5, 4.7, 'KIẾN TRÚC ĐIỀU PHỐI HAI LUỒNG XỬ LÝ ĐỘC LẬP (DUAL-STREAM PIPELINE)', 
        fontsize=11, fontweight='bold', ha='center', color='#09090b')

# Box Camera Input
box_cam = patches.FancyBboxPatch((0.5, 2.0), 1.8, 1.4, boxstyle="round,pad=0.1", fc='#f4f4f5', ec='#27272a', lw=1.5)
ax.add_patch(box_cam)
ax.text(1.4, 2.8, 'NGUỒN CAMERA\n(Webcam / USB / RTSP)', ha='center', va='center', fontsize=9, fontweight='bold', color='#18181b')
ax.text(1.4, 2.3, '15 FPS (720p/1080p)', ha='center', va='center', fontsize=8, color='#52525b')

# Stream 1: Recording / RingBuffer
box_ring = patches.FancyBboxPatch((3.5, 2.8), 2.8, 1.4, boxstyle="round,pad=0.1", fc='#ecfdf5', ec='#059669', lw=1.5)
ax.add_patch(box_ring)
ax.text(4.9, 3.6, 'LUỒNG GHI HÌNH BẰNG CHỨNG', ha='center', va='center', fontsize=9, fontweight='bold', color='#065f46')
ax.text(4.9, 3.1, 'Bộ đệm vòng Circular RingBuffer\n(Giữ toàn bộ ~15 FPS, thời gian thực)', ha='center', va='center', fontsize=8, color='#047857')

# Stream 2: AI Inference Worker
box_ai = patches.FancyBboxPatch((3.5, 0.8), 2.8, 1.4, boxstyle="round,pad=0.1", fc='#eff6ff', ec='#2563eb', lw=1.5)
ax.add_patch(box_ai)
ax.text(4.9, 1.6, 'LUỒNG SUY LUẬN AI', ha='center', va='center', fontsize=9, fontweight='bold', color='#1e40af')
ax.text(4.9, 1.1, 'Bộ đệm 1 phần tử (Single-Slot)\nChỉ giữ khung hình mới nhất', ha='center', va='center', fontsize=8, color='#1d4ed8')

# Box Evidence Trigger & MP4 Resampler
box_evid = patches.FancyBboxPatch((7.2, 2.8), 2.4, 1.4, boxstyle="round,pad=0.1", fc='#fef2f2', ec='#dc2626', lw=1.5)
ax.add_patch(box_evid)
ax.text(8.4, 3.6, 'XUẤT CLIP MP4 (1.0x)', ha='center', va='center', fontsize=9, fontweight='bold', color='#991b1b')
ax.text(8.4, 3.1, 'Pre 5s + Post 10s = 15s\nTái lấy mẫu lưới thời gian', ha='center', va='center', fontsize=8, color='#b91c1c')

# Box DB & Dashboard
box_db = patches.FancyBboxPatch((7.2, 0.8), 2.4, 1.4, boxstyle="round,pad=0.1", fc='#faf5ff', ec='#7c3aed', lw=1.5)
ax.add_patch(box_db)
ax.text(8.4, 1.6, 'GIÁM THỊ & CƠ SỞ DỮ LIỆU', ha='center', va='center', fontsize=9, fontweight='bold', color='#5b21b6')
ax.text(8.4, 1.1, 'SQLite WAL (cheating_system.db)\nReact 19 Proctor Dashboard', ha='center', va='center', fontsize=8, color='#6d28d9')

# Connectors
arrow_kw = dict(arrowstyle="->", lw=1.5, color='#27272a')
# Cam to Ring
ax.annotate('', xy=(3.5, 3.5), xytext=(2.3, 2.9), arrowprops=arrow_kw)
ax.text(2.8, 3.4, '15 FPS', fontsize=8, color='#059669', fontweight='bold')
# Cam to AI
ax.annotate('', xy=(3.5, 1.5), xytext=(2.3, 2.5), arrowprops=arrow_kw)
ax.text(2.7, 1.8, 'Khung mới', fontsize=8, color='#2563eb', fontweight='bold')

# AI Trigger to Ring
ax.annotate('', xy=(7.2, 3.3), xytext=(6.3, 1.7), 
            arrowprops=dict(arrowstyle="->", lw=1.5, color='#dc2626', linestyle='dashed'))
ax.text(6.8, 2.4, 'Kích hoạt cờ Đỏ', fontsize=8, color='#dc2626', fontweight='bold', rotation=30)

# Ring to Evidence MP4
ax.annotate('', xy=(7.2, 3.5), xytext=(6.3, 3.5), arrowprops=arrow_kw)

# Evidence MP4 to DB/Dashboard
ax.annotate('', xy=(8.4, 2.2), xytext=(8.4, 2.8), arrowprops=arrow_kw)
ax.text(8.5, 2.5, 'Lưu sự cố', fontsize=8, color='#27272a')

ax.set_xlim(0, 10)
ax.set_ylim(0, 5)
plt.tight_layout()
p1 = os.path.join(diagram_dir, 'architecture_pipeline_diagram.png')
plt.savefig(p1, bbox_inches='tight', dpi=300)
plt.close()
print(f"Generated {p1}")

# -------------------------------------------------------------
# 2. RingBuffer Time Window Diagram (Cua so thoi gian pre/post)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 3.5), dpi=300)
ax.set_facecolor('#ffffff')
ax.axis('off')

ax.text(5, 3.2, 'CƠ CHẾ TRÍCH XUẤT CỬA SỔ THỜI GIAN VIDEO BẰNG CHỨNG (TIME-BASED RINGBUFFER)', 
        fontsize=11, fontweight='bold', ha='center', color='#09090b')

# Time axis line
ax.annotate('', xy=(9.5, 1.5), xytext=(0.5, 1.5), 
            arrowprops=dict(arrowstyle="->", lw=2.0, color='#3f3f46'))
ax.text(9.5, 1.2, 'Trục thời gian $t$ (giây)', fontsize=8, color='#52525b', ha='right')

# T_trigger
ax.plot([4.0, 4.0], [0.8, 2.2], color='#dc2626', lw=2.0, linestyle='--')
ax.plot(4.0, 1.5, marker='o', markersize=8, color='#dc2626')
ax.text(4.0, 2.3, 'Mốc vi phạm kích hoạt cờ Đỏ ($t_{\\mathrm{event}}$)\n(Điện thoại / Quay đầu $\\geq$ 1,25 giây)', 
        ha='center', fontsize=8.5, fontweight='bold', color='#dc2626')

# Pre-roll box
box_pre = patches.Rectangle((1.5, 1.0), 2.5, 1.0, fc='#fed7aa', ec='#ea580c', lw=1.2, alpha=0.8)
ax.add_patch(box_pre)
ax.text(2.75, 1.5, 'PRE-ROLL\n(-5,0 giây)', ha='center', va='center', fontsize=9, fontweight='bold', color='#9a3412')

# Post-roll box
box_post = patches.Rectangle((4.0, 1.0), 4.5, 1.0, fc='#bbf7d0', ec='#16a34a', lw=1.2, alpha=0.8)
ax.add_patch(box_post)
ax.text(6.25, 1.5, 'POST-ROLL\n(+10,0 giây)', ha='center', va='center', fontsize=9, fontweight='bold', color='#166534')

# Total clip summary
ax.annotate('', xy=(8.5, 0.6), xytext=(1.5, 0.6), 
            arrowprops=dict(arrowstyle="<->", lw=1.5, color='#18181b'))
ax.text(5.0, 0.35, 'Tổng thời lượng clip bằng chứng: ~15,0 giây (Tốc độ phát chuẩn 1.0x)', 
        ha='center', fontsize=9, fontweight='bold', color='#18181b')

ax.set_xlim(0, 10)
ax.set_ylim(0, 3.5)
plt.tight_layout()
p2 = os.path.join(diagram_dir, 'ring_buffer_time_window.png')
plt.savefig(p2, bbox_inches='tight', dpi=300)
plt.close()
print(f"Generated {p2}")

# -------------------------------------------------------------
# 3. Pose Keypoints Heuristic Diagram (17 diem khung xuong COCO)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
ax.set_facecolor('#ffffff')
ax.axis('off')

ax.text(4, 4.2, 'MÔ HÌNH 17 ĐIỂM KHUNG XƯƠNG (YOLO11M-POSE) VÀ HEURISTIC QUAY ĐẦU', 
        fontsize=10.5, fontweight='bold', ha='center', color='#09090b')

# Draw head & shoulders skeleton
pts = {
    'Nose': (3.0, 3.2),
    'L_Eye': (2.7, 3.4), 'R_Eye': (3.3, 3.4),
    'L_Ear': (2.3, 3.3), 'R_Ear': (3.7, 3.3),
    'L_Shoulder': (1.8, 2.0), 'R_Shoulder': (4.2, 2.0),
    'L_Elbow': (1.4, 1.2), 'R_Elbow': (4.6, 1.2),
    'L_Wrist': (1.2, 0.5), 'R_Wrist': (4.8, 0.5),
}

# Connect lines
connections = [
    ('L_Ear', 'L_Eye'), ('L_Eye', 'Nose'), ('Nose', 'R_Eye'), ('R_Eye', 'R_Ear'),
    ('L_Shoulder', 'R_Shoulder'), ('L_Shoulder', 'L_Elbow'), ('L_Elbow', 'L_Wrist'),
    ('R_Shoulder', 'R_Elbow'), ('R_Elbow', 'R_Wrist')
]

for p1_name, p2_name in connections:
    p1 = pts[p1_name]
    p2 = pts[p2_name]
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#3b82f6', lw=2.0)

for name, (x, y) in pts.items():
    ax.plot(x, y, marker='o', markersize=6, color='#dc2626')
    ax.text(x, y + 0.15, name, fontsize=7, ha='center', color='#1e293b', fontweight='semibold')

# Heuristic Explanation Box on right
box_rules = patches.FancyBboxPatch((5.4, 0.6), 2.5, 3.2, boxstyle="round,pad=0.1", fc='#f8fafc', ec='#94a3b8', lw=1.2)
ax.add_patch(box_rules)
ax.text(6.65, 3.5, 'QUY TẮC TÍNH ĐIỂM 2D', ha='center', fontsize=8.5, fontweight='bold', color='#0f172a')
explanation = (
    "1. Lọc nhiễu EMA (α = 0,75)\n"
    "2. Khoảng cách Mũi - Tai:\n"
    "   d(Nose, L_Ear) vs d(Nose, R_Ear)\n"
    "3. Bất đối xứng Mắt - Vai:\n"
    "   Vector lệch trục đối xứng\n"
    "4. Chuẩn hóa điểm: S ∈ [0.0, 1.0]\n"
    "5. Ngưỡng cờ Vàng: S ≥ 0,50\n"
    "6. Leo thang cờ Đỏ:\n"
    "   Duy trì liên tục ≥ 1,25 giây\n"
    "   (Khử cảnh báo cử động thoáng qua)"
)
ax.text(5.55, 2.0, explanation, ha='left', va='center', fontsize=7.5, color='#334155', linespacing=1.4)

ax.set_xlim(0, 8.2)
ax.set_ylim(0, 4.6)
plt.tight_layout()
p3 = os.path.join(diagram_dir, 'pose_heuristic_diagram.png')
plt.savefig(p3, bbox_inches='tight', dpi=300)
plt.close()
print(f"Generated {p3}")
