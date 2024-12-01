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
from constant import XLS_FILE_FORMAT, PicklistStatus
from core.error_codes import ErrCode
from core.utils import validate_picklist_file, extract_picklist_item
from io import BytesIO

router = APIRouter(tags=["Picklist"], prefix="/picklist")


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
        .filter(Picklist_TM.picklist_status == PicklistStatus.ON_DRAFT)
        .all()
    )

    if picklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrCode.get(ErrCode.PIC_NEW_E01),
        )

    # Add picklist to DB
    new_picklist = Picklist_TM(
        draft_create_dt=datetime.now(),
        picklist_status=PicklistStatus.ON_DRAFT,
        creator_id=user_id,
    )

    db.add(new_picklist)
    db.commit()
    db.refresh(new_picklist)

    return {"msg": f"Successfully created picklist!", "data": new_picklist}


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
    orders = extract_picklist_item(sheet, ecom_code, picklist_id)

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

    # Assign stock_id and picklistfile_id to each order
    picklistfile_id = new_picklistfile.id

    for order in orders:
        stock_key = (
            order["field1"],
            order["field2"],
            order["field3"],
            order["field4"],
            order["field5"],
        )
        order["stock_id"] = stock_lookup.get(stock_key)
        order["picklistfile_id"] = picklistfile_id

    # Bulk insert the orders into the PicklistItem_TR table
    db.bulk_insert_mappings(PicklistItem_TR, orders)
    db.commit()

    workbook.close()

    return {"orders": orders}
