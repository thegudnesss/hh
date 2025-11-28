from pydantic import BaseModel, Field

from typing import Union, Optional, List, Dict

from datetime import datetime



class User(BaseModel):
    _id: int
    id: int
    phone_number: Optional[str] = None
    is_premium: Optional[bool] = False
    balance: Optional[Union[int, float]] = 0
    referrer_id: Optional[int] = None
    referrals_count: Optional[int] = 0
    order_count: Optional[int] = 0
    savat: Optional[List[Dict[str, int]]] = Field(default_factory=list)

class Admin(BaseModel):
    _id: int
    id: int

class Categories(BaseModel):
    name: str
    photo: Optional[str] = None
    category_id: int
    products: List[int] = Field(default_factory=list)

class Products(BaseModel):
    id: int
    title: str
    description: str
    price: int
    photo: Optional[str] = None

class Order(BaseModel):
    order_id: int
    user_id: int
    products: List[Dict[str, int]]  # [{"product_id": 1, "count": 2}, ...]
    total_amount: float
    status: str = "pending"  # pending, paid, cancelled
    payment_method: Optional[str] = None  # click, payme
    created_at: Optional[datetime] = Field(default_factory=datetime.now)