from fastapi import APIRouter, HTTPException, Depends, Query
from models.ad import AdResponse
from utils.jwt import verify_token
from database import get_database
from typing import List

router = APIRouter(prefix="/favorites", tags=["favorites"])

@router.post("/{ad_id}")
async def add_to_favorites(ad_id: str, uid: str = Depends(verify_token)):
    db = await get_database()

    # Check if ad exists
    ad = await db.ads.find_one({"ad_id": ad_id})
    if not ad:
        raise HTTPException(status_code=44, detail="Ad not found")

    # Fetch user's document
    user = await db.users.find_one({"uid": uid}, {"favorites": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if ad is already in favorites
    if "favorites" in user and ad_id in user["favorites"]:
        raise HTTPException(status_code=400, detail="You have already favorited this ad.")

    # Add to user's favorites
    await db.users.update_one(
        {"uid": uid},
        {"$addToSet": {"favorites": ad_id}}
    )

    # Increment ad's favorited count
    await db.ads.update_one(
        {"ad_id": ad_id},
        {"$inc": {"favorited": 1}}
    )

    return {"message": "Added to favorites"}

@router.delete("/{ad_id}")
async def remove_from_favorites(ad_id: str, uid: str = Depends(verify_token)):
    db = await get_database()
    
    # Remove from user's favorites
    result = await db.users.update_one(
        {"uid": uid},
        {"$pull": {"favorites": ad_id}}
    )
    
    if result.modified_count > 0:
        # Decrement favorited count for the ad
        await db.ads.update_one(
            {"ad_id": ad_id},
            {"$inc": {"favorited": -1}}
        )
        return {"message": "Removed from favorites"}
    
    raise HTTPException(status_code=404, detail="Ad not in favorites")

@router.get("/", response_model=List[AdResponse])
async def get_favorites(
    uid: str = Depends(verify_token),
    page: int = Query(..., ge=1),
    page_size: int = Query(5, ge=1, le=100)
):
    db = await get_database()
    
    # Get user's favorite ad IDs
    user = await db.users.find_one({"uid": uid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    favorite_ads = []
    if user.get("favorites"):
        # Calculate offset for pagination
        offset = (page - 1) * page_size
        
        ads_cursor = db.ads.find({"ad_id": {"$in": user["favorites"]}}).skip(offset).limit(page_size)
        ads = await ads_cursor.to_list(None)
        favorite_ads = [AdResponse(**ad) for ad in ads]
    
    return favorite_ads
