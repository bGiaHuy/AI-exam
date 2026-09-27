"""
================================================================================
INCIDENTS ROUTER - AI EXAM CONTROL
================================================================================
Anonymous event management: query, filter, paginate, and review incidents.
Zero personal identity information.
================================================================================
"""

import os
import glob
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Incident
from schemas import IncidentResponse, IncidentConfirmRequest
from routers.ai_engine import verify_write_allowed

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=List[IncidentResponse])
def get_incidents(
    source_id: Optional[str] = Query(None, description="Lọc sự cố theo nguồn video/camera"),
    violation_type: Optional[str] = Query(None, description="Lọc theo loại: PHONE hoặc HEAD_TURNING"),
    level: Optional[str] = Query(None, description="Lọc theo mức độ: 'yellow' hoặc 'red'"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái: 'pending', 'confirmed', 'dismissed'"),
    limit: int = Query(50, ge=1, le=200, description="Số bản ghi tối đa"),
    skip: int = Query(0, ge=0, description="Phân trang"),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách các sự cố vi phạm ghi nhận được, sắp xếp mới nhất lên đầu.
    """
    query = db.query(Incident)

    if source_id:
        query = query.filter(Incident.source_id == source_id.strip())

    if violation_type:
        query = query.filter(Incident.violation_type == violation_type.strip().upper())

    if level:
        query = query.filter(Incident.level == level.strip().lower())

    if status:
        query = query.filter(Incident.status == status.strip().lower())

    return (
        query.order_by(Incident.detected_at.desc(), Incident.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.patch("/{incident_id}/confirm", response_model=IncidentResponse, dependencies=[Depends(verify_write_allowed)])
def confirm_incident(
    incident_id: str,
    payload: IncidentConfirmRequest,
    db: Session = Depends(get_db)
):
    """
    Giám thị/Người vận hành xác nhận hoặc bỏ qua cảnh báo vi phạm.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy sự cố với mã '{incident_id}'."
        )

    incident.status = payload.status

    if payload.notes:
        incident.proctor_notes = payload.notes

    db.commit()
    db.refresh(incident)
    return incident


@router.delete("/videos/purge-all", dependencies=[Depends(verify_write_allowed)])
def purge_all_incident_videos(
    db: Session = Depends(get_db)
):
    """
    Xoá toàn bộ các tệp video bằng chứng vi phạm trên ổ đĩa và cập nhật CSDL.
    Tuyệt đối không lưu lại video trên ổ cứng hay đẩy lên kho lưu trữ GitHub.
    """
    evidence_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "evidence"))
    deleted_files = 0
    if os.path.isdir(evidence_dir):
        for ext in ("*.mp4", "*.avi", "*.mov", "*.webm", "*.mkv", "*.jpg", "*.png"):
            for f in glob.glob(os.path.join(evidence_dir, ext)):
                try:
                    os.remove(f)
                    deleted_files += 1
                except Exception as e:
                    logger.warning(f"[PURGE_ALL_VIDEOS] Lỗi xoá file {f}: {e}")

    try:
        deleted_records = db.query(Incident).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        deleted_records = 0
        logger.error(f"[PURGE_ALL_VIDEOS] Lỗi cập nhật CSDL: {e}")

    logger.info(f"[PURGE_ALL_VIDEOS] Đã xoá {deleted_files} tệp và {deleted_records} bản ghi sự cố.")
    return {
        "success": True, 
        "deleted_files_count": deleted_files,
        "deleted_records_count": deleted_records,
        "message": f"Đã xoá sạch {deleted_files} tệp video và hình ảnh bằng chứng khỏi hệ thống."
    }


@router.delete("/{incident_id}", dependencies=[Depends(verify_write_allowed)])
def delete_incident(
    incident_id: str,
    db: Session = Depends(get_db)
):
    """
    Xoá vĩnh viễn sự cố vi phạm và file video/ảnh bằng chứng liên quan trên ổ đĩa.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy sự cố với mã '{incident_id}'."
        )

    evidence_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "evidence"))
    # Delete video file
    if incident.video_path:
        filename = os.path.basename(incident.video_path)
        video_full_path = os.path.join(evidence_dir, filename)
        if os.path.isfile(video_full_path):
            try:
                os.remove(video_full_path)
            except Exception as e:
                logger.warning(f"[DELETE_INCIDENT] Không thể xoá video file {video_full_path}: {e}")

    # Delete snapshot file
    if incident.snapshot_path:
        filename = os.path.basename(incident.snapshot_path)
        snap_full_path = os.path.join(evidence_dir, filename)
        if os.path.isfile(snap_full_path):
            try:
                os.remove(snap_full_path)
            except Exception as e:
                logger.warning(f"[DELETE_INCIDENT] Không thể xoá snapshot file {snap_full_path}: {e}")

    db.delete(incident)
    db.commit()
    logger.info(f"[DELETE_INCIDENT] Đã xoá sự cố '{incident_id}' và các tệp liên quan.")
    return {"success": True, "message": f"Đã xoá sự cố '{incident_id}'."}
