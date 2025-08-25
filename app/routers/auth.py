from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime
from ..database import get_db
from ..models import UserCreate, UserPublic, UserInDB
from ..auth import get_password_hash, verify_password, create_access_token
from ..deps import get_current_user  # ✅ import directly from deps

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=UserPublic, status_code=201)
async def signup(payload: UserCreate):
    db = get_db()
    exists = await db.users.find_one({"email": payload.email})
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    doc = {
        "email": payload.email.lower(),
        "full_name": payload.full_name.strip(),
        "password_hash": get_password_hash(payload.password),
        "created_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(doc)
    user = UserPublic(
        id=str(result.inserted_id),
        email=doc["email"],
        full_name=doc["full_name"],
        created_at=doc["created_at"],
    )
    return user


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Accepts form fields: username (email) & password.
    Returns: { access_token, token_type, user }
    """
    db = get_db()
    user_doc = await db.users.find_one({"email": form_data.username.lower()})
    if not user_doc or not verify_password(form_data.password, user_doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token(str(user_doc["_id"]))
    user = UserPublic(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        full_name=user_doc["full_name"],
        created_at=user_doc["created_at"],
    )
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserPublic)
async def me(current_user: UserInDB = Depends(get_current_user)):  # ✅ fixed
    return UserPublic(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        created_at=current_user.created_at,
    )
