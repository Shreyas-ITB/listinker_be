from fastapi import APIRouter, HTTPException, Depends, UploadFile
from models.user import UserResponse, UserUpdate, FollowRequest, FollowersRequest, FollowersCountResponse, FollowerResponse, FollowersResponse, FollowingRequest, FollowingCountResponse, FollowingResponse, FollowingListResponse
from utils.jwt import verify_token
from utils.s3 import s3_client
from database import get_database
from utils.email import send_email
from utils.otp import generate_otp, store_email_otp
from utils.email_templates import EMAIL_VERIFICATION_TEMPLATE
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user(uid: str = Depends(verify_token)):
    db = await get_database()
    user = await db.users.find_one({"uid": uid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)

@router.put("/me")
async def update_user_profile(
    user_update: UserUpdate = Depends(UserUpdate.as_form),
    profile_image: UploadFile = None,
    uid: str = Depends(verify_token)
):
    db = await get_database()
    user_collection = db.users

    # Fetch existing user data
    existing_user = await user_collection.find_one({"uid": uid})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Filter out None values from user_update
    update_fields = {
        key: value for key, value in user_update.dict().items()
        if value is not None
    }

    # Check if email is being updated
    email_updated = False
    if "email" in update_fields and existing_user.get("email") != update_fields["email"]:
        email_updated = True
        # Set email_verified to False when email is updated
        update_fields["email_verified"] = False

    # Compare each field to existing DB values
    update_data = {}
    for key, new_value in update_fields.items():
        if key == "username":
            if not (4 <= len(new_value) <= 10):
                raise HTTPException(
                    status_code=422,
                    detail="Username must be between 4 and 10 characters"
                )

        if existing_user.get(key) != new_value:
            update_data[key] = new_value

        # Normalize user_location comparison
        if key == "user_location":
            existing_location = existing_user.get("user_location")
            if existing_location is None or [round(float(c), 6) for c in existing_location] != [round(float(c), 6) for c in new_value]:
                update_data[key] = new_value
        elif existing_user.get(key) != new_value:
            update_data[key] = new_value

    # Handle image upload separately
    if profile_image:
        image_url = await s3_client.upload_file(profile_image)
        if existing_user.get("profile_img") != image_url:
            update_data["profile_img"] = image_url

    if not update_data:
        raise HTTPException(status_code=400, detail="No changes detected")

    # Handle email verification if email is updated
    if email_updated:
        # Generate OTP
        otp = generate_otp()
        
        # Store OTP with email
        email = update_fields["email"]
        store_email_otp(email, otp)
        
        # Send email with OTP
        html_content = EMAIL_VERIFICATION_TEMPLATE.replace("{{otp_code}}", otp)
        subject = "Email Verification OTP"
        email_sent = send_email(email, subject, html_content)
        
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send verification email")
        
        # Apply updates (email_verified is already set to False in update_fields)
        await user_collection.update_one({"uid": uid}, {"$set": update_data})
        
        return {"message": "Verification Code has been sent to your email", "updated_fields": list(update_data.keys())}

    # Apply updates for non-email changes
    await user_collection.update_one({"uid": uid}, {"$set": update_data})

    return {"message": "Profile updated successfully", "updated_fields": list(update_data.keys())}

@router.delete("/me")
async def delete_user(uid: str = Depends(verify_token)):
    db = await get_database()
    
    # Delete user's ads
    await db.ads.delete_many({"owner": uid})
    
    # Delete user's chatrooms and messages
    chatrooms = await db.chatrooms.find({"participants": uid}).to_list(None)
    for chatroom in chatrooms:
        await db.messages.delete_many({"chatroom_id": chatroom["chatroom_id"]})
    await db.chatrooms.delete_many({"participants": uid})
    
    # Delete user
    await db.users.delete_one({"uid": uid})
    
    return {"message": "User and all related data deleted successfully"}


@router.post("/follow")
async def follow_user(
    follow_request: FollowRequest,
    current_user_id: str = Depends(verify_token)
):
    db = await get_database()
    
    # Get the target user ID from the request body
    target_user_id = follow_request.uid
    
    # Validate action parameter if provided
    if follow_request.action and follow_request.action not in ["follow", "unfollow"]:
        raise HTTPException(status_code=400, detail="Action must be 'follow' or 'unfollow'")
    
    # Get target user document
    target_user = await db.users.find_one({"uid": target_user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    
    # Get current user document
    current_user = await db.users.find_one({"uid": current_user_id})
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")
    
    # Get the followers_id from target user's document
    followers_id = target_user.get("followers")
    if not followers_id:
        raise HTTPException(status_code=500, detail="Target user followers data not found")
    
    # Get the followers document
    followers_doc = await db.followers.find_one({"_id": followers_id})
    if not followers_doc:
        raise HTTPException(status_code=500, detail="Followers document not found")
    
    followers_list = followers_doc.get("followers", [])
    followers_count = len(followers_list)
    
    if follow_request.action == "follow":
        # Check if already following
        if current_user_id in followers_list:
            # Return current followers count without changes
            return {"followers_count": followers_count}
        
        # Add current user to target user's followers list
        followers_list.append(current_user_id)
        followers_count = len(followers_list)
        
        # Update the followers document with both followers list and followers_count
        await db.followers.update_one(
            {"_id": followers_id},
            {"$set": {"followers": followers_list, "followers_count": followers_count}}
        )
        
        # Also update the following collection for the current user
        current_user_following_id = current_user.get("following")
        if current_user_following_id:
            following_doc = await db.following.find_one({"_id": current_user_following_id})
            if following_doc:
                following_list = following_doc.get("following", [])
                if target_user_id not in following_list:
                    following_list.append(target_user_id)
                    following_count = len(following_list)
                    await db.following.update_one(
                        {"_id": current_user_following_id},
                        {"$set": {"following": following_list, "following_count": following_count}}
                    )
        
        return {"followers_count": followers_count}
    
    elif follow_request.action == "unfollow":
        # Check if not following
        if current_user_id not in followers_list:
            # Return current followers count without changes
            return {"followers_count": followers_count}
        
        # Remove current user from target user's followers list
        followers_list.remove(current_user_id)
        followers_count = len(followers_list)
        
        # Ensure followers_count doesn't drop below zero
        if followers_count < 0:
            followers_count = 0
        
        # Update the followers document with both followers list and followers_count
        await db.followers.update_one(
            {"_id": followers_id},
            {"$set": {"followers": followers_list, "followers_count": followers_count}}
        )
        
        # Also update the following collection for the current user
        current_user_following_id = current_user.get("following")
        if current_user_following_id:
            following_doc = await db.following.find_one({"_id": current_user_following_id})
            if following_doc:
                following_list = following_doc.get("following", [])
                if target_user_id in following_list:
                    following_list.remove(target_user_id)
                    following_count = len(following_list)
                    # Ensure following_count doesn't drop below zero
                    if following_count < 0:
                        following_count = 0
                    await db.following.update_one(
                        {"_id": current_user_following_id},
                        {"$set": {"following": following_list, "following_count": following_count}}
                    )
        
        return {"followers_count": followers_count}
    
    else:  # No action provided, check follow status
        is_following = current_user_id in followers_list
        return {"is_following": is_following}

@router.post("/followers")
async def get_followers(
    followers_request: FollowersRequest,
    page: int = None,
    page_size: int = None,
    current_user_id: str = Depends(verify_token)
):
    db = await get_database()
    
    # If uid is not provided, use the current user's UID
    target_user_id = followers_request.uid or current_user_id
    
    # Get target user document
    target_user = await db.users.find_one({"uid": target_user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    
    # Get the followers_id from target user's document
    followers_id = target_user.get("followers")
    if not followers_id:
        raise HTTPException(status_code=500, detail="Target user followers data not found")
    
    # Get the followers document
    followers_doc = await db.followers.find_one({"_id": followers_id})
    if not followers_doc:
        raise HTTPException(status_code=500, detail="Followers document not found")
    
    # Get the followers list
    followers_list = followers_doc.get("followers", [])
    
    # If search is provided, filter followers by username
    if followers_request.search:
        # Get user details for all followers
        follower_users = await db.users.find({"uid": {"$in": followers_list}}).to_list(None)
        
        # Filter followers by username search term
        search_term = followers_request.search.lower()
        filtered_followers = [
            user for user in follower_users
            if search_term in user.get("username", "").lower()
        ]
        
        # Get the UIDs of filtered followers
        followers_list = [user["uid"] for user in filtered_followers]
    
    # Calculate total followers count
    total_followers = len(followers_list)
    
    # If pagination parameters are not provided, return just the follower count
    if page is None or page_size is None:
        return FollowersCountResponse(followers_count=total_followers)
    
    # Validate page number
    if page < 1:
        raise HTTPException(status_code=400, detail="Page number must be greater than 0")
    
    # Validate page_size
    if page_size < 1:
        raise HTTPException(status_code=400, detail="Page size must be greater than 0")
    
    # Calculate pagination values
    total_pages = (total_followers + page_size - 1) // page_size if page_size > 0 else 0
    
    # Calculate start and end indices for pagination
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    # If start index is beyond the list, return empty result
    if start_index >= total_followers:
        return FollowersResponse(
            followers_count=total_followers,
            followers=[],
            current_page=page,
            total_pages=total_pages,
            page_size=page_size
        )
    
    # Get the paginated followers list
    paginated_followers_ids = followers_list[start_index:end_index]
    
    # Get user details for paginated followers
    paginated_followers = await db.users.find({"uid": {"$in": paginated_followers_ids}}).to_list(None)
    
    # Create a dictionary to map UID to user details for sorting
    followers_dict = {user["uid"]: user for user in paginated_followers}
    
    # Sort followers in the same order as paginated_followers_ids
    sorted_followers = [
        FollowerResponse(
            uid=user["uid"],
            username=user["username"],
            profile_img=user.get("profile_img")
        )
        for uid in paginated_followers_ids
        if uid in followers_dict
        for user in [followers_dict[uid]]
    ]
    
    return FollowersResponse(
        followers_count=total_followers,
        followers=sorted_followers,
        current_page=page,
        total_pages=total_pages,
        page_size=page_size
    )

@router.post("/following")
async def get_following(
    following_request: FollowingRequest,
    page: int = None,
    page_size: int = None,
    current_user_id: str = Depends(verify_token)
):
    db = await get_database()
    
    # If uid is not provided, use the current user's UID
    target_user_id = following_request.uid or current_user_id
    
    # Get target user document
    target_user = await db.users.find_one({"uid": target_user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    
    # Get the following_id from target user's document
    following_id = target_user.get("following")
    if not following_id:
        raise HTTPException(status_code=500, detail="Target user following data not found")
    
    # Get the following document
    following_doc = await db.following.find_one({"_id": following_id})
    if not following_doc:
        raise HTTPException(status_code=500, detail="Following document not found")
    
    # Get the following list
    following_list = following_doc.get("following", [])
    
    # If search is provided, filter following by username
    if following_request.search:
        # Get user details for all following
        following_users = await db.users.find({"uid": {"$in": following_list}}).to_list(None)
        
        # Filter following by username search term
        search_term = following_request.search.lower()
        filtered_following = [
            user for user in following_users
            if search_term in user.get("username", "").lower()
        ]
        
        # Get the UIDs of filtered following
        following_list = [user["uid"] for user in filtered_following]
    
    # Calculate total following count
    total_following = len(following_list)
    
    # If pagination parameters are not provided, return just the following count
    if page is None or page_size is None:
        return FollowingCountResponse(following_count=total_following)
    
    # Validate page number
    if page < 1:
        raise HTTPException(status_code=400, detail="Page number must be greater than 0")
    
    # Validate page_size
    if page_size < 1:
        raise HTTPException(status_code=400, detail="Page size must be greater than 0")
    
    # Calculate pagination values
    total_pages = (total_following + page_size - 1) // page_size if page_size > 0 else 0
    
    # Calculate start and end indices for pagination
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    # If start index is beyond the list, return empty result
    if start_index >= total_following:
        return FollowingListResponse(
            following_count=total_following,
            following=[],
            current_page=page,
            total_pages=total_pages,
            page_size=page_size
        )
    
    # Get the paginated following list
    paginated_following_ids = following_list[start_index:end_index]
    
    # Get user details for paginated following
    paginated_following = await db.users.find({"uid": {"$in": paginated_following_ids}}).to_list(None)
    
    # Create a dictionary to map UID to user details for sorting
    following_dict = {user["uid"]: user for user in paginated_following}
    
    # Sort following in the same order as paginated_following_ids
    sorted_following = [
        FollowingResponse(
            uid=user["uid"],
            username=user["username"],
            profile_img=user.get("profile_img")
        )
        for uid in paginated_following_ids
        if uid in following_dict
        for user in [following_dict[uid]]
    ]
    
    return FollowingListResponse(
        following_count=total_following,
        following=sorted_following,
        current_page=page,
        total_pages=total_pages,
        page_size=page_size
    )
