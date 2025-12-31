from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List
from utils.jwt import verify_token
from database import get_database
from typing import Union
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

class CategoryResponse(BaseModel):
    numb_id: int
    name: str

class SubCategoryResponse(BaseModel):
    numb_id: int
    name: str
    parent_id: int

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/suggest", response_model=List[str])
async def suggest_subcategories(
    input: str = Query(..., min_length=1),
):
    db = await get_database()

    # Find all matching subcategories across documents
    cursor = db.sub_categories.find({
        "name": {
            "$regex": f"^{input}",
            "$options": "i"
        }
    })

    results = set()

    async for doc in cursor:
        results.add(doc["name"])

    return sorted(results)

@router.get("/categories", response_model=List[CategoryResponse])
async def get_all_categories(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    cursor = db.categories.find({}, {"numb_id": 1, "name": 1, "_id": 0})
    categories = []
    
    async for doc in cursor:
        categories.append(CategoryResponse(**doc))
    
    return categories

@router.get("/sub-categories", response_model=List[SubCategoryResponse])
async def get_all_sub_categories(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    cursor = db.sub_categories.find({}, {"numb_id": 1, "name": 1, "parent_id": 1, "_id": 0})
    sub_categories = []
    
    async for doc in cursor:
        sub_categories.append(SubCategoryResponse(**doc))
    
    return sub_categories

@router.get("/{category_id}")
async def get_category_details(
    category_id: Union[int, str],
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # Step 1: Identify whether the input is a num_id or a name
    if str(category_id).isdigit():
        # Search by num_id
        query = {"numb_id": int(category_id)}
    else:
        # Search by category name (case-insensitive)
        print("Search by name")
        query = {"name": {"$regex": f"^{category_id}$", "$options": "i"}}

    category_doc = await db.categories.find_one(query)

    if not category_doc:
        raise HTTPException(status_code=404, detail="Category not found")

    # Extract numb_id and name from category_doc
    num_id = category_doc.get("numb_id")
    name = category_doc.get("name")

    if num_id is None or name is None:
        raise HTTPException(status_code=500, detail="Missing numb_id or name in category document")

    # Step 2: Find subcategories by parent_id
    sub_cursor = db.sub_categories.find({"parent_id": num_id})
    subcategories = []

    async for doc in sub_cursor:
        subcategories.append({
            "name": doc["name"],
            "numb_id": doc["numb_id"]
        })

    # Sort by numb_id
    subcategories.sort(key=lambda x: x["numb_id"])

    return {
        "category": name,
        "sub_categories": subcategories
    }