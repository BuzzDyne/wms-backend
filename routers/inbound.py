from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.exc import NoResultFound
from database import get_db, MasterParameter_TM, InboundSchedule_TM
from schemas import InboundSchedule, CreateScheduleRequest
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(tags=["Inbound"], prefix="/inbound")


@router.get("/schedules", response_model=List[InboundSchedule])
def list_inbound_schedules(
    year: int = Query(
        ..., ge=1000, le=9999, description="Year must be a 4-digit number"
    ),
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    schedules = (
        db.query(InboundSchedule_TM)
        .filter(InboundSchedule_TM.schedule_date.like(f"{year}%"))
        .all()
    )
    return [
        {
            "id": schedule.id,
            "schedule_date": schedule.schedule_date,
            "created_dt": schedule.created_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "creator_id": schedule.creator_id,
            "notes": schedule.notes if schedule.notes else "Scheduled Inbound",
            "is_active": schedule.is_active,
        }
        for schedule in schedules
    ]


@router.post("/schedules")
def create_inbound_schedule(
    schedule: CreateScheduleRequest,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    new_schedule = InboundSchedule_TM(
        schedule_date=schedule.schedule_date,
        created_dt=datetime.now(),
        creator_id=Authorize.get_raw_jwt()["user_id"],
        notes=schedule.notes,
        is_active=1,
    )
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    return {"message": "Schedule created successfully", "schedule_id": new_schedule.id}


@router.delete("/schedules/{schedule_id}")
def delete_inbound_schedule(
    schedule_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    schedule = db.query(InboundSchedule_TM).filter_by(id=schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted successfully"}


@router.get("/inbound-status")
def get_inbound_status(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    try:
        parameter = (
            db.query(MasterParameter_TM)
            .filter_by(parameter_name="inbound_active")
            .one()
        )
        return {"inbound_active": parameter.parameter_value_int}
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="Inbound status parameter not found"
        )


@router.put("/inbound-status/toggle/{on_off}")
def toggle_inbound_status(
    on_off: str = Path(..., regex="^(on|off)$"),
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    try:
        parameter = (
            db.query(MasterParameter_TM)
            .filter_by(parameter_name="inbound_active")
            .one()
        )
        parameter.parameter_value_int = 1 if on_off == "on" else 0
        db.commit()
        return {
            "message": f"Inbound status updated to {'on' if on_off == 'on' else 'off'}"
        }
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="Inbound status parameter not found"
        )
