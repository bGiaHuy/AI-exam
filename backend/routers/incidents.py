"""
================================================================================
INCIDENTS ROUTER - AI EXAM CONTROL
================================================================================
Anonymous event management: query, filter, paginate, and review incidents.
Zero personal identity information.
================================================================================
"""

import os
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Incident
from schemas import IncidentResponse, IncidentConfirmRequest, IncidentDeleteResponse
from routers.ai_engine import verify_write_allowed
from services.evidence_files import delete_evidence

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

router = APIRouter(prefix="/incidents", tags=["Incidents"])
EVIDENCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "evidence"))


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


@router.delete("/videos/purge-all", response_model=IncidentDeleteResponse, dependencies=[Depends(verify_write_allowed)])
def purge_all_incident_videos(
    db: Session = Depends(get_db)
):
    """
    Xoá toàn bộ các tệp video bằng chứng vi phạm trên ổ đĩa và cập nhật CSDL.
    Tuyệt đối không lưu lại video trên ổ cứng hay đẩy lên kho lưu trữ GitHub.
    """
    logger.info("[PURGE_ALL_VIDEOS] Requested deletion of all completed evidence")
    return _delete_evidence_response(db)


@router.delete("/{incident_id}", response_model=IncidentDeleteResponse, dependencies=[Depends(verify_write_allowed)])
def delete_incident(
    incident_id: str,
    db: Session = Depends(get_db)
):
    """
    Xoá vĩnh viễn sự cố vi phạm và file video/ảnh bằng chứng liên quan trên ổ đĩa.
    """
    logger.info("[DELETE_INCIDENT] Requested incident_id=%s", incident_id)
    return _delete_evidence_response(db, incident_id)


def _delete_evidence_response(db: Session, incident_id: Optional[str] = None):
    try:
        result = delete_evidence(db, EVIDENCE_DIR, incident_id)
    except Exception:
        logger.exception("[DELETE_INCIDENT] Deletion failed incident_id=%s", incident_id or "all")
        raise HTTPException(status_code=500, detail="Không hoàn tất xóa bằng chứng. Vui lòng thử lại; kiểm tra log nếu lỗi tiếp diễn.")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy sự cố với mã '{incident_id}'.")
    return result
