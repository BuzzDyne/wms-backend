from typing import List, Optional, Dict
from pydantic import BaseModel


# Picklist


class Item(BaseModel):
    item_id: int
    item_name: str
    is_excluded: int


class UnmappedItem(BaseModel):
    item_id: int
    item_name: str
    ecom_code: str
    is_excluded: int


class Stock(BaseModel):
    stock_id: int
    product_type: str
    product_color: str
    product_size: str
    count: int
    items: Dict[str, List[Item]]  # Dictionary to map platforms to lists of items


class PicklistDashboardResponse(BaseModel):
    tik_file_id: Optional[int]
    tok_file_id: Optional[int]
    sho_file_id: Optional[int]
    laz_file_id: Optional[int]
    stocks: List[Stock]
    unmapped_items: List[UnmappedItem]


# User Table
class User(BaseModel):
    id: Optional[int]
    created_dt: Optional[str]
    last_login_dt: Optional[str]
    role: Optional[str]
    username: Optional[str]
    password: Optional[str]

    class Config:
        orm_mode = True


class LoginForm(BaseModel):
    username: str
    password: str


class RegisterForm(BaseModel):
    username: str
    password: str
    rolename: str


class RepeatItemMappingRequest(BaseModel):
    mapped_picklistitem_id: Optional[int]


class SetItemMappingRequest(BaseModel):
    stock_size_value: str
    stock_type_value: str
    stock_color_name: str


class CreateNewVariantTypeRequest(BaseModel):
    type_name: str


class CreateNewVariantSizeRequest(BaseModel):
    size_name_start: str
    size_name_end: Optional[str]


class CreateNewVariantColorRequest(BaseModel):
    color_name: str
    color_hex: str
