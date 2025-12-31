from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import CollectionInvalid

async def initialize_follow_relations_collections(db: AsyncIOMotorDatabase):
    """
    Initialize followers and following collections with necessary indexes.
    """
    # Initialize followers collection
    try:
        # Create followers collection if it doesn't exist
        if "followers" not in await db.list_collection_names():
            await db.create_collection("followers")
            print("[INIT] Created followers collection.")
        else:
            print("[INIT] Followers collection already exists.")
            
        # Create indexes for followers collection
        followers_collection = db.followers
        await followers_collection.create_index("user_id", unique=True)
        print("[INIT] Created index on user_id for followers collection.")
        
        # Add followers_count field to existing documents if not present
        await followers_collection.update_many(
            {"followers_count": {"$exists": False}},
            {"$set": {"followers_count": 0}}
        )
        print("[INIT] Added followers_count field to existing followers documents.")
        
    except CollectionInvalid as e:
        print(f"[ERROR] Error creating followers collection: {e}")
    
    # Initialize following collection
    try:
        # Create following collection if it doesn't exist
        if "following" not in await db.list_collection_names():
            await db.create_collection("following")
            print("[INIT] Created following collection.")
        else:
            print("[INIT] Following collection already exists.")
            
        # Create indexes for following collection
        following_collection = db.following
        await following_collection.create_index("user_id", unique=True)
        print("[INIT] Created index on user_id for following collection.")
        
        # Add following_count field to existing documents if not present
        await following_collection.update_many(
            {"following_count": {"$exists": False}},
            {"$set": {"following_count": 0}}
        )
        print("[INIT] Added following_count field to existing following documents.")
        
    except CollectionInvalid as e:
        print(f"[ERROR] Error creating following collection: {e}")
