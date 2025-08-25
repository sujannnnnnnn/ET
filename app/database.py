from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client: AsyncIOMotorClient | None = None

def get_client() -> AsyncIOMotorClient:
    global client
    if client is None:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
    return client

def get_db():
    return get_client()[settings.MONGODB_DB]

async def ensure_indexes():
    db = get_db()
    # Users: unique email
    await db.users.create_index("email", unique=True)
    # Expenses: compound indexes for queries
    await db.expenses.create_index([("user_id", 1), ("date", 1)])
    await db.expenses.create_index([("user_id", 1), ("category", 1)])
