from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Literal


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MenuCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=500)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    is_available: bool = True


class MenuUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    is_available: bool | None = None


class MenuResponse(MenuCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class OrderItemRequest(BaseModel):
    menu_item_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemRequest] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    menu_item_id: int
    name: str
    quantity: int
    unit_price: float
    subtotal: float


class OrderResponse(BaseModel):
    id: int
    total_amount: float
    status: str
    created_at: datetime
    items: list[OrderItemResponse]


class StatusUpdate(BaseModel):
    status: Literal["PENDING", "PREPARING", "READY", "COMPLETED"]
