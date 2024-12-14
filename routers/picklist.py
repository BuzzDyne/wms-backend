from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Query
from datetime import datetime
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
from schemas import (
    RepeatItemMappingRequest,
    SetItemMappingRequest,
    PicklistDashboardResponse,
)
from constant import XLS_FILE_FORMAT
from core.error_codes import ErrCode as E
from core.db_enums import PicklistTMStatus, PicklistItemTRIsExcluded
from core.db_utils import (
    get_picklist_by_id,
    set_picklist_status,
    get_picklistitems_by_picklist_id,
    update_stock_quantity_by_stock_id,
    get_picklistitem_by_id,
    copy_stock_id_by_picklistitem_object,
    get_all_product_mapping,
    get_stock_by_variant_ids,
    get_stock_by_stock_id,
    get_picklistfile_by_picklist_id,
    get_stock_size_name_by_id,
    get_stock_type_name_by_id,
    get_stock_color_name_by_id,
    get_picklistfile_by_id,
    get_picklistfile_by_picklist_id_and_ecom_code,
    get_stocktype_by_value,
    get_stocksize_by_value,
    get_stockcolor_by_name,
    create_stock,
    create_product_mapping,
    delete_picklistfile_by_picklist_id_and_ecom_code,
    delete_picklistfile_by_picklist_id,
    delete_picklistitems_by_picklistfile_id,
    delete_picklistfile_by_id,
    delete_picklistitems_by_picklist_id,
    set_is_excluded_picklistitem_by_id,
)
from core.utils import (
    validate_picklist_file,
    extract_picklist_item,
    map_picklistfile_ids,
)
from io import BytesIO

router = APIRouter(tags=["Picklist"], prefix="/picklist")


@router.get("/list_picklists")
def list_picklists(
    page: int = 1,
    size: int = 100,
    picklist_status: Optional[PicklistTMStatus] = Query(None),
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    user_id = Authorize.get_raw_jwt()["user_id"]

    query = db.query(Picklist_TM).order_by(Picklist_TM.draft_create_dt.desc())

    if picklist_status:
        query = query.filter(Picklist_TM.picklist_status == picklist_status)

    total = query.count()

    picklists = query.offset((page - 1) * size).limit(size).all()

    return {
        "msg": "Successfully listed picklists",
        "data": picklists,
        "page": page,
        "size": size,
        "total": total,
    }


@router.post("/")
def create_picklist(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    user_id = Authorize.get_raw_jwt()["user_id"]

    # Check if on draft picklist exists
    picklist = (
        db.query(Picklist_TM)
        .filter(Picklist_TM.picklist_status == PicklistTMStatus.ON_DRAFT)
        .all()
    )

    if picklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_NEW_E01),
        )

    # Add picklist to DB
    new_picklist = Picklist_TM(
        draft_create_dt=datetime.now(),
        picklist_status=PicklistTMStatus.ON_DRAFT,
    )

    db.add(new_picklist)
    db.commit()
    db.refresh(new_picklist)

    # TODO Logging

    return {"msg": f"Successfully created picklist!", "data": new_picklist}


@router.get("/{picklist_id}/dashboard", response_model=PicklistDashboardResponse)
def get_picklist_dashboard(
    picklist_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    user_id = Authorize.get_raw_jwt()["user_id"]

    # Fetch picklist files from the database
    picklist_files = get_picklistfile_by_picklist_id(db, picklist_id)

    file_ids = map_picklistfile_ids(picklist_files)

    # Fetch picklist items from the database
    picklist_items = get_picklistitems_by_picklist_id(db, picklist_id)

    # Aggregate stocks data
    stocks = []
    stock_map = {}
    unmapped_items = []

    for item in picklist_items:
        stock = get_stock_by_stock_id(db, item.stock_id)
        if not stock:
            unmapped_items.append(
                {
                    "item_id": item.id,
                    "item_name": item.product_name,
                    "ecom_code": item.ecom_code,
                    "is_excluded": item.is_excluded,
                }
            )
            continue

        stock_key = (stock.stock_type_id, stock.stock_color_id, stock.stock_size_id)
        if stock_key not in stock_map:
            stock_map[stock_key] = {
                "stock_id": stock.id,
                "product_type": get_stock_type_name_by_id(db, stock.stock_type_id),
                "product_color": get_stock_color_name_by_id(db, stock.stock_color_id),
                "product_size": get_stock_size_name_by_id(db, stock.stock_size_id),
                "count": 0,
                "items": {},
            }
            stocks.append(stock_map[stock_key])

        if not item.is_excluded:
            stock_map[stock_key]["count"] += 1

        platform = item.ecom_code
        if platform not in stock_map[stock_key]["items"]:
            stock_map[stock_key]["items"][platform] = []

        stock_map[stock_key]["items"][platform].append(
            {
                "item_id": item.id,
                "item_name": item.product_name,
                "is_excluded": item.is_excluded,
                "ecom_order_id": item.ecom_order_id,
            }
        )

    # Sort the stocks by product_type, product_color, and product_size
    sorted_stocks = sorted(
        stocks, key=lambda s: (s["product_type"], s["product_color"], s["product_size"])
    )

    # Construct the response
    res = PicklistDashboardResponse(
        tik_file_id=file_ids["tik_file_id"],
        tok_file_id=file_ids["tok_file_id"],
        sho_file_id=file_ids["sho_file_id"],
        laz_file_id=file_ids["laz_file_id"],
        stocks=sorted_stocks,
        unmapped_items=unmapped_items,
    )

    # TODO Logging

    return res


@router.put("/{picklist_id}/picklistitem/{item_id}/exclude")
def exclude_picklistitem(
    picklist_id: int,
    item_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    return update_picklistitem_status(
        db, picklist_id, item_id, PicklistItemTRIsExcluded.EXCLUDED
    )


@router.put("/{picklist_id}/picklistitem/{item_id}/include")
def include_picklistitem(
    picklist_id: int,
    item_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    return update_picklistitem_status(
        db, picklist_id, item_id, PicklistItemTRIsExcluded.INCLUDED
    )


@router.delete("/{picklist_id}/file/id/{file_id}")
def delete_file_by_id(
    picklist_id: int,
    file_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    user_id = Authorize.get_raw_jwt()["user_id"]

    db_picklist = get_picklist_by_id(db, picklist_id)

    if not db_picklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_DFI_E01),
        )

    db_file = get_picklistfile_by_id(db, file_id)

    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_DFI_E02),
        )

    if db_file.picklist_id != db_picklist.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_DFI_E03),
        )

    delete_picklistitems_by_picklistfile_id(db, db_file.id)
    delete_picklistfile_by_id(db, db_file.id)

    return {"msg": f"Successfully delete picklistfile (ID: {file_id})!"}


@router.delete("/{picklist_id}/file")
def delete_file_by_picklist_id(
    picklist_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    user_id = Authorize.get_raw_jwt()["user_id"]

    db_picklist = get_picklist_by_id(db, picklist_id)

    if not db_picklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_DFI_E01),  # TODO Fix ErroCode
        )

    db_file = get_picklistfile_by_picklist_id(db, picklist_id)

    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_DFI_E04),  # TODO Fix ErroCode
        )

    delete_picklistitems_by_picklist_id(db, picklist_id)
    delete_picklistfile_by_picklist_id(db, picklist_id)

    return {
        "msg": f"Successfully delete all item and file (PicklistID: {picklist_id})!"
    }


@router.delete("/{picklist_id}/file/ecom_code/{ecom_code}")
def delete_file_by_ecom_code(
    picklist_id: int,
    ecom_code: str,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    user_id = Authorize.get_raw_jwt()["user_id"]

    db_picklist = get_picklist_by_id(db, picklist_id)

    if not db_picklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_DFI_E01),
        )

    db_file = get_picklistfile_by_picklist_id_and_ecom_code(db, picklist_id, ecom_code)

    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_DFI_E04),
        )

    delete_picklistitems_by_picklistfile_id(db, db_file.id)
    delete_picklistfile_by_id(db, db_file.id)

    return {"msg": f"Successfully delete picklistfile (ID: {db_file.id})!"}


@router.post("/{picklist_id}/update/cancelled")
async def cancel_draft(
    picklist_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    user_id = Authorize.get_raw_jwt()["user_id"]

    db_picklist = get_picklist_by_id(db, picklist_id)

    if not db_picklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_CCL_E01),
        )

    # Validation
    if db_picklist.picklist_status != PicklistTMStatus.ON_DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(
                E.PIC_CCL_E02, db_picklist.picklist_status, PicklistTMStatus.ON_DRAFT
            ),
        )

    # Set Status
    set_picklist_status(db, db_picklist, PicklistTMStatus.CANCELLED)

    # TODO Logging

    return {"msg": "Cancel successful"}


@router.post("/{picklist_id}/update/created")
async def finish_draft(
    picklist_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    user_id = Authorize.get_raw_jwt()["user_id"]

    db_picklist = get_picklist_by_id(db, picklist_id)

    if not db_picklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_FIN_E01),
        )

    # Validation
    if db_picklist.picklist_status != PicklistTMStatus.ON_DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(
                E.PIC_FIN_E02, db_picklist.picklist_status, PicklistTMStatus.ON_DRAFT
            ),
        )

    items_arr = get_picklistitems_by_picklist_id(db, db_picklist.id)

    if not items_arr:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_FIN_E03),
        )

    # Check if all picklistitem has stock_id
    for item in items_arr:
        if (
            item.stock_id is None
            and item.is_excluded == PicklistItemTRIsExcluded.INCLUDED
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=E.format_error(E.PIC_FIN_E04),
            )

    # Set Status
    set_picklist_status(db, db_picklist, PicklistTMStatus.CREATED)

    # TODO Use Returned Items Flow
    # TODO Logging

    return {"msg": "Finished Draft successful"}


@router.post("/{picklist_id}/repeat-item-mapping")
async def repeat_item_mapping(
    picklist_id: int,
    data: RepeatItemMappingRequest,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    db_picklist = get_picklist_by_id(db, picklist_id)

    if not db_picklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_REM_E01),
        )

    # If mapped item id given, copy from that
    if data.mapped_picklistitem_id:
        item = get_picklistitem_by_id(db, data.mapped_picklistitem_id)

        if item.picklist_id != picklist_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=E.format_error(
                    E.PIC_REM_E02,
                    data.mapped_picklistitem_id,
                    item.picklist_id,
                    picklist_id,
                ),
            )

        copy_stock_id_by_picklistitem_object(db, item)

        return {
            "msg": f"Successfully applied stock mapping from picklistitem id ({data.mapped_picklistitem_id}) to other similar picklistitem under the same picklist id!",
        }
    else:  # check item against all mapping
        # Get All Items which belong to this PicklistID
        items = get_picklistitems_by_picklist_id(db, picklist_id)

        # Get all mappings
        mappings = get_all_product_mapping(db)

        # Create a lookup dictionary for stock_id
        mapping_lookup = {
            (row.field1, row.field2, row.field3, row.field4, row.field5): row.stock_id
            for row in mappings
        }

        for item in items:
            stock_key = (
                item.field1,
                item.field2,
                item.field3,
                item.field4,
                item.field5,
            )
            item.stock_id = mapping_lookup.get(stock_key)

        db.commit()

        return {"msg": "Successfully processed Picklist File!"}


@router.post("/{picklist_id}/update/on-picking")
async def set_on_picking(
    picklist_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    user_id = Authorize.get_raw_jwt()["user_id"]

    db_picklist = get_picklist_by_id(db, picklist_id)

    if not db_picklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_OPI_E01),
        )

    # Validation
    if db_picklist.picklist_status != PicklistTMStatus.CREATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(
                E.PIC_OPI_E02, db_picklist.picklist_status, PicklistTMStatus.CREATED
            ),
        )

    # Set Status
    set_picklist_status(db, db_picklist, PicklistTMStatus.ON_PICKING)

    # TODO Use Returned Items Flow
    # TODO Logging

    return {"msg": "Draft set to OnPicking successfully"}


@router.post("/{picklist_id}/update/complete-draft")
async def complete_draft(
    picklist_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    user_id = Authorize.get_raw_jwt()["user_id"]

    db_picklist = get_picklist_by_id(db, picklist_id)

    if not db_picklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_OPI_E01),
        )

    # Validation
    if db_picklist.picklist_status != PicklistTMStatus.ON_PICKING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(
                E.PIC_FIN_E02, db_picklist.picklist_status, PicklistTMStatus.ON_PICKING
            ),
        )

    # Reduce Stock Quantity based on Picklist Item
    items_arr = get_picklistitems_by_picklist_id(db, db_picklist.id)
    stock_updates = {}

    # Group items by stock_id and count how many times each stock_id appears
    for item in items_arr:
        if item.is_excluded == PicklistItemTRIsExcluded.INCLUDED:
            stock_updates[item.stock_id] = stock_updates.get(item.stock_id, 0) + 1

    # Update stock quantities in bulk
    for stock_id, count in stock_updates.items():
        update_stock_quantity_by_stock_id(db, stock_id, count)

    # Set Status
    set_picklist_status(db, db_picklist, PicklistTMStatus.COMPLETED)

    # TODO Logging

    return {"msg": "Picklist completed successfully"}


@router.post("/{picklist_id}/upload/{ecom_code}")
async def upload(
    picklist_id: int,
    ecom_code: str,
    file: UploadFile,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    if file.content_type != XLS_FILE_FORMAT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only XLSX files are allowed.",
        )

    file_content = await file.read()
    workbook = load_workbook(filename=BytesIO(file_content))

    sheet = validate_picklist_file(workbook, ecom_code)
    items = extract_picklist_item(sheet, ecom_code, picklist_id)

    # region Save File
    new_picklistfile = PicklistFile_TR(
        ecom_code=ecom_code,
        file_data=file_content,
        file_name=file.filename,
        picklist_id=picklist_id,
        upload_dt=datetime.now(),
    )

    db.add(new_picklistfile)
    db.commit()
    db.refresh(new_picklistfile)
    # endregion

    # Fetch all relevant product mappings for the ecom_code
    product_mappings = (
        db.query(
            ProductMapping_TR.field1,
            ProductMapping_TR.field2,
            ProductMapping_TR.field3,
            ProductMapping_TR.field4,
            ProductMapping_TR.field5,
            ProductMapping_TR.stock_id,
        )
        .filter(ProductMapping_TR.ecom_code == ecom_code)
        .all()
    )

    # Create a lookup dictionary for stock_id
    stock_lookup = {
        (row.field1, row.field2, row.field3, row.field4, row.field5): row.stock_id
        for row in product_mappings
    }

    # Assign stock_id and picklistfile_id to each item
    picklistfile_id = new_picklistfile.id

    for item in items:
        stock_key = (
            item["field1"],
            item["field2"],
            item["field3"],
            item["field4"],
            item["field5"],
        )
        item["stock_id"] = stock_lookup.get(stock_key)
        item["picklistfile_id"] = picklistfile_id

    # Bulk insert the items into the PicklistItem_TR table
    db.bulk_insert_mappings(PicklistItem_TR, items)
    db.commit()

    workbook.close()

    return {"msg": "Successfully processed Picklist File!", "data": items}


@router.post("/item/{picklistitem_id}/set-mapping")
async def set_item_mapping(
    picklistitem_id: int,
    data: SetItemMappingRequest,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    user_id = Authorize.get_raw_jwt()["user_id"]

    item = get_picklistitem_by_id(db, picklistitem_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_SEM_E01),
        )

    # Get Variants from DB
    type_db = get_stocktype_by_value(db, data.stock_type_value)
    size_db = get_stocksize_by_value(db, data.stock_size_value)
    color_db = get_stockcolor_by_name(db, data.stock_color_name)

    if not (type_db and size_db and color_db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_SEM_E02),
        )

    # Get Stock
    stock_db = get_stock_by_variant_ids(db, type_db.id, size_db.id, color_db.id)

    if not stock_db:
        stock_db = create_stock(db, type_db.id, size_db.id, color_db.id)

    # Insert New ProductMapping
    mapping_db = create_product_mapping(db, item, stock_db.id)

    item.stock_id = stock_db.id
    db.commit()

    # TODO Logging

    return {
        "msg": f"PicklistItem (ID {item.id}) stock_id updated to stock (ID {stock_db.id}) successfully. (Mapping ID {mapping_db.id})"
    }


def update_picklistitem_status(
    db: Session, picklist_id: int, item_id: int, is_excluded: str
):
    db_picklist = get_picklist_by_id(db, picklist_id)

    if not db_picklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_DIT_E01),
        )

    db_item = get_picklistitem_by_id(db, item_id)

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_DFI_E02),
        )

    if db_item.picklist_id != db_picklist.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_DFI_E03),
        )

    set_is_excluded_picklistitem_by_id(db, db_item.id, is_excluded)

    return {
        "msg": f"Successfully updated picklistitem (ID: {item_id}) to {is_excluded}!"
    }
