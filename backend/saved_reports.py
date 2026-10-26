
import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import SavedReport, User

router = APIRouter(prefix="/saved-reports", tags=["Saved Reports"])


class SaveReportRequest(BaseModel):
    location: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    report_data: dict


@router.post("", status_code=201)
def save_report(
    data: SaveReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    report = SavedReport(
        user_id=current_user.id,
        location=data.location.strip(),
        title=data.title.strip(),
        report_data=json.dumps(data.report_data),
        created_at=now,
        expires_at=now + timedelta(hours=24),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "id": report.id,
        "location": report.location,
        "title": report.title,
        "created_at": report.created_at,
        "expires_at": report.expires_at,
    }


@router.get("")
def list_saved_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.query(SavedReport).filter(
        SavedReport.user_id == current_user.id,
        SavedReport.expires_at <= now,
    ).delete(synchronize_session=False)
    db.commit()

    reports = (
        db.query(SavedReport)
        .filter(
            SavedReport.user_id == current_user.id,
            SavedReport.expires_at > now,
        )
        .order_by(SavedReport.created_at.desc())
        .all()
    )

    return [
        {
            "id": r.id,
            "location": r.location,
            "title": r.title,
            "report_data": json.loads(r.report_data),
            "created_at": r.created_at,
            "expires_at": r.expires_at,
        }
        for r in reports
    ]


@router.get("/{report_id}")
def get_saved_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    report = db.query(SavedReport).filter(
        SavedReport.id == report_id,
        SavedReport.user_id == current_user.id,
        SavedReport.expires_at > now,
    ).first()

    if report is None:
        raise HTTPException(status_code=404, detail="Saved report not found or expired")

    return {
        "id": report.id,
        "location": report.location,
        "title": report.title,
        "report_data": json.loads(report.report_data),
        "created_at": report.created_at,
        "expires_at": report.expires_at,
    }


@router.delete("/{report_id}", status_code=204)
def delete_saved_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(SavedReport).filter(
        SavedReport.id == report_id,
        SavedReport.user_id == current_user.id,
    ).first()

    if report is None:
        raise HTTPException(status_code=404, detail="Saved report not found")

    db.delete(report)
    db.commit()
