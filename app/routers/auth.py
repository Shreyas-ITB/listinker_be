from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from utils.otp import send_otp, verify_otp, send_email_otp, verify_email_otp, get_email_by_otp
from utils.jwt import create_access_token, verify_token_bool
from utils.credits import sync_credits
from database import get_database
from models.user import UserCreate, User
import uuid

router = APIRouter(prefix="/auth", tags=["authentication"])

class OTPRequest(BaseModel):
    mobile_number: str

class EmailOTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    mobile_number: str
    otp: str

class TokenVerify(BaseModel):
    token: str

class EmailVerify(BaseModel):
    email: str
    otp: str

@router.post("/request-otp")
async def request_otp(request: OTPRequest):
    success = await send_otp(request.mobile_number)
    if success:
        return {"message": "OTP sent successfully"}
    raise HTTPException(status_code=400, detail="Failed to send OTP")

@router.post("/request-email-otp")
async def request_email_otp(request: EmailOTPRequest):
    success = await send_email_otp(request.email)
    if success:
        return {"message": "Email OTP sent successfully"}
    raise HTTPException(status_code=400, detail="Failed to send email OTP")

@router.post("/verify-otp")
async def verify_otp_endpoint(request: UserCreate = Depends(UserCreate.as_form)):
    if not verify_otp(request.mobilenumber, request.otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    db = await get_database()
    existing_user = await db.users.find_one({"mobilenumber": request.mobilenumber})

    if existing_user:
        uid = existing_user["uid"]
    else:
        uid = str(uuid.uuid4())
        # Generate UUIDs for followers and following collections
        followers_id = str(uuid.uuid4())
        following_id = str(uuid.uuid4())
        
        # Create entries in followers and following collections with empty arrays
        await db.followers.insert_one({
            "_id": followers_id,
            "user_id": uid,
            "followers": [],
            "followers_count": 0
        })
        
        await db.following.insert_one({
            "_id": following_id,
            "user_id": uid,
            "following": [],
            "following_count": 0
        })
        
        new_user = User(
            username="ListinkerUser",
            mobilenumber=request.mobilenumber,
            profile_img=None,
            user_location=request.user_location,
            email="hello@listinker.com",
            uid=uid,
            favorites=[],
            history=[],
            my_ads=[],
            chatrooms=[],
            followers=followers_id,
            following=following_id
        )
        await db.users.insert_one(new_user.dict())

    await sync_credits(db, uid)

    token = create_access_token({"uid": uid})
    return {"token": token, "uid": uid}

@router.post("/verify-user")
async def verify_user(request: TokenVerify):
    is_valid = verify_token_bool(request.token)
    return {"valid": is_valid}

@router.post("/verify-email")
async def verify_email(request: EmailVerify):
    # Verify OTP matches stored OTP
    if not verify_email_otp(request.email, request.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    db = await get_database()
    
    # Find user by email
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user's email_verified status to True
    await db.users.update_one(
        {"email": request.email},
        {"$set": {"email_verified": True}}
    )
    
    return {"message": "Email verified successfully"}
