from typing import Optional
from pydantic import BaseModel


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
    stock_size_id: int
    stock_type_id: int
    stock_color_id: int


class CreateNewVariantTypeRequest(BaseModel):
    type_name: str


class CreateNewVariantSizeRequest(BaseModel):
    size_name_start: str
    size_name_end: Optional[str]


class CreateNewVariantColorRequest(BaseModel):
    color_name: str
    color_hex: str
