from sqlalchemy.orm import Session
from core.db_enums import PicklistTMStatus, StockTMIsActive
from database import (
    Picklist_TM,
    PicklistFile_TR,
    PicklistItem_TR,
    Stock_TM,
    StockType_TR,
    StockSize_TR,
    StockColor_TR,
    ProductMapping_TR,
)

from datetime import datetime
from sqlalchemy import text


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


# region PicklistFileTR
def get_picklistfile_by_id(db: Session, file_id: int):
    return db.query(PicklistFile_TR).filter(PicklistFile_TR.id == file_id).first()


def get_picklistfile_by_picklist_id(db: Session, picklist_id: int):
    return (
        db.query(PicklistFile_TR)
        .filter(PicklistFile_TR.picklist_id == picklist_id)
        .all()
    )


def get_picklistfile_by_picklist_id_and_ecom_code(
    db: Session, picklist_id: int, ecom_code: str
):
    return (
        db.query(PicklistFile_TR)
        .filter(
            PicklistFile_TR.picklist_id == picklist_id,
            PicklistFile_TR.ecom_code == ecom_code,
        )
        .first()
    )


def delete_picklistfile_by_id(db: Session, file_id: int):
    picklist_file = (
        db.query(PicklistFile_TR).filter(PicklistFile_TR.id == file_id).first()
    )
    # If found, delete it
    if picklist_file:
        db.delete(picklist_file)
        db.commit()


def delete_picklistfile_by_picklist_id(db: Session, picklist_id: int):
    picklist_files = (
        db.query(PicklistFile_TR)
        .filter(PicklistFile_TR.picklist_id == picklist_id)
        .all()
    )
    # If found, delete them
    if picklist_files:
        for picklist_file in picklist_files:
            db.delete(picklist_file)
        db.commit()


def delete_picklistfile_by_picklist_id_and_ecom_code(
    db: Session, picklist_id: int, ecom_code: str
):
    picklist_file = (
        db.query(PicklistFile_TR)
        .filter(
            PicklistFile_TR.picklist_id == picklist_id,
            PicklistFile_TR.ecom_code == ecom_code,
        )
        .first()
    )
    # If found, delete it
    if picklist_file:
        db.delete(picklist_file)
        db.commit()


# endregion


# region PicklistItemTR
def get_picklistitems_by_picklist_id(db: Session, picklist_id: int):
    return (
        db.query(PicklistItem_TR)
        .filter(PicklistItem_TR.picklist_id == picklist_id)
        .all()
    )


def get_picklistitem_by_id(db: Session, picklistitem_id: int):
    return (
        db.query(PicklistItem_TR).filter(PicklistItem_TR.id == picklistitem_id).first()
    )


def set_is_excluded_picklistitem_by_id(
    db: Session, picklistitem_id: int, exclude_flag: int
):
    picklist_item = (
        db.query(PicklistItem_TR).filter(PicklistItem_TR.id == picklistitem_id).first()
    )
    # If found, delete all picklist items
    if picklist_item:
        picklist_item.is_excluded = exclude_flag
        db.commit()


def delete_picklistitems_by_picklistfile_id(db: Session, picklistfile_id: int):
    picklist_items = (
        db.query(PicklistItem_TR)
        .filter(PicklistItem_TR.picklistfile_id == picklistfile_id)
        .all()
    )
    # If found, delete all picklist items
    if picklist_items:
        for item in picklist_items:
            db.delete(item)
        db.commit()


def delete_picklistitems_by_picklist_id(db: Session, picklist_id: int):
    picklist_items = (
        db.query(PicklistItem_TR)
        .filter(PicklistItem_TR.picklist_id == picklist_id)
        .all()
    )
    # If found, delete all picklist items
    if picklist_items:
        for item in picklist_items:
            db.delete(item)
        db.commit()


def copy_stock_id_by_picklistitem_object(db: Session, picklistitem: PicklistItem_TR):
    matching_items = (
        db.query(PicklistItem_TR)
        .filter(
            PicklistItem_TR.ecom_code == picklistitem.ecom_code,
            PicklistItem_TR.field1 == picklistitem.field1,
            PicklistItem_TR.field2 == picklistitem.field2,
            PicklistItem_TR.field3 == picklistitem.field3,
            PicklistItem_TR.field4 == picklistitem.field4,
            PicklistItem_TR.field5 == picklistitem.field5,
            PicklistItem_TR.picklist_id == picklistitem.picklist_id,
            PicklistItem_TR.id != picklistitem.id,
        )
        .all()
    )

    # Update the stock_id for all matching items
    for item in matching_items:
        item.stock_id = picklistitem.stock_id

    # Commit the changes to the database
    db.commit()

    return matching_items


# endregion


# region StockTM
def get_stocks(db: Session):
    results = (
        db.query(
            Stock_TM.id.label("stock_id"),
            Stock_TM.stock_type_id,
            StockType_TR.type_name,
            Stock_TM.stock_size_id,
            StockSize_TR.size_name,
            Stock_TM.stock_color_id,
            StockColor_TR.color_name,
            Stock_TM.quantity.label("quantity"),
            Stock_TM.is_active.label("is_active"),
        )
        .join(StockType_TR, Stock_TM.stock_type_id == StockType_TR.id)
        .join(StockSize_TR, Stock_TM.stock_size_id == StockSize_TR.id)
        .join(StockColor_TR, Stock_TM.stock_color_id == StockColor_TR.id)
        .filter(Stock_TM.is_active == StockTMIsActive.ACTIVE)
        .all()
    )

    # Convert result to list of dictionaries
    stocks = []
    for result in results:
        stock = {
            "stock_id": result.stock_id,
            "stock_type_id": result.stock_type_id,
            "type_name": result.type_name,
            "stock_size_id": result.stock_size_id,
            "size_name": result.size_name,
            "stock_color_id": result.stock_color_id,
            "color_name": result.color_name,
            "quantity": result.quantity,
            "is_active": result.is_active,
        }
        stocks.append(stock)

    return stocks


def get_stock_by_stock_id(db: Session, stock_id: int):
    return db.query(Stock_TM).filter(Stock_TM.id == stock_id).first()


def get_stock_by_variant_ids(db: Session, type_id: int, size_id: int, color_id: int):
    return (
        db.query(Stock_TM)
        .filter(
            Stock_TM.stock_type_id == type_id,
            Stock_TM.stock_size_id == size_id,
            Stock_TM.stock_color_id == color_id,
        )
        .first()
    )


def update_stock_quantity_by_stock_id(db: Session, stock_id: int, count: int):
    stock = get_stock_by_stock_id(db, stock_id)
    stock.quantity -= count
    db.commit()


def get_all_stock_size(db: Session):
    return db.query(StockSize_TR).order_by(StockSize_TR.size_name.asc()).all()


def get_stock_size_name_by_id(db: Session, size_id: int):
    return db.query(StockSize_TR).filter(StockSize_TR.id == size_id).first().size_name


def get_all_stock_type(db: Session):
    return db.query(StockType_TR).order_by(StockType_TR.type_name.asc()).all()


def get_stock_type_name_by_id(db: Session, type_id: int):
    return db.query(StockType_TR).filter(StockType_TR.id == type_id).first().type_name


def get_all_stock_color(db: Session):
    return db.query(StockColor_TR).order_by(StockColor_TR.color_name.asc()).all()


def get_stock_color_name_by_id(db: Session, color_id: int):
    return (
        db.query(StockColor_TR).filter(StockColor_TR.id == color_id).first().color_name
    )


def create_stock(db: Session, type_id: int, size_id: int, color_id: int):
    new_stock = Stock_TM(
        stock_type_id=type_id,
        stock_size_id=size_id,
        stock_color_id=color_id,
    )

    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)

    return new_stock


def get_all_stocks_from_view(db: Session):
    query = text(
        """
        SELECT * FROM stock_view
        ORDER BY stock_type_id ASC, stock_color_id ASC, stock_size_id ASC
    """
    )
    return db.execute(query).fetchall()


# endregion


# region StockTypeTR
def get_stocktype_by_value(db: Session, type_value: str):
    return db.query(StockType_TR).filter(StockType_TR.type_value == type_value).first()


def create_stocktype(db: Session, type_value: str, type_name: str):
    new_stocktype = StockType_TR(
        type_value=type_value,
        type_name=type_name,
    )

    db.add(new_stocktype)
    db.commit()
    db.refresh(new_stocktype)

    return new_stocktype


# endregion


# region StockSizeTR
def get_stocksize_by_value(db: Session, size_value: str):
    return db.query(StockSize_TR).filter(StockSize_TR.size_value == size_value).first()


def create_stocksize(db: Session, size_value: str, size_name: str):
    new_stocksize = StockSize_TR(
        size_value=size_value,
        size_name=size_name,
    )

    db.add(new_stocksize)
    db.commit()
    db.refresh(new_stocksize)

    return new_stocksize


# endregion


# region StockColorTR
def get_stockcolor_by_name(db: Session, color_name: str):
    return (
        db.query(StockColor_TR).filter(StockColor_TR.color_name == color_name).first()
    )


def create_stockcolor(db: Session, color_name: str, color_hex: str):
    new_stockcolor = StockColor_TR(
        color_name=color_name,
        color_hex=color_hex,
    )

    db.add(new_stockcolor)
    db.commit()
    db.refresh(new_stockcolor)

    return new_stockcolor


# endregion


# region ProductMappingTR
def get_all_product_mapping(db: Session):
    return db.query(ProductMapping_TR).all()


def get_product_mapping_by_id(db: Session, mapping_id: int):
    return (
        db.query(ProductMapping_TR).filter(ProductMapping_TR.id == mapping_id).first()
    )


def create_product_mapping(db: Session, item: PicklistItem_TR, stock_id: int):
    new_mapping = ProductMapping_TR(
        ecom_code=item.ecom_code,
        field1=item.field1,
        field2=item.field2,
        field3=item.field3,
        field4=item.field4,
        field5=item.field5,
        stock_id=stock_id,
    )

    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)

    return new_mapping


def get_product_mappings_with_stock_details(db: Session):
    return (
        db.query(
            ProductMapping_TR.id,
            ProductMapping_TR.ecom_code,
            ProductMapping_TR.field1,
            ProductMapping_TR.field2,
            ProductMapping_TR.field3,
            ProductMapping_TR.field4,
            ProductMapping_TR.field5,
            ProductMapping_TR.stock_id,
            StockType_TR.type_name.label("stock_type"),
            StockColor_TR.color_name.label("stock_color"),
            StockSize_TR.size_name.label("stock_size"),
        )
        .join(Stock_TM, ProductMapping_TR.stock_id == Stock_TM.id)
        .join(StockType_TR, Stock_TM.stock_type_id == StockType_TR.id)
        .join(StockSize_TR, Stock_TM.stock_size_id == StockSize_TR.id)
        .join(StockColor_TR, Stock_TM.stock_color_id == StockColor_TR.id)
        .all()
    )


def delete_product_mapping_by_id(db: Session, mapping_id: int) -> bool:
    mapping = (
        db.query(ProductMapping_TR).filter(ProductMapping_TR.id == mapping_id).first()
    )
    if not mapping:
        return False
    db.delete(mapping)
    db.commit()
    return True


# endregion
