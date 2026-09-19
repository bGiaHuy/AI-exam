"""
================================================================================
INCIDENTS ROUTER - AI EXAM CONTROL
================================================================================
Anonymous event management: query, filter, paginate, and review incidents.
Zero personal identity information.
================================================================================
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Incident
from schemas import IncidentResponse, IncidentConfirmRequest

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


@router.patch("/{incident_id}/confirm", response_model=IncidentResponse)
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
