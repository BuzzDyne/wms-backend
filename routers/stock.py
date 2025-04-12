from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
from database import get_db, Stock_TM, StockType_TR, StockColor_TR, StockSize_TR
from core.utils import transform_size_names, transform_type_name, transform_color_name
from core.error_codes import ErrCode as E
from schemas import (
    CreateNewVariantTypeRequest,
    CreateNewVariantSizeRequest,
    CreateNewVariantColorRequest,
    CreateNewStockRequest,
    UpdateStockQuantityRequest,
)
from core.db_utils import (
    get_all_stock_size,
    get_all_stock_type,
    get_all_stock_color,
    get_stocksize_by_value,
    create_stocksize,
    get_stocktype_by_value,
    create_stocktype,
    get_stockcolor_by_name,
    create_stockcolor,
    get_all_stocks_from_view,
    get_stock_by_variant_ids,
    create_stock,
    get_stock_by_stock_id,
)
from sqlalchemy import distinct

router = APIRouter(tags=["Stock"], prefix="/stock")


@router.get("/")
def get_all_stock(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    stocks = get_all_stocks_from_view(db)
    return {"data": [dict(stock._mapping) for stock in stocks]}


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


@router.get("/variant/size")
def get_variant_size(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    return {"data": get_all_stock_size(db)}


@router.get("/variant/type")
def get_variant_type(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    return {"data": get_all_stock_type(db)}


@router.get("/variant/color")
def get_variant_color(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    return {"data": get_all_stock_color(db)}


@router.post("/")
def post_new_stock(
    data: CreateNewStockRequest,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    # Validate if the combination of type, color, and size exists
    existing_stock = get_stock_by_variant_ids(
        db, data.type_id, data.size_id, data.color_id
    )
    if existing_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock with the given type, color, and size already exists.",
        )

    # Create the new stock
    new_stock = create_stock(db, data.type_id, data.size_id, data.color_id)
    return {"msg": "Stock created successfully", "data": {"stock_id": new_stock.id}}


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


@router.post("/update-quantity")
def update_stock_quantity(
    data: UpdateStockQuantityRequest,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    for stock_update in data.stocks:
        stock = get_stock_by_stock_id(db, stock_update.stock_id)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock with ID {stock_update.stock_id} not found.",
            )
        stock.quantity += stock_update.add_quantity
        db.commit()

    return {"msg": "Stock quantities updated successfully"}


@router.get("/type-from-stock")
def get_types_from_stock(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    # Authorize.jwt_required()
    types = (
        db.query(distinct(Stock_TM.stock_type_id), StockType_TR.type_name)
        .join(StockType_TR, Stock_TM.stock_type_id == StockType_TR.id)
        .order_by(Stock_TM.stock_type_id.asc())
        .all()
    )
    return {"data": [{"type_id": t[0], "type_name": t[1]} for t in types]}


@router.get("/color-from-stock")
def get_colors_from_stock(
    type_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    # Authorize.jwt_required()
    colors = (
        db.query(distinct(Stock_TM.stock_color_id), StockColor_TR.color_name)
        .join(StockColor_TR, Stock_TM.stock_color_id == StockColor_TR.id)
        .filter(Stock_TM.stock_type_id == type_id)
        .order_by(Stock_TM.stock_color_id.asc())
        .all()
    )
    return {"data": [{"color_id": c[0], "color_name": c[1]} for c in colors]}


@router.get("/size-from-stock")
def get_sizes_from_stock(
    type_id: int,
    color_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    # Authorize.jwt_required()
    sizes = (
        db.query(distinct(Stock_TM.stock_size_id), StockSize_TR.size_name)
        .join(StockSize_TR, Stock_TM.stock_size_id == StockSize_TR.id)
        .filter(Stock_TM.stock_type_id == type_id, Stock_TM.stock_color_id == color_id)
        .order_by(Stock_TM.stock_size_id.asc())
        .all()
    )
    return {"data": [{"size_id": s[0], "size_name": s[1]} for s in sizes]}
