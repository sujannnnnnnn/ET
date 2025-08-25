from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from datetime import datetime
from ..deps import get_current_user
from ..models import UserInDB
from ..database import get_db

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/monthly")
async def monthly_report(
    year: int = Query(..., ge=1970, le=9999),
    month: int = Query(..., ge=1, le=12),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Returns:
    {
      "year": 2025,
      "month": 8,
      "total": 1234.5,
      "byCategory": {"Food": 100, "Travel": 200, ...},
      "count": 17
    }
    """
    db = get_db()
    from datetime import date, timedelta

    start = datetime(year, month, 1)
    # compute next month start
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)

    pipeline = [
        {"$match": {"user_id": current_user.id, "date": {"$gte": start, "$lt": next_month}}},
        {"$group": {"_id": "$category", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
    ]
    agg = await db.expenses.aggregate(pipeline).to_list(length=100)

    by_category = {doc["_id"]: float(doc["total"]) for doc in agg}
    cnt = sum(int(doc["count"]) for doc in agg)
    total = sum(float(doc["total"]) for doc in agg)

    return {
        "year": year,
        "month": month,
        "total": float(total),
        "byCategory": by_category,
        "count": cnt,
    }
