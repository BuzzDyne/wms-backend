from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from core.db_enums import PicklistTMStatus
from database import Picklist_TM, PicklistItem_TR
from datetime import datetime


# region PicklistTM
def get_picklist_by_id(db: Session, picklist_id: int):
    return db.query(Picklist_TM).filter(Picklist_TM.id == picklist_id).first()


def set_picklist_status(db: Session, picklist, new_picklist_status: PicklistTMStatus):
    picklist.picklist_status = new_picklist_status

    match new_picklist_status:
        case PicklistTMStatus.CANCELLED:
            picklist.draft_cancel_dt = datetime.now()

        case PicklistTMStatus.CREATED:
            picklist.creation_dt = datetime.now()

        case PicklistTMStatus.ON_PICKING:
            picklist.pick_start_dt = datetime.now()

        case PicklistTMStatus.COMPLETED:
            picklist.completion_dt = datetime.now()

    db.commit()


# endregion


# region PicklistItemTR
def get_picklistitems_by_picklist_id(db: Session, picklist_id: int):
    return (
        db.query(PicklistItem_TR)
        .filter(PicklistItem_TR.picklist_id == picklist_id)
        .all()
    )


# endregion
