from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from core.db_enums import PicklistTMStatus
from database import Picklist_TM, PicklistItem_TR, Stock_TM

from datetime import datetime


# region PicklistTM
def get_picklist_by_id(db: Session, picklist_id: int):
    return db.query(Picklist_TM).filter(Picklist_TM.id == picklist_id).first()


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


# region StockTM
def get_stock_by_stock_id(db: Session, stock_id: int):
    return db.query(Stock_TM).filter(Stock_TM.id == stock_id).first()


def update_stock_quantity_by_stock_id(db: Session, stock_id: int, count: int):
    stock = get_stock_by_stock_id(db, stock_id)
    stock.quantity -= count
    db.commit()


# endregion
