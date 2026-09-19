"""
================================================================================
SCRIPT CHAY TEST NHANH MODULE AI GIAM SAT PHONG THI (DEMO)
================================================================================
Dong doi co the chay file nay de kiem tra ngay module AI hoat dong:
    python test_demo.py
Hoac truyen video:
    python test_demo.py --video path/to/video.mp4
================================================================================
"""

import cv2
import sys
import os
import argparse

# Import Engine vua duoc dong goi
from exam_analyzer import ExamBehaviorDetector

def main():
    parser = argparse.ArgumentParser(description="Demo Test Exam Proctoring AI Module")
    parser.add_argument("--video", type=str, default=None, help="Duong dan video file (mac dinh la bat webcam)")
    args = parser.parse_args()

    # 1. Khoi tao Engine (Tu dong nhan dien weights trong thu muc weights/)
    print("-> Dang khoi tao ExamBehaviorDetector...")
    detector = ExamBehaviorDetector(
        phone_model_path="weights/phone_detector_v5.pt",
        pose_model_path="weights/yolo11m-pose.pt",
        phone_conf=0.35
    )

    # 2. Mo camera / video
    source = args.video if args.video else 0
    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"[LOI] Khong the mo nguon video: {source}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    print(f"[OK] Dang chay camera/video: {source}. Nhan 'q' tren cua so de thoat.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 3. GỌI ĐÚNG 1 HÀM NÀY ĐỂ XỬ LÝ FRAME
        annotated_frame, alerts = detector.process_frame(frame, fps=fps, draw=True)

        # 4. In thong tin canh bao ra terminal neu co hanh vi bat thuong
        for a in alerts:
            if a["status_code"] != "NORMAL":
                print(f"[CANH BAO] Thi sinh ID {a['track_id']}: {a['status']} | Diem: {a['score']:.2f} | Goc quay: {a['turn_deg']:.0f}° | Dien thoai: {a['has_phone']}")

        # 5. Hien thi len man hinh
        cv2.imshow("AI Exam Proctoring Demo", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
