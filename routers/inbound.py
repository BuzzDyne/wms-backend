from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.exc import NoResultFound
from database import (
    get_db,
    MasterParameter_TM,
    InboundSchedule_TM,
    Inbound_TM,
    InboundItems_TR,
    Stock_TM,
    StockType_TR,
    StockColor_TR,
    StockSize_TR,
)
from schemas import (
    InboundSchedule,
    CreateScheduleRequest,
    CreateInboundRequest,
    AddInboundItemRequest,
)
from datetime import datetime
from core.db_utils import get_stock_by_stock_id

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


# prefix="/inbound"
@router.get("/")
def list_inbounds(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    inbounds = db.query(Inbound_TM).order_by(Inbound_TM.created_at.desc()).all()
    return {
        "data": [
            {
                "id": inbound.id,
                "status": inbound.status,
                "supplier_name": inbound.supplier_name,
                "notes": inbound.notes,
                "created_at": inbound.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": inbound.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": inbound.user_id,
            }
            for inbound in inbounds
        ]
    }


@router.post("/")
def create_inbound(
    data: CreateInboundRequest,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    # Check if inbound is active
    parameter = (
        db.query(MasterParameter_TM)
        .filter_by(parameter_name="inbound_active")
        .one_or_none()
    )
    if not parameter:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System configuration for inbound_active is missing.",
        )

    if parameter.parameter_value_int == 1:
        # Check if today's date matches any active schedule in InboundSchedule_TM
        today_date = datetime.now().strftime("%Y%m%d")
        schedule = (
            db.query(InboundSchedule_TM)
            .filter(
                InboundSchedule_TM.schedule_date == today_date,
                InboundSchedule_TM.is_active == 1,
            )
            .first()
        )
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inbound creation is not allowed. No active schedule matches today's date.",
            )

    # Proceed with inbound creation
    new_inbound = Inbound_TM(
        status="PENDING",
        supplier_name=data.supplier_name,
        notes=data.notes,
        user_id=Authorize.get_raw_jwt()["user_id"],
    )
    db.add(new_inbound)
    db.commit()
    db.refresh(new_inbound)
    return {
        "msg": "Inbound created successfully",
        "data": {"inbound_id": new_inbound.id},
    }


@router.post("/{inbound_id}/items")
def add_inbound_item(
    inbound_id: int,
    data: AddInboundItemRequest,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    inbound = db.query(Inbound_TM).filter_by(id=inbound_id).first()
    if not inbound or inbound.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inbound not found or not in PENDING status.",
        )

    # Validate if the combination of type, color, and size exists in Stock table
    stock = (
        db.query(Stock_TM)
        .filter_by(
            stock_type_id=data.type_id,
            stock_color_id=data.color_id,
            stock_size_id=data.size_id,
        )
        .first()
    )
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock with the given type, color, and size combination not found.",
        )

    new_item = InboundItems_TR(
        inbound_id=inbound_id,
        stock_id=stock.id,
        add_quantity=data.add_quantity,
    )
    db.add(new_item)
    db.commit()
    return {"msg": "Inbound item added successfully"}


@router.post("/{inbound_id}/submit")
def submit_inbound(
    inbound_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    inbound = db.query(Inbound_TM).filter_by(id=inbound_id).first()
    if not inbound or inbound.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inbound not found or not in PENDING status.",
        )

    items = db.query(InboundItems_TR).filter_by(inbound_id=inbound_id).all()
    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No items found for this inbound.",
        )

    for item in items:
        stock = get_stock_by_stock_id(db, item.stock_id)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock with ID {item.stock_id} not found.",
            )
        stock.quantity += item.add_quantity

    inbound.status = "COMPLETED"
    db.commit()
    return {"msg": "Inbound submitted successfully"}


@router.delete("/{inbound_id}")
def cancel_inbound(
    inbound_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    inbound = db.query(Inbound_TM).filter_by(id=inbound_id).first()
    if not inbound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inbound not found.",
        )

    db.query(InboundItems_TR).filter_by(inbound_id=inbound_id).delete()
    db.delete(inbound)
    db.commit()
    return {"msg": "Inbound canceled successfully"}


@router.get("/{inbound_id}")
def get_inbound_details(
    inbound_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    inbound = db.query(Inbound_TM).filter_by(id=inbound_id).first()
    if not inbound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inbound not found.",
        )

    items = (
        db.query(
            InboundItems_TR.id,
            InboundItems_TR.stock_id,
            Stock_TM.stock_type_id,
            StockType_TR.type_name,
            Stock_TM.stock_color_id,
            StockColor_TR.color_name,
            Stock_TM.stock_size_id,
            StockSize_TR.size_name,
            InboundItems_TR.add_quantity,
            InboundItems_TR.created_at,
            InboundItems_TR.updated_at,
        )
        .join(Stock_TM, InboundItems_TR.stock_id == Stock_TM.id)
        .join(StockType_TR, Stock_TM.stock_type_id == StockType_TR.id)
        .join(StockColor_TR, Stock_TM.stock_color_id == StockColor_TR.id)
        .join(StockSize_TR, Stock_TM.stock_size_id == StockSize_TR.id)
        .filter(InboundItems_TR.inbound_id == inbound_id)
        .all()
    )

    return {
        "inbound": {
            "id": inbound.id,
            "status": inbound.status,
            "supplier_name": inbound.supplier_name,
            "notes": inbound.notes,
            "created_at": inbound.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": inbound.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": inbound.user_id,
        },
        "items": [
            {
                "id": item.id,
                "stock_id": item.stock_id,
                "type_id": item.stock_type_id,
                "type_name": item.type_name,
                "color_id": item.stock_color_id,
                "color_name": item.color_name,
                "size_id": item.stock_size_id,
                "size_name": item.size_name,
                "add_quantity": item.add_quantity,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": item.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for item in items
        ],
    }


@router.delete("/items/{inbound_item_id}")
def delete_inbound_item(
    inbound_item_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    inbound_item = db.query(InboundItems_TR).filter_by(id=inbound_item_id).first()
    if not inbound_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inbound item not found.",
        )

    db.delete(inbound_item)
    db.commit()
    return {"msg": "Inbound item deleted successfully"}
