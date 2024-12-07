from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
from database import get_db, ProductMapping_TR
from constant import XLS_FILE_FORMAT
from core.error_codes import ErrCode as E
from core.db_enums import PicklistTMStatus, PicklistItemTRIsExcluded
from core.db_utils import (
    get_stocks,
    get_all_stock_size,
    get_all_stock_type,
    get_all_stock_color,
)

router = APIRouter(tags=["Stock"], prefix="/stock")


@router.get("/")
def get_all_stock(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    return {"data": get_stocks(db)}


@router.get("/variant-options")
def get_variants(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    return {
        "data": {
            "size": get_all_stock_size(db),
            "type": get_all_stock_type(db),
            "color": get_all_stock_color(db),
        }
    }
