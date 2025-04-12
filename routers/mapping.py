from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import CategorizedProductMappingResponse
from core.db_utils import (
    get_product_mappings_with_stock_details,
    delete_product_mapping_by_id,
)

router = APIRouter(tags=["Mapping"], prefix="/mapping")


@router.get("/stock-mappings", response_model=list[CategorizedProductMappingResponse])
def list_stock_mappings(db: Session = Depends(get_db)):
    raw_mappings = get_product_mappings_with_stock_details(db)
    categorized_response = {}

    for mapping in raw_mappings:
        stock_id = mapping.stock_id
        if stock_id not in categorized_response:
            categorized_response[stock_id] = {
                "stock_id": stock_id,
                "stock_type": mapping.stock_type,
                "stock_color": mapping.stock_color,
                "stock_size": mapping.stock_size,
                "mappings": [],
            }
        categorized_response[stock_id]["mappings"].append(
            {
                "mapping_id": mapping.id,
                "ecom_code": mapping.ecom_code,
                "field1": mapping.field1,
                "field2": mapping.field2,
                "field3": mapping.field3,
                "field4": mapping.field4,
                "field5": mapping.field5,
            }
        )

    # Sort the result by stock_type, stock_color, and stock_size
    sorted_response = sorted(
        categorized_response.values(),
        key=lambda x: (x["stock_type"], x["stock_color"], x["stock_size"]),
    )

    # Sort the mappings inside each stock by ecom_code, field1, field2, ..., field5
    for stock in sorted_response:
        stock["mappings"] = sorted(
            stock["mappings"],
            key=lambda m: (
                m["ecom_code"],
                m["field1"] or "",
                m["field2"] or "",
                m["field3"] or "",
                m["field4"] or "",
                m["field5"] or "",
            ),
        )

    return sorted_response


@router.delete("/stock-mappings/{mapping_id}")
def delete_stock_mapping(mapping_id: int, db: Session = Depends(get_db)):
    success = delete_product_mapping_by_id(db, mapping_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping with ID {mapping_id} not found.",
        )
    return {"msg": f"Mapping with ID {mapping_id} successfully deleted."}
