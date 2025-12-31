from datetime import datetime

async def sync_credits(db, uid: str):
    now = datetime.utcnow().isoformat()

    categories_cursor = db.categories.find({})
    async for category in categories_cursor:
        cat_id = category["numb_id"]

        # Free Credits
        existing_free = await db.free_credits.find_one({"UID": uid, "category": cat_id})
        if not existing_free:
            await db.free_credits.insert_one({
                "UID": uid,
                "category": cat_id,
                "credits": 1,
                "created": now,
                "updated": now
            })

        # Paid Credits
        existing_paid = await db.paid_credits.find_one({"UID": uid, "category": cat_id})
        if not existing_paid:
            await db.paid_credits.insert_one({
                "UID": uid,
                "category": cat_id,
                "credits": 0,
                "created": now,
                "updated": now
            })
