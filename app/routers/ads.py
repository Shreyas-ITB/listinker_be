from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from models.ad import Ad, AdCreate, AdUpdate, AdResponse, AdFeedResponse
from config import MAX_DISTANCE_KM
from utils.jwt import verify_token, get_optional_uid
from utils.s3 import s3_client
from database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING
from collections import Counter
from typing import List
import uuid
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from typing import Optional

router = APIRouter(prefix="/ads", tags=["ads"])

@router.post("/", response_model=AdResponse)
async def create_ad(
    ad_create: AdCreate = Depends(AdCreate.as_form),
    image: UploadFile = File(...),  # File(...) makes image REQUIRED
    uid: str = Depends(verify_token)
):
    db = await get_database()
    now = datetime.utcnow()

    # Use category IDs directly
    category_ids = ad_create.category
    
    if not category_ids:
        raise HTTPException(status_code=400, detail="At least one category ID is required.")

    # Check each category ID against sub_categories collection
    # Each category ID should be a valid numb_id of a sub_category
    valid_category_ids = []
    for category_id in category_ids:
        doc = await db.sub_categories.find_one({
            "numb_id": category_id
        })
        if not doc:
            raise HTTPException(status_code=400, detail=f"Category ID {category_id} is not valid.")
        valid_category_ids.append(category_id)
    
    # All category IDs must be valid
    if len(valid_category_ids) != len(category_ids):
        raise HTTPException(status_code=400, detail="One or more category IDs are not valid.")
    
    # Get the parent_id for credit checking (all categories should belong to the same parent)
    parent_ids = set()
    for category_id in valid_category_ids:
        doc = await db.sub_categories.find_one({
            "numb_id": category_id
        })
        if doc:
            parent_ids.add(doc["parent_id"])
    
    if len(parent_ids) > 1:
        raise HTTPException(status_code=400, detail="Provided category IDs belong to multiple unrelated categories.")
    
    matched_numb_id = list(parent_ids)[0] if parent_ids else None
    if not matched_numb_id:
        raise HTTPException(status_code=400, detail="No valid parent category found for the provided category IDs.")

    # Credit check
    free_credit_doc = await db.free_credits.find_one({
        "UID": uid,
        "category": matched_numb_id,
        "credits": {"$gt": 0}
    })

    paid_credit_doc = None
    used_free_credit = False

    if free_credit_doc:
        # Use free credit
        await db.free_credits.update_one(
            {"_id": free_credit_doc["_id"]},
            {"$inc": {"credits": -1}, "$set": {"updated": now}}
        )
        used_free_credit = True
    else:
        paid_credit_doc = await db.paid_credits.find_one({
            "UID": uid,
            "category": matched_numb_id,
            "credits": {"$gt": 0}
        })
        if paid_credit_doc:
            await db.paid_credits.update_one(
                {"_id": paid_credit_doc["_id"]},
                {"$inc": {"credits": -1}, "$set": {"updated": now}}
            )
        else:
            raise HTTPException(status_code=403, detail="Not enough free or paid credits to create ad")

    # Upload image to S3 (now mandatory)
    if not image:
        raise HTTPException(status_code=400, detail="Image is required to create an ad")

    image_url = await s3_client.upload_file(image)

    # Create the ad
    new_ad = Ad(
        ad_id=str(uuid.uuid4()),
        title=ad_create.title,
        description=ad_create.description,
        price=ad_create.price,
        category=category_ids,
        ad_loc=ad_create.ad_loc,
        owner=uid,
        image=[image_url],
        time_created=now.isoformat()
    )
    await db.ads.insert_one(new_ad.dict())

    # Update user's ad list
    await db.users.update_one(
        {"uid": uid},
        {"$push": {"my_ads": new_ad.ad_id}}
    )

    return AdResponse(**new_ad.dict())

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

@router.get("/", response_model=List[AdFeedResponse])
async def get_ads(
    uid: Optional[str] = Depends(get_optional_uid),
    category: Optional[int] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    page: int = Query(..., ge=1),
    page_size: int = Query(15, ge=1, le=100),
    db=Depends(get_database)
):
    query = {}
    
    if category:
        query["category"] = category
    if min_price is not None and max_price is not None:
        query["price"] = {"$gte": min_price, "$lte": max_price}
    
    # Calculate offset for pagination
    offset = (page - 1) * page_size
    
    ads_to_show = []
    user_location = None
    history_ids = []

    if uid:
        user = await db.users.find_one({"uid": uid}, {"history": 1, "user_location": 1})
        history_ids = user.get("history", []) if user else []
        user_location = user.get("user_location") if user else None

        if history_ids:
            history_ads = await db.ads.find(
                {"ad_id": {"$in": history_ids}}, {"ad_id": 1, "category": 1}
            ).to_list(100)

            all_cats = [cat for ad in history_ads for cat in ad.get("category", [])]
            ranked_cats = [cat for cat, _ in Counter(all_cats).most_common()]

            for cat in ranked_cats:
                ads = await db.ads.find(
                    {
                        "category": cat,
                        "ad_id": {"$nin": history_ids},
                        **query
                    },
                    {"title": 1, "description": 1, "image": 1, "views": 1,
                     "favorited": 1, "owner": 1, "ad_id": 1, "ad_loc": 1, "time_created": 1, "category": 1}
                ).skip(offset).limit(page_size).sort("time_created", DESCENDING).to_list(page_size)

                for ad in ads:
                    if "ad_id" not in ad:
                        continue
                    if user_location and "ad_loc" in ad and ad["ad_loc"]:
                        try:
                            dist = haversine(user_location[0], user_location[1], ad["ad_loc"][0], ad["ad_loc"][1])
                            if dist <= MAX_DISTANCE_KM:
                                ads_to_show.append(ad)
                        except Exception:
                            continue
                    else:
                        ads_to_show.append(ad)

                if len(ads_to_show) >= page_size:
                    break

            # Show filler ads only if still needed
            if len(ads_to_show) < page_size:
                seen_ids = [ad["ad_id"] for ad in ads_to_show if "ad_id" in ad] + \
                           [ad["ad_id"] for ad in history_ads if "ad_id" in ad]

                filler_ads = await db.ads.find(
                    {"ad_id": {"$nin": seen_ids}},
                    {"title": 1, "description": 1, "image": 1, "views": 1,
                     "favorited": 1, "owner": 1, "ad_id": 1, "ad_loc": 1, "time_created": 1, "category": 1}
                ).skip(offset).limit(page_size).to_list(page_size)

                for ad in filler_ads:
                    if "ad_id" not in ad:
                        continue
                    if user_location and "ad_loc" in ad and ad["ad_loc"]:
                        try:
                            dist = haversine(user_location[0], user_location[1], ad["ad_loc"][0], ad["ad_loc"][1])
                            if dist <= MAX_DISTANCE_KM:
                                ads_to_show.append(ad)
                                if len(ads_to_show) >= page_size:
                                    break
                        except Exception:
                            continue
                    else:
                        ads_to_show.append(ad)
                        if len(ads_to_show) >= page_size:
                            break

        else:
            # No history
            candidate_ads = await db.ads.find(
                query,
                {"title": 1, "description": 1, "image": 1, "views": 1,
                "favorited": 1, "owner": 1, "ad_id": 1, "ad_loc": 1, "time_created": 1, "category": 1}
            ).sort("time_created", DESCENDING).skip(offset).limit(page_size).to_list(page_size)

            for ad in candidate_ads:
                if "ad_id" not in ad:
                    continue
                if user_location and "ad_loc" in ad and ad["ad_loc"]:
                    try:
                        dist = haversine(user_location[0], user_location[1], ad["ad_loc"][0], ad["ad_loc"][1])
                        if dist <= MAX_DISTANCE_KM:
                            ads_to_show.append(ad)
                            if len(ads_to_show) >= page_size:
                                break
                    except Exception:
                        continue
                else:
                    ads_to_show.append(ad)
                    if len(ads_to_show) >= page_size:
                        break
    else:
        # Anonymous user
        ads_to_show = await db.ads.find(
            query,
            {"title": 1, "description": 1, "image": 1, "views": 1,
            "favorited": 1, "owner": 1, "ad_id": 1, "time_created": 1, "category": 1}
        ).sort("time_created", DESCENDING).skip(offset).limit(page_size).to_list(page_size)

    # Get owner usernames
    owner_ids = list({ad["owner"] for ad in ads_to_show if "owner" in ad})
    owners = await db.users.find({"uid": {"$in": owner_ids}}, {"uid": 1, "username": 1}).to_list(len(owner_ids))
    owner_map = {u["uid"]: u["username"] for u in owners}

    # Final formatting
    results = []
    for ad in ads_to_show[:page_size]:
        if "ad_id" not in ad:
            continue
        results.append({
            "title": ad["title"],
            "description": ad["description"],
            "image": ad["image"][0] if ad.get("image") else None,
            "views": ad.get("views", 0),
            "favorited": ad.get("favorited", 0),
            "username": owner_map.get(ad["owner"], "Unknown"),
            "ad_id": ad["ad_id"],
            "time_created": ad.get("time_created", ""),
            "category": ad.get("category", [])
        })
    
    return results

@router.get("/my-ads")
async def get_my_ads(
    uid: str = Depends(verify_token),
    page: int = Query(..., ge=1),
    page_size: int = Query(5, ge=1, le=100)
):
    db = await get_database()
    user = await db.users.find_one({"uid": uid})
    if not user or "my_ads" not in user or not user["my_ads"]:
        return []
    
    # Calculate offset for pagination
    offset = (page - 1) * page_size
    
    ads = await db.ads.find({"ad_id": {"$in": user["my_ads"]}}).skip(offset).limit(page_size).to_list(None)
    for ad in ads:
        ad.pop("_id", None)

    return [AdResponse(**ad) for ad in ads]

@router.get("/{ad_id}", response_model=AdResponse)
async def get_ad(
    ad_id: str,
    uid: Optional[str] = Depends(get_optional_uid),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    ad = await db.ads.find_one({"ad_id": ad_id})
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if uid:
        # Check if user has already viewed the ad
        already_viewed = uid in ad.get("viewed_by", [])

        if not already_viewed:
            # 1. Update the ad document: increment views, add to viewed_by
            await db.ads.update_one(
                {"ad_id": ad_id},
                {
                    "$inc": {"views": 1},
                    "$addToSet": {"viewed_by": uid}
                }
            )

            # 2. Update the user's history (only if ad_id is not already there)
            user = await db.users.find_one({"uid": uid}, {"history": 1})
            if user is not None:
                history = user.get("history", [])
                if ad_id not in history:
                    # Prepend the new ad_id, truncate to max 15
                    new_history = [ad_id] + history[:14]
                    await db.users.update_one(
                        {"uid": uid},
                        {"$set": {"history": new_history}}
                    )

            # Refresh ad to reflect updated data in response
            ad["views"] = ad.get("views", 0) + 1
            ad["viewed_by"] = ad.get("viewed_by", []) + [uid]

    return AdResponse(**ad)

@router.put("/{ad_id}")
async def update_ad(
    ad_id: str,
    ad_update: AdUpdate = Depends(AdUpdate.as_form),
    uid: str = Depends(verify_token)
):
    db = await get_database()
    ad = await db.ads.find_one({"ad_id": ad_id})

    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if ad["owner"] != uid:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = ad_update.dict(exclude_unset=True)
    
    # Check for "no changes detected"
    unchanged = True
    for key, value in update_data.items():
        if ad.get(key) != value:
            unchanged = False
            break
    
    if unchanged:
        raise HTTPException(status_code=400, detail="No changes detected")
    
    # Validate category IDs if they are being updated
    if "category" in update_data:
        category_ids = update_data["category"]
        if category_ids:
            # Check each category ID against sub_categories collection
            # Each category ID should be a valid numb_id of a sub_category
            valid_category_ids = []
            for category_id in category_ids:
                doc = await db.sub_categories.find_one({
                    "numb_id": category_id
                })
                if not doc:
                    raise HTTPException(status_code=400, detail=f"Category ID {category_id} is not valid.")
                valid_category_ids.append(category_id)
            
            # All category IDs must be valid
            if len(valid_category_ids) != len(category_ids):
                raise HTTPException(status_code=400, detail="One or more category IDs are not valid.")
            
            # Get the parent_id for credit checking (all categories should belong to the same parent)
            parent_ids = set()
            for category_id in valid_category_ids:
                doc = await db.sub_categories.find_one({
                    "numb_id": category_id
                })
                if doc:
                    parent_ids.add(doc["parent_id"])
            
            if len(parent_ids) > 1:
                raise HTTPException(status_code=400, detail="Provided category IDs belong to multiple unrelated categories.")
    
    await db.ads.update_one({"ad_id": ad_id}, {"$set": update_data})
    return {"message": "Ad updated successfully"}

@router.delete("/{ad_id}")
async def delete_ad(ad_id: str, uid: str = Depends(verify_token)):
    db = await get_database()
    ad = await db.ads.find_one({"ad_id": ad_id})
    if not ad or ad["owner"] != uid:
        raise HTTPException(status_code=403, detail="Not authorized or ad not found")
    await db.ads.delete_one({"ad_id": ad_id})
    await db.users.update_one(
        {"uid": uid},
        {"$pull": {"my_ads": ad_id}}
    )
    return {"message": "Ad deleted successfully"}