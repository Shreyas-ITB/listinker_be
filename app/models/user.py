from pydantic import BaseModel, Field, EmailStr
from fastapi import Form, HTTPException
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    username: str
    mobilenumber: str
    profile_img: Optional[str] = None
    user_location: List[float]
    email: str = "hello@listinker.com"
    email_verified: bool = False
    uid: str
    favorites: List[str] = []
    history: List[str] = Field(default=[], max_length=10)
    my_ads: List[str] = []
    chatrooms: List[str] = []
    followers: str
    following: str

class UserCreate(BaseModel):
    mobilenumber: str
    otp: str
    user_location: List[float]
    email: Optional[EmailStr] = None

    @classmethod
    def as_form(
        cls,
        mobilenumber: str = Form(...),
        otp: str = Form(...),
        user_location: str = Form(...),
        email: Optional[EmailStr] = Form(None)
    ):
        try:
            coords = [float(coord.strip()) for coord in user_location.split(",")]
            if len(coords) != 2:
                raise ValueError()
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Invalid location format. Must be two comma-separated numbers like '17.89,25.66'"
            )

        return cls(
            mobilenumber=mobilenumber,
            otp=otp,
            user_location=coords,
            email=email
        )

class UserUpdate(BaseModel):
    username: Optional[str] = None
    profile_img: Optional[str] = None
    user_location: Optional[List[float]] = None
    email: Optional[EmailStr] = None

    @classmethod
    def as_form(
        cls,
        username: Optional[str] = Form(None),
        profile_img: Optional[str] = Form(None),
        user_location: Optional[str] = Form(None),
        email: Optional[EmailStr] = Form(None),
    ):
        parsed_location = None
        if user_location:
            try:
                coords = [float(coord.strip()) for coord in user_location.split(",")]
                if len(coords) != 2:
                    raise ValueError("Location must contain exactly two numbers: latitude and longitude")
                parsed_location = coords
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail="Invalid location format. Must be two comma-separated numbers like '17.89,25.66'"
                )

        return cls(
            username=username,
            profile_img=profile_img,
            user_location=parsed_location,
            email=email
        )

class UserResponse(BaseModel):
    username: str
    mobilenumber: str
    email: str
    email_verified: bool = False
    profile_img: Optional[str] = None
    user_location: List[float]
    uid: str
    favorites: List[str] = []
    history: List[str] = []
    my_ads: List[str] = []
    chatrooms: List[str] = []
    followers: str
    following: str


class FollowRequest(BaseModel):
    action: Optional[str] = None  # "follow" or "unfollow"
    uid: str  # target user ID


class FollowersRequest(BaseModel):
    uid: Optional[str] = None  # target user ID (optional)
    search: Optional[str] = None  # search term for username (optional)


class FollowingRequest(BaseModel):
    uid: Optional[str] = None  # target user ID (optional)
    search: Optional[str] = None  # search term for username (optional)


class FollowersCountResponse(BaseModel):
    followers_count: int


class FollowingCountResponse(BaseModel):
    following_count: int


class FollowerResponse(BaseModel):
    uid: str
    username: str
    profile_img: Optional[str] = None


class FollowingResponse(BaseModel):
    uid: str
    username: str
    profile_img: Optional[str] = None


class FollowersResponse(BaseModel):
    followers_count: int
    followers: List[FollowerResponse]
    current_page: int
    total_pages: int
    page_size: int


class FollowingListResponse(BaseModel):
    following_count: int
    following: List[FollowingResponse]
    current_page: int
    total_pages: int
    page_size: int
