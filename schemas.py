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
