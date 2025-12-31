from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from bson import ObjectId


class CategoryCredit(BaseModel):
    category_id: int = Field(..., description="Numeric ID of the category as per categories.toml")
    credits: int = Field(default=1, description="Number of remaining credits in this category")
    last_used: datetime = Field(default_factory=datetime.utcnow, description="Last time a free credit was used in this category")


class UserCreditsModel(BaseModel):
    user_id: str = Field(..., description="User's ID or ObjectId in string form")
    credits: List[CategoryCredit] = Field(..., description="List of credits per category")

    class Config:
        arbitrary_types_allowed = True