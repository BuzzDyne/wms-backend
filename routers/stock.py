from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile
from datetime import datetime, timedelta
from openpyxl import load_workbook
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
from database import (
    get_db,
    PicklistFile_TR,
    PicklistItem_TR,
    ProductMapping_TR,
    Picklist_TM,
)
from constant import XLS_FILE_FORMAT
from core.error_codes import ErrCode as E
from core.db_enums import PicklistTMStatus, PicklistItemTRIsExcluded
from core.db_utils import (
    get_stocks,
    get_picklist_by_id,
    set_picklist_status,
    get_picklistitems_by_picklist_id,
    update_stock_quantity_by_stock_id,
)
from core.utils import validate_picklist_file, extract_picklist_item
from io import BytesIO

router = APIRouter(tags=["Stock"], prefix="/stock")


@router.get("/")
def get_all_stock(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    return {"data": get_stocks(db)}
