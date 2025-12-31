from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def get_database() -> AsyncIOMotorClient:
    return db.database

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(MONGO_URI)
    db.database = db.client[DB_NAME]
    print("[INIT] Connected to MongoDB")

async def close_mongo_connection():
    db.client.close()
    print("[INIT] Disconnected from MongoDB")
