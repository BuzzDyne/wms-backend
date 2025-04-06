from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
from database import get_db
from schemas import InboundSchedule
from core.db_utils import get_all_inbound_schedules

router = APIRouter(tags=["Inbound"], prefix="/inbound")


@router.get("/schedules", response_model=List[InboundSchedule])
def list_inbound_schedules(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    user_id = Authorize.get_raw_jwt()["user_id"]
    schedules = get_all_inbound_schedules(db)
    return schedules
