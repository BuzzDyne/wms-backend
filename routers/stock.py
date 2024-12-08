from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
from database import get_db, ProductMapping_TR
from constant import XLS_FILE_FORMAT
from core.utils import transform_size_names, transform_type_name, transform_color_name
from core.error_codes import ErrCode as E
from core.db_enums import PicklistTMStatus, PicklistItemTRIsExcluded
from schemas import (
    CreateNewVariantTypeRequest,
    CreateNewVariantSizeRequest,
    CreateNewVariantColorRequest,
)
from core.db_utils import (
    get_stocks,
    get_all_stock_size,
    get_all_stock_type,
    get_all_stock_color,
    get_stocksize_by_value,
    create_stocksize,
    get_stocktype_by_value,
    create_stocktype,
    get_stockcolor_by_name,
    create_stockcolor,
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


@router.post("/variant/size")
def create_variant_size(
    data: CreateNewVariantSizeRequest,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    # Transform start name
    valid_names = transform_size_names(data.size_name_start, data.size_name_end)

    if not valid_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.STO_NSZ_E01),
        )

    # Check existing size
    name, value = valid_names
    db_size = get_stocksize_by_value(db, value)

    if db_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.STO_NSZ_E02, db_size.size_value),
        )

    # Create in DB
    db_size = create_stocksize(db, value, name)

    return {"msg": "Create new size successful", "data": db_size}


@router.post("/variant/type")
def create_variant_type(
    data: CreateNewVariantTypeRequest,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    valid_names = transform_type_name(data.type_name)

    if not valid_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.STO_NTY_E01),
        )

    # Check existing type
    name, value = valid_names
    db_type = get_stocktype_by_value(db, value)

    if db_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.STO_NTY_E02, db_type.type_value),
        )

    # Create in DB
    db_type = create_stocktype(db, value, name)

    return {"msg": "Create new type successful", "data": db_type}


@router.post("/variant/color")
def create_variant_color(
    data: CreateNewVariantColorRequest,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    valid_names = transform_color_name(data.color_name, data.color_hex)

    if not valid_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.STO_NCO_E01),
        )

    # Check existing size
    name, hexa = valid_names
    db_color = get_stockcolor_by_name(db, name)

    if db_color:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.STO_NCO_E02, db_color.color_name),
        )

    # Create in DB
    db_color = create_stockcolor(db, name, hexa)

    return {"msg": "Create new color successful", "data": db_color}
