from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, date, timedelta
from bson import ObjectId
from ..database import get_db
from ..models import ExpenseCreate, ExpenseUpdate, ExpenseOut, UserInDB
from ..deps import get_current_user

router = APIRouter(prefix="/expenses", tags=["Expenses"])

def date_to_dt(d: date) -> datetime:
    # store as UTC midnight
    return datetime(d.year, d.month, d.day)

def to_expense_out(doc) -> ExpenseOut:
    return ExpenseOut(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        title=doc["title"],
        amount=float(doc["amount"]),
        category=doc["category"],
        date=doc["date"].date(),
        notes=doc.get("notes"),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )

@router.post("", response_model=ExpenseOut, status_code=201)
async def create_expense(
    payload: ExpenseCreate,
    current_user: UserInDB = Depends(get_current_user),
):
    db = get_db()
    now = datetime.utcnow()
    doc = {
        "user_id": current_user.id,
        "title": payload.title.strip(),
        "amount": float(payload.amount),
        "category": payload.category,
        "date": date_to_dt(payload.date),
        "notes": payload.notes.strip() if payload.notes else None,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.expenses.insert_one(doc)
    doc["_id"] = result.inserted_id
    return to_expense_out(doc)

@router.get("", response_model=List[ExpenseOut])
async def list_expenses(
    current_user: UserInDB = Depends(get_current_user),
    category: Optional[str] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    skip: int = 0,
    limit: int = 100,
):
    db = get_db()
    q = {"user_id": current_user.id}
    if category:
        q["category"] = category
    if start_date or end_date:
        q["date"] = {}
        if start_date:
            q["date"]["$gte"] = date_to_dt(start_date)
        if end_date:
            # include the end date itself (next day exclusive)
            q["date"]["$lt"] = date_to_dt(end_date) + timedelta(days=1)

    cursor = db.expenses.find(q).sort("date", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [to_expense_out(d) for d in docs]

@router.get("/{expense_id}", response_model=ExpenseOut)
async def get_expense(expense_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    doc = await db.expenses.find_one({"_id": ObjectId(expense_id), "user_id": current_user.id})
    if not doc:
        raise HTTPException(status_code=404, detail="Expense not found")
    return to_expense_out(doc)

@router.put("/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    expense_id: str,
    payload: ExpenseUpdate,
    current_user: UserInDB = Depends(get_current_user),
):
    db = get_db()
    updates = {}
    if payload.title is not None:
        updates["title"] = payload.title.strip()
    if payload.amount is not None:
        updates["amount"] = float(payload.amount)
    if payload.category is not None:
        updates["category"] = payload.category
    if payload.date is not None:
        updates["date"] = date_to_dt(payload.date)
    if payload.notes is not None:
        updates["notes"] = payload.notes.strip() if payload.notes else None

    if not updates:
        doc = await db.expenses.find_one({"_id": ObjectId(expense_id), "user_id": current_user.id})
        if not doc:
            raise HTTPException(status_code=404, detail="Expense not found")
        return to_expense_out(doc)

    updates["updated_at"] = datetime.utcnow()
    result = await db.expenses.find_one_and_update(
        {"_id": ObjectId(expense_id), "user_id": current_user.id},
        {"$set": updates},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Expense not found")
    return to_expense_out(result)

@router.delete("/{expense_id}", status_code=204)
async def delete_expense(expense_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    res = await db.expenses.delete_one({"_id": ObjectId(expense_id), "user_id": current_user.id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return
