# Dataset Protocol & Structure (Sprint 2.1A)

## Structure
- datasets/phone/
  - images/{train,val,test}/
  - labels/{train,val,test}/
  - metadata/samples.csv
  - metadata/sessions.csv
  - data_phone.yaml
- datasets/posture/
  - videos/{train,val,test}/
  - annotations/events.csv
  - metadata/sessions.csv

## Phone Dataset Protocol
1. Metadata Schema: `sample_id,relative_path,source_video_id,session_id,subject_id_anonymous,scene_id,camera_id,timestamp_seconds,split,has_phone,has_distractor,distractor_types,lighting,occlusion,distance_group,source_provenance,usage_permission`
2. Distractor & Hard-Negative Rules:
   - `has_phone`: boolean indicating whether at least one real phone is present.
   - `has_distractor`: boolean indicating whether distractors (Casio calculator, pencil case, wallet, etc.) are present.
   - `distractor_types`: pipe-separated string (e.g., `calculator|wallet|pencil_case`).
   - `has_phone=False` -> label file MUST be strictly empty (0 annotations).
   - `has_phone=True` -> label file MUST have at least one annotation for class 0 (phone).
   - `has_phone=True` and `has_distractor=True` CAN coexist in the same image.
   - Distractors do NOT create a separate YOLO class. Only class 0 exists.
3. Bounding Box Rules:
   - Exactly 5 finite numeric fields: `0 xc yc w h` (no NaN, no Inf).
   - Strictly bounded: $0 \le xc \le 1$, $0 \le yc \le 1$, $0 < w \le 1$, $0 < h \le 1$.
   - Strictly within image boundaries: $xc - w/2 \ge 0$, $xc + w/2 \le 1$, $yc - h/2 \ge 0$, $yc + h/2 \le 1$. No outer tolerance allowed.
4. Data Integrity:
   - No duplicate `sample_id` or `relative_path`.
   - All images must have matching label files (no orphan images, no orphan labels).
   - All image files must be readable and uncorrupted.

## Posture Dataset Protocol
1. Metadata Schema: `event_id,video_id,target_id_anonymous,scene_id,behavior,start_seconds,end_seconds,direction,severity,annotator,review_status,split`
2. Annotation Rules:
   - Annotator records behavior (`HEAD_TURNING` / `NORMAL`), start/end seconds, direction, and target anonymous ID.
   - Severity (`YELLOW`/`RED`) is derived from duration threshold (duration $\ge 1.25$s $\to$ `RED`, else `YELLOW`).
   - Video duration in `sessions.csv` must be $\ge end\_seconds$.
   - Normal duration = `video_duration - union_duration(approved HEAD_TURNING intervals)`.
   - FAR is computed per minute of normal duration; if normal duration is 0, FAR is `not_applicable`.
