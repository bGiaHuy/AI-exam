"""
================================================================================
EXAM BEHAVIOR DETECTOR & MULTI-ANGLE CHEATING ANALYZER (V7 ENGINE)
================================================================================
Module tich hop AI giam sat phong thi:
1. Uoc luong tu the (YOLO Pose Estimation) & Theo vet thi sinh (ByteTrack)
2. Nhan dien vat the cam (YOLO Phone Detection) & Gan dien thoai cho thi sinh
3. Phan tich chuyen sau goc nghieng dau, boc tach Yaw/Roll, huong quay nguoi
4. Bo loc lam muot EMA khu rung giat keypoint qua thoi gian
5. Bo dem thoi gian nghi ngo tranh bao dong gia (Temporal Suspicion Consensus)
================================================================================
"""

import os
import sys
import math
import argparse
from collections import defaultdict
import numpy as np
import cv2
from ultralytics import YOLO

# ==============================================================================
# 1. CAC HANG SO HINH HOC & CAU HINH MAC DINH
# ==============================================================================
DEFAULT_PHONE_CONF = 0.35
DEFAULT_SUSPICION_THRESHOLD = 0.50
DEFAULT_ALERT_SECONDS = 1.25
DEFAULT_BASELINE_FRAMES = 30

# Chi so COCO Keypoints
NOSE = 0
L_EYE, R_EYE = 1, 2
L_EAR, R_EAR = 3, 4
L_SHOULDER, R_SHOULDER = 5, 6
L_ELBOW, R_ELBOW = 7, 8
L_WRIST, R_WRIST = 9, 10
L_HIP, R_HIP = 11, 12

# Mau sac hien thi (BGR)
COLOR_NORMAL = (0, 220, 0)       # Xanh la - Binh thuong
COLOR_SUSPICIOUS = (0, 220, 255) # Vang - Nghi ngo
COLOR_CHEATING = (0, 0, 255)     # Do - Gian lan / Phat hien dien thoai
COLOR_GRAY = (190, 190, 190)     # Xam - Thong tin phu


# ==============================================================================
# 2. CAC HAM HINH HOC CO BAN
# ==============================================================================
def dist(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def mid(p1, p2):
    return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

def xy(kp, idx):
    return (float(kp[idx][0]), float(kp[idx][1]))

def conf(kp, idx):
    return float(kp[idx][2])

def box_center(box):
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


# ==============================================================================
# 3. BO LOC LAM MUOT KEYPOINTS (EMA FILTER)
# ==============================================================================
class KeypointSmoother:
    """Lam muot toa do keypoint qua thoi gian (EMA) de khu rung giat pixel."""
    def __init__(self, alpha=0.75):
        self.alpha = alpha
        self.history = {}

    def smooth(self, track_id, kp):
        if hasattr(kp, "detach"):
            kp_arr = kp.detach().cpu().numpy().copy()
        elif isinstance(kp, np.ndarray):
            kp_arr = kp.copy()
        else:
            kp_arr = np.array(kp, dtype=np.float32)

        if track_id not in self.history:
            self.history[track_id] = kp_arr
            return kp_arr

        prev = self.history[track_id]
        for idx in range(len(kp_arr)):
            if kp_arr[idx][2] > 0.15 and prev[idx][2] > 0.15:
                kp_arr[idx][0] = self.alpha * kp_arr[idx][0] + (1 - self.alpha) * prev[idx][0]
                kp_arr[idx][1] = self.alpha * kp_arr[idx][1] + (1 - self.alpha) * prev[idx][1]

        self.history[track_id] = kp_arr
        return kp_arr

    def clear(self):
        self.history.clear()


# ==============================================================================
# 4. GAN DIEN THOAI CHO THI SINH (SMART PHONE ASSIGNMENT)
# ==============================================================================
def person_anchor(kp, phone_center=None):
    best_wrist = None
    best_wrist_dist = float('inf')
    for w_idx in [L_WRIST, R_WRIST]:
        if conf(kp, w_idx) > 0.25:
            w_pos = xy(kp, w_idx)
            if phone_center is not None:
                d = dist(w_pos, phone_center)
                if d < best_wrist_dist:
                    best_wrist_dist = d
                    best_wrist = w_pos
            else:
                return w_pos
    if best_wrist is not None:
        return best_wrist

    if conf(kp, L_SHOULDER) > 0.25 and conf(kp, R_SHOULDER) > 0.25:
        return mid(xy(kp, L_SHOULDER), xy(kp, R_SHOULDER))

    if conf(kp, NOSE) > 0.2:
        return xy(kp, NOSE)

    return None

def assign_phones_to_persons(phone_boxes, all_keypoints, all_person_boxes):
    persons_with_phone = set()
    for phone_box in phone_boxes:
        phone_cx, phone_cy = box_center(phone_box)
        best_person_idx = -1
        best_distance = float('inf')

        for i, kp in enumerate(all_keypoints):
            anchor = person_anchor(kp, phone_center=(phone_cx, phone_cy))
            if anchor is None:
                continue

            d = dist(anchor, (phone_cx, phone_cy))
            pb = all_person_boxes[i]
            person_diag = dist((pb[0], pb[1]), (pb[2], pb[3]))
            max_allowed = person_diag * 1.5

            if d < best_distance and d < max_allowed:
                best_distance = d
                best_person_idx = i

        if best_person_idx >= 0:
            persons_with_phone.add(best_person_idx)

    return persons_with_phone


# ==============================================================================
# 5. TRANG THAI NGUOI & ENGINE PHAN TICH HANH VI GIAN LAN (V7)
# ==============================================================================
class PersonState:
    def __init__(self, baseline_frames=DEFAULT_BASELINE_FRAMES):
        self.suspicion_count = 0
        self.baseline_frames = baseline_frames
        self.baseline_body_angles = []
        self.baseline_body_angle = None
        self.last_status = "Normal"

    def update_baseline(self, body_angle):
        if len(self.baseline_body_angles) < self.baseline_frames:
            self.baseline_body_angles.append(body_angle)
            if len(self.baseline_body_angles) == self.baseline_frames:
                s = sorted(self.baseline_body_angles)
                self.baseline_body_angle = s[len(s) // 2]


class AdaptiveMonitor:
    def __init__(self, baseline_frames=DEFAULT_BASELINE_FRAMES, 
                       suspicion_threshold=DEFAULT_SUSPICION_THRESHOLD, 
                       alert_seconds=DEFAULT_ALERT_SECONDS):
        self.states = defaultdict(lambda: PersonState(baseline_frames=baseline_frames))
        self.smoother = KeypointSmoother(alpha=0.75)
        self.baseline_frames = baseline_frames
        self.suspicion_threshold = suspicion_threshold
        self.alert_seconds = alert_seconds

    def analyze(self, raw_kp, track_id, fps=30, img_w=1280, img_h=720):
        kp = self.smoother.smooth(track_id, raw_kp)
        state = self.states[track_id]
        signals = []

        # ----------------------------------------------------
        # 1. XAC DINH HE TRUC THAN NGUOI (TORSO REFERENCE FRAME)
        # ----------------------------------------------------
        has_shoulders = (conf(kp, L_SHOULDER) > 0.25 and conf(kp, R_SHOULDER) > 0.25)
        l_sh, r_sh = (0, 0), (0, 0)
        sh_center = (0, 0)
        sh_width = 1.0
        sh_angle = 0.0
        body_score = 0.0

        if has_shoulders:
            l_sh = xy(kp, L_SHOULDER)
            r_sh = xy(kp, R_SHOULDER)
            sh_center = mid(l_sh, r_sh)
            sh_width = dist(l_sh, r_sh)
            sh_angle = math.atan2(l_sh[1] - r_sh[1], l_sh[0] - r_sh[0])
            state.update_baseline(sh_angle)

            if state.baseline_body_angle is not None:
                dev = abs(sh_angle - state.baseline_body_angle)
                if dev > math.pi:
                    dev = 2 * math.pi - dev
                body_dev_deg = math.degrees(dev)
                if body_dev_deg >= 18.0:
                    body_score = min((body_dev_deg - 18.0) / 18.0, 1.0)
                    signals.append(("BodyRot", body_score, 0.8))

        # ----------------------------------------------------
        # 2. XAC DINH CAC DIEM KHUON MAT & TRUC DAU
        # ----------------------------------------------------
        has_eyes = (conf(kp, L_EYE) > 0.25 and conf(kp, R_EYE) > 0.25)
        has_ears = (conf(kp, L_EAR) > 0.25 and conf(kp, R_EAR) > 0.25)
        has_nose = (conf(kp, NOSE) > 0.25)
        face_present = (has_eyes or (has_nose and (conf(kp, L_EAR) > 0.25 or conf(kp, R_EAR) > 0.25)))

        head_center = None
        if has_eyes:
            head_center = mid(xy(kp, L_EYE), xy(kp, R_EYE))
        elif has_nose:
            head_center = xy(kp, NOSE)
        elif has_ears:
            head_center = mid(xy(kp, L_EAR), xy(kp, R_EAR))
        elif conf(kp, L_EAR) > 0.25:
            head_center = xy(kp, L_EAR)
        elif conf(kp, R_EAR) > 0.25:
            head_center = xy(kp, R_EAR)

        # ----------------------------------------------------
        # 3. BÓC TÁCH CHUYÊN SÂU: ROLL vs YAW (KHI CO MAT TRUOC)
        # ----------------------------------------------------
        yaw_score = 0.0
        detected_yaw_deg = 0.0
        is_frontal_centered = False

        # CA A: Co Mui va 2 Mat (Khuon mat day du - khong bi che)
        if has_nose and has_eyes:
            l_e = xy(kp, L_EYE)
            r_e = xy(kp, R_EYE)
            n_p = xy(kp, NOSE)
            m_e = mid(l_e, r_e)
            eye_dist = dist(l_e, r_e)

            if eye_dist > 5.0:
                eye_vec_x = (l_e[0] - r_e[0]) / eye_dist
                eye_vec_y = (l_e[1] - r_e[1]) / eye_dist
                vn_x = n_p[0] - m_e[0]
                vn_y = n_p[1] - m_e[1]

                nose_proj = vn_x * eye_vec_x + vn_y * eye_vec_y
                symmetry_offset = abs(nose_proj) / (eye_dist / 2.0)

                d_l = dist(n_p, l_e)
                d_r = dist(n_p, r_e)
                max_d = max(d_l, d_r)
                min_d = min(d_l, d_r)
                sym_ratio = (min_d / max_d) if max_d > 0 else 1.0

                # Khi nhin thang vao bai lam: mat can doi, offset nho
                if symmetry_offset < 0.24 and sym_ratio >= 0.58:
                    is_frontal_centered = True
                    yaw_score = 0.0
                    detected_yaw_deg = 0.0
                elif symmetry_offset >= 0.28 or sym_ratio < 0.52:
                    s_off = min(max(symmetry_offset - 0.28, 0.0) / 0.35, 1.0)
                    s_rat = min(max(0.52 - sym_ratio, 0.0) / 0.28, 1.0)
                    yaw_score = max(s_off, s_rat)
                    detected_yaw_deg = max(symmetry_offset * 60.0, (1.0 - sym_ratio) * 60.0)

        # CA B: Deo Khau Trang (Mat bi che Mui, chi co 2 Mat va 2 Tai)
        elif has_eyes and has_ears:
            m_eyes = mid(xy(kp, L_EYE), xy(kp, R_EYE))
            m_ears = mid(xy(kp, L_EAR), xy(kp, R_EAR))
            eye_w = dist(xy(kp, L_EYE), xy(kp, R_EYE))

            if eye_w > 5.0:
                ear_eye_offset = dist(m_eyes, m_ears) / eye_w
                if ear_eye_offset >= 0.35:
                    yaw_score = min((ear_eye_offset - 0.35) / 0.30, 1.0)
                    detected_yaw_deg = ear_eye_offset * 50.0

        # CA C: Che khuat Tai khong doi xung (Ear Occlusion Asymmetry - Tu V6)
        ear_asym_score = 0.0
        if face_present and not is_frontal_centered:
            has_l_ear = conf(kp, L_EAR) > 0.35
            has_r_ear = conf(kp, R_EAR) > 0.35
            if has_l_ear and not has_r_ear and conf(kp, R_EAR) < 0.15:
                ear_asym_score = 0.65
            elif has_r_ear and not has_l_ear and conf(kp, L_EAR) < 0.15:
                ear_asym_score = 0.65

        head_turn_score = max(yaw_score, ear_asym_score)
        if head_turn_score > 0.15:
            disp_deg = detected_yaw_deg if detected_yaw_deg > 0 else (head_turn_score * 45.0)
            signals.append((f"Turn({disp_deg:.0f}°)", head_turn_score, 1.0))
        else:
            disp_deg = 0.0

        # ----------------------------------------------------
        # 4. DO LECH NGANG DAU KET HOP (TIERED LATERAL DRIFT)
        # ----------------------------------------------------
        lateral_drift_score = 0.0
        lateral_ratio = 0.0
        if head_center is not None and has_shoulders and sh_width > 10.0:
            vx = head_center[0] - sh_center[0]
            vy = head_center[1] - sh_center[1]
            cos_sh = math.cos(sh_angle)
            sin_sh = math.sin(sh_angle)
            proj_x = vx * cos_sh + vy * sin_sh
            lateral_ratio = abs(proj_x) / (sh_width / 2.0)
            if lateral_ratio >= 0.38:
                lateral_drift_score = min((lateral_ratio - 0.38) / 0.25, 1.0)

        # ----------------------------------------------------
        # 5. XU LY MAT MAT TRUOC (CUI DAU SAU vs SIDEVIEW vs TURNBACK)
        # ----------------------------------------------------
        face_lost_score = 0.0
        if not face_present:
            if body_score >= 0.30:
                face_lost_score = 0.80
                signals.append(("TurnBack", 0.80, 1.0))
            elif lateral_ratio >= 0.30 or body_score >= 0.20:
                face_lost_score = 0.70
                signals.append(("SideView", 0.70, 1.0))
            elif has_shoulders and sh_width > 10.0:
                if conf(kp, L_EAR) > 0.30 and conf(kp, R_EAR) > 0.30:
                    l_ear_pt = xy(kp, L_EAR)
                    r_ear_pt = xy(kp, R_EAR)
                    ear_ang = math.atan2(l_ear_pt[1] - r_ear_pt[1], l_ear_pt[0] - r_ear_pt[0])
                    diff_ang = abs(ear_ang - sh_angle)
                    if diff_ang > math.pi:
                        diff_ang = 2 * math.pi - diff_ang
                    diff_deg = math.degrees(diff_ang)
                    if diff_deg >= 22.0:
                        face_lost_score = 0.70
                        signals.append((f"SideView({diff_deg:.0f}°)", 0.70, 1.0))
                elif conf(kp, L_EAR) > 0.35 or conf(kp, R_EAR) > 0.35:
                    cos_sh = math.cos(sh_angle)
                    sin_sh = math.sin(sh_angle)
                    is_head_twisted = False
                    if conf(kp, L_EAR) > 0.35:
                        v_ear_x = xy(kp, L_EAR)[0] - l_sh[0]
                        v_ear_y = xy(kp, L_EAR)[1] - l_sh[1]
                        proj_ear = abs(v_ear_x * cos_sh + v_ear_y * sin_sh)
                        offset_ratio = proj_ear / sh_width
                        if offset_ratio > 0.26:
                            is_head_twisted = True
                    elif conf(kp, R_EAR) > 0.35:
                        v_ear_x = xy(kp, R_EAR)[0] - r_sh[0]
                        v_ear_y = xy(kp, R_EAR)[1] - r_sh[1]
                        proj_ear = abs(v_ear_x * cos_sh + v_ear_y * sin_sh)
                        offset_ratio = proj_ear / sh_width
                        if offset_ratio > 0.26:
                            is_head_twisted = True

                    if is_head_twisted:
                        face_lost_score = 0.70
                        signals.append(("SideView", 0.70, 1.0))

        # ----------------------------------------------------
        # 6. CO TAY VUON XA BAT THUONG (WRIST REACH ANOMALY)
        # ----------------------------------------------------
        wrist_score = 0.0
        if has_shoulders and sh_width > 10.0:
            for w_idx in [L_WRIST, R_WRIST]:
                if conf(kp, w_idx) > 0.30:
                    ratio = dist(xy(kp, w_idx), sh_center) / sh_width
                    if ratio > 1.30:
                        s = min((ratio - 1.30) / 0.45, 1.0)
                        if s > wrist_score:
                            wrist_score = s
            if wrist_score > 0.15:
                signals.append(("Wrist", wrist_score, 0.7))

        # ----------------------------------------------------
        # 7. LOGIC PHAN QUYET PHAN TANG DONG THUAN (TIERED CONSENSUS)
        # ----------------------------------------------------
        primary_violation = max(head_turn_score, face_lost_score, wrist_score)

        if primary_violation >= 0.55:
            final_score = primary_violation
        elif head_turn_score >= 0.35 and body_score >= 0.30:
            final_score = 0.65
        elif head_turn_score >= 0.35 and lateral_drift_score >= 0.40:
            final_score = 0.60
        elif head_turn_score >= 0.35 and wrist_score >= 0.35:
            final_score = 0.65
        elif body_score >= 0.65:
            final_score = 0.60
        else:
            final_score = 0.0

        alert_frames = int(fps * self.alert_seconds)
        is_instant_suspicious = (final_score >= self.suspicion_threshold)

        if is_instant_suspicious:
            state.suspicion_count += 1
        else:
            state.suspicion_count = max(0, state.suspicion_count - 3)

        sustained = (state.suspicion_count >= alert_frames)
        is_cheating_sustained = (is_instant_suspicious and sustained)

        if is_cheating_sustained:
            state.last_status = "!! GIAN LAN !!"
        elif is_instant_suspicious:
            state.last_status = "? NGHI NGO"
        else:
            state.last_status = "Normal"

        info_dict = {
            "turn_deg": disp_deg,
            "face_valid": face_present,
            "is_suspicious": is_instant_suspicious,
            "is_instant_suspicious": is_instant_suspicious,
            "is_cheating_sustained": is_cheating_sustained
        }
        return final_score, is_instant_suspicious, signals, info_dict

    def clear(self):
        self.states.clear()
        self.smoother.clear()


# ==============================================================================
# 6. CLASS DONG GOI CHUAN DE DONG DOI DE DANG MERGE & SU DUNG
# ==============================================================================
class ExamBehaviorDetector:
    """
    Class Engine tich hop AI:
    - Load san models (YOLO Pose + YOLO Phone)
    - Cung cap phuong thuc process_frame(frame, fps=30) danh cho moi luong Video/Webcam
    - Tra ve ca frame anh da ve va danh sach alert co cau truc (structured data)
    """
    def __init__(self, 
                 phone_model_path="weights/phone_detector_v5.pt", 
                 pose_model_path="weights/yolo11m-pose.pt", 
                 phone_conf=DEFAULT_PHONE_CONF,
                 suspicion_threshold=DEFAULT_SUSPICION_THRESHOLD,
                 alert_seconds=DEFAULT_ALERT_SECONDS,
                 tracker="bytetrack.yaml"):
        
        self.phone_conf = phone_conf
        self.tracker = tracker

        # Tim duong dan model thong minh neu nguoi dung truyen tuong doi
        resolved_pose = self._resolve_path(pose_model_path)
        resolved_phone = self._resolve_path(phone_model_path)

        print("[ExamBehaviorDetector] Loading Pose Model:", resolved_pose)
        self.pose_model = YOLO(resolved_pose)

        if resolved_phone and os.path.exists(resolved_phone):
            print("[ExamBehaviorDetector] Loading Phone Model:", resolved_phone)
            self.phone_model = YOLO(resolved_phone)
        else:
            print(f"[ExamBehaviorDetector] WARNING: Phone model '{phone_model_path}' not found! Running in Pose-only mode.")
            self.phone_model = None

        self.monitor = AdaptiveMonitor(
            suspicion_threshold=suspicion_threshold,
            alert_seconds=alert_seconds
        )

    def _resolve_path(self, path):
        if not path:
            return None
        if os.path.isabs(path) and os.path.exists(path):
            return path
        # Tim quanh thu muc hien tai hoac thu muc file nay
        current_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            path,
            os.path.join(current_dir, path),
            os.path.join(current_dir, "..", path),
            os.path.join(current_dir, "weights", os.path.basename(path))
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return path

    def reset(self):
        """Reset lai toan bo bo dem baseline va tracking khi bat dau phien thi moi."""
        self.monitor.clear()

    def process_frame(self, frame, fps=30, draw=True):
        """
        HAM XU LY FRAME CHINH:
        - Input: 
            + frame: anh OpenCV (numpy array BGR)
            + fps: frame rate cua camera/video
            + draw: True neu muon ve thang bounding box/text len frame tra ve
        - Output:
            + annotated_frame: frame da duoc ve truc quan
            + alerts: list cac dict chua thong tin chi tiet ve hanh vi cua tung thi sinh
        """
        h, w = frame.shape[:2]
        annotated_frame = frame.copy() if draw else frame
        alerts = []

        # 1. Pose Inference voi Tracker
        pose_results = self.pose_model.track(
            frame, 
            persist=True, 
            tracker=self.tracker, 
            verbose=False
        )[0]

        # 2. Phone Inference
        phone_boxes = []
        if self.phone_model is not None:
            phone_results = self.phone_model(frame, conf=self.phone_conf, imgsz=960, verbose=False)[0]
            for box in phone_results.boxes:
                bx1, by1, bx2, by2 = map(int, box.xyxy[0])
                phone_boxes.append((bx1, by1, bx2, by2))
                if draw:
                    cv2.rectangle(annotated_frame, (bx1, by1), (bx2, by2), COLOR_CHEATING, 3)
                    cv2.putText(annotated_frame, f"PHONE {box.conf[0]:.2f}",
                                (bx1, max(by1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_CHEATING, 2)

        # 3. Gan phone cho thi sinh
        persons_with_phone = set()
        if (pose_results.keypoints is not None 
                and len(pose_results.keypoints.data) > 0 
                and len(phone_boxes) > 0):
            all_kps = pose_results.keypoints.data
            all_pboxes = [pose_results.boxes[j].xyxy[0].tolist() for j in range(len(all_kps))]
            persons_with_phone = assign_phones_to_persons(phone_boxes, all_kps, all_pboxes)

        # 4. Xu ly phan tich tung thi sinh
        if pose_results.keypoints is not None and len(pose_results.keypoints.data) > 0:
            track_ids = pose_results.boxes.id

            for i, raw_kp in enumerate(pose_results.keypoints.data):
                tid = int(track_ids[i]) if track_ids is not None else i
                score, is_suspicious, signals, info = self.monitor.analyze(raw_kp, tid, fps, w, h)
                has_phone = i in persons_with_phone

                is_cheating_sustained = info.get("is_cheating_sustained", False)

                # Phan loai trang thai:
                # - Co dien thoai => GIAN LAN (Do)
                # - Vi pham tu the keo dai >= 1.25s => GIAN LAN (Do)
                # - Vua phat hien vi pham tu the => NGHI NGO (Vang)
                # - Con lai => Normal (Xanh)
                if has_phone:
                    status = "!! GIAN LAN (DT) !!"
                    status_code = "CHEATING_PHONE"
                    color = COLOR_CHEATING
                elif is_cheating_sustained:
                    status = "!! GIAN LAN (>1.25s) !!"
                    status_code = "CHEATING_POSTURE"
                    color = COLOR_CHEATING
                elif is_suspicious:
                    status = "? NGHI NGO"
                    status_code = "SUSPICIOUS"
                    color = COLOR_SUSPICIOUS
                else:
                    status = "Normal"
                    status_code = "NORMAL"
                    color = COLOR_NORMAL

                # Lay toa do box nguoi
                person_box = pose_results.boxes[i].xyxy[0].tolist() if pose_results.boxes is not None else None

                # Luu vao danh sach alert tra ve cho he thong
                alerts.append({
                    "track_id": tid,
                    "status": status,
                    "status_code": status_code,
                    "score": float(score),
                    "is_suspicious": bool(is_suspicious),
                    "has_phone": bool(has_phone),
                    "turn_deg": float(info.get("turn_deg", 0.0)),
                    "signals": signals,
                    "box": person_box
                })

                # Ve len frame neu yeu cau
                if draw:
                    if conf(raw_kp, NOSE) > 0.2:
                        tx, ty = int(xy(raw_kp, NOSE)[0]), int(xy(raw_kp, NOSE)[1])
                    elif conf(raw_kp, L_EYE) > 0.2 and conf(raw_kp, R_EYE) > 0.2:
                        c = mid(xy(raw_kp, L_EYE), xy(raw_kp, R_EYE))
                        tx, ty = int(c[0]), int(c[1])
                    elif conf(raw_kp, L_SHOULDER) > 0.2 and conf(raw_kp, R_SHOULDER) > 0.2:
                        c = mid(xy(raw_kp, L_SHOULDER), xy(raw_kp, R_SHOULDER))
                        tx, ty = int(c[0]), int(c[1]) - 30
                    else:
                        continue

                    angle_txt = f"Turn:{info['turn_deg']:.0f}°"
                    label = f"ID {tid}: {status} [{score:.2f}] | {angle_txt}"
                    cv2.putText(annotated_frame, label, (max(tx - 110, 10), max(ty - 30, 25)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

                    if signals:
                        sig_str = " | ".join(f"{n}:{s:.1f}" for n, s, w in signals)
                        cv2.putText(annotated_frame, sig_str, (max(tx - 110, 10), max(ty - 10, 45)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, COLOR_GRAY, 1)

        if draw and len(phone_boxes) > 0:
            cv2.putText(annotated_frame, f"!! PHONE DETECTED ({len(phone_boxes)}) !!", (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLOR_CHEATING, 2)

        return annotated_frame, alerts


# Alias de tuong thich ten goi
ExamMonitorEngine = ExamBehaviorDetector


# ==============================================================================
# 7. SCRIPT TEST DOC LAP (CLI / WEBCAM / VIDEO FILE)
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Exam Proctoring AI Monitor Engine (V7)")
    parser.add_argument("--video", type=str, default=None, help="Duong dan video dau vao (neu khong truyen se bat webcam)")
    parser.add_argument("--webcam", action="store_true", help="Su dung webcam (camera index 0)")
    parser.add_argument("--output", type=str, default=None, help="Duong dan luu video ket qua (neu chay video)")
    parser.add_argument("--phone-model", type=str, default="weights/phone_detector_v5.pt", help="Duong dan file weights phone")
    parser.add_argument("--pose-model", type=str, default="weights/yolo11m-pose.pt", help="Duong dan file weights pose")
    args = parser.parse_args()

    # Khoi tao Engine
    detector = ExamBehaviorDetector(
        phone_model_path=args.phone_model,
        pose_model_path=args.pose_model
    )

    # Chon nguon phat
    source = 0 if (args.webcam or args.video is None) else args.video
    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"Loi: Khong mo duoc nguon video '{source}'")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    out_writer = None
    if args.output and isinstance(source, str):
        out_writer = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    print(f"\n[OK] Bat dau chay giam sat tren: {source} ({w}x{h} @ {fps:.1f} FPS)")
    print("Nhan 'q' de dung lai.\n")

    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1

        annotated_frame, alerts = detector.process_frame(frame, fps=fps, draw=True)

        if out_writer:
            out_writer.write(annotated_frame)
            if frame_idx % 60 == 0:
                print(f"  Processed frame {frame_idx}/{total_frames}")
        else:
            cv2.imshow("Exam Monitor AI Engine (V7)", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    if out_writer:
        out_writer.release()
        print(f"\n[OK] Da luu video ket qua tai: {args.output}")
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
