from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, Literal
from datetime import datetime, date as Date
from bson import ObjectId


# ----- Helpers to work with Mongo ObjectId -----
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, *args, **kwargs):
        # Pydantic v2 adapter
        from pydantic_core import core_schema

        def validate(v):
            if isinstance(v, ObjectId):
                return v
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            return ObjectId(v)

        return core_schema.no_info_after_validator_function(
            validate, core_schema.str_schema()
        )


def to_object_id(id_str: str) -> ObjectId:
    return ObjectId(id_str)


# ----- Enums / constants -----
Category = Literal["Food", "Travel", "Bills", "Shopping", "Others"]


# ----- Users -----
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Internal user persisted form (not exposed)
class UserInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    full_name: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ----- Expenses -----
class ExpenseBase(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    amount: float = Field(gt=0)
    category: Category
    date: Date  # ✅ fixed: use Date alias
    notes: Optional[str] = Field(default=None, max_length=500)


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    amount: Optional[float] = Field(default=None, gt=0)
    category: Optional[Category] = None
    date: Optional[Date] = None  # ✅ fixed
    notes: Optional[str] = Field(default=None, max_length=500)


class ExpenseOut(ExpenseBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
