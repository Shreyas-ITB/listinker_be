from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi import Form, HTTPException

class Ad(BaseModel):
    ad_id: str
    title: str
    description: str
    price: int
    image: List[str] = []
    category: List[int]
    ad_loc: List[float]
    time_created: str
    owner: str
    status: str = "under-review"
    views: int = 0
    favorited: int = 0

class AdCreate(BaseModel):
    title: str
    description: str
    price: int
    category: List[int]
    ad_loc: List[float]
    status: str = "under-review"

    @classmethod
    def as_form(
        cls,
        title: str = Form(...),
        description: str = Form(...),
        price: int = Form(...),
        category: List[int] = Form(...),
        ad_loc: str = Form(...),
        status: str = Form("under-review")
    ):
        try:
            coords = [float(x.strip()) for x in ad_loc.split(",")]
            if len(coords) != 2:
                raise ValueError("length")
        except ValueError as e:
            if str(e) == "length":
                raise HTTPException(
                    status_code=422,
                    detail="Location must contain exactly two numbers: latitude and longitude"
                )
            raise HTTPException(
                status_code=422,
                detail="Invalid location format. Must be two comma-separated numbers"
            )

        return cls(
            title=title,
            description=description,
            price=price,
            category=category,
            ad_loc=coords,
            status=status
        )

class AdUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    category: Optional[List[int]] = None
    ad_loc: Optional[List[float]] = None
    status: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        title: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        price: Optional[int] = Form(None),
        category: Optional[List[int]] = Form(None),
        ad_loc: Optional[str] = Form(None),
        status: Optional[str] = Form(None),
    ):
        parsed_loc = None
        if ad_loc:
            try:
                coords = [float(x.strip()) for x in ad_loc.split(",")]
                if len(coords) != 2:
                    raise ValueError("length")
                parsed_loc = coords
            except ValueError as e:
                if str(e) == "length":
                    raise HTTPException(
                        status_code=422,
                        detail="Location must contain exactly two numbers: latitude and longitude"
                    )
                raise HTTPException(
                    status_code=422,
                    detail="Invalid location format. Must be two comma-separated numbers"
                )

        return cls(
            title=title,
            description=description,
            price=price,
            category=category,
            ad_loc=parsed_loc,
            status=status
        )

class AdResponse(BaseModel):
    ad_id: str
    title: str
    description: str
    price: int
    image: List[str]
    category: List[int]
    ad_loc: List[float]
    time_created: str
    owner: str
    status: str
    views: int
    favorited: int

class AdFeedResponse(BaseModel):
    title: str
    description: str
    image: Optional[str]
    views: int
    favorited: int
    username: str
    ad_id: str
    time_created: str
    category: List[int]