from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import ensure_indexes
from .routers import auth as auth_router
from .routers import expenses as expenses_router
from .routers import reports as reports_router

app = FastAPI(title="Expense Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(expenses_router.router)
app.include_router(reports_router.router)

@app.on_event("startup")
async def startup_event():
    await ensure_indexes()

@app.get("/")
async def root():
    return {"status": "ok", "name": "Expense Tracker API"}
