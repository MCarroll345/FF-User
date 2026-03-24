from fastapi import FastAPI, APIRouter, Body, Request, Response, HTTPException, status
from dotenv import dotenv_values
from .models import User, LoginUser, all_users, Likes, likes_get, all_likes, individual_data, UserUpdate
from .config import user_likedb, userdb
from bson import ObjectId
import bcrypt

app = FastAPI()
router = APIRouter()
encrypt = bcrypt.gensalt()

@router.get("/users")
async def get_all_users():
    try:
        data = list(userdb.find())
        return all_users(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {e}")

@router.post("/users")
async def create_user(new_user: User):
    try:
        enc_user = new_user.dict()
        enc_user["password"] = bcrypt.hashpw(new_user.password.encode(encoding="utf-8"), encrypt)
        resp = userdb.insert_one(dict(enc_user))
        return individual_data(userdb.find_one({"_id": resp.inserted_id}))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        data = userdb.find_one({"_id": ObjectId(user_id)})
        if not data:
            raise HTTPException(status_code=404, detail="User not found")
        return individual_data(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")

@router.put("/users/{user_id}")
def update_user(user_id: str, payload: UserUpdate):
    upuser = userdb.find_one({"_id": ObjectId(user_id)})
    if not upuser:
        raise HTTPException(status_code=404, detail="User not found")
    updated = userdb.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": payload.dict(exclude_unset=True)},
        return_document=True
    )
    return individual_data(updated)

@router.post("/login")
async def login_user(user: LoginUser):
    try:
        data = userdb.find_one({"email": user.email})
        if not data:
            raise HTTPException(status_code=404, detail="User not found")
        if not bcrypt.checkpw(user.password.encode(encoding="utf-8"), data["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return individual_data(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")
    
@router.post("/likes")
async def make_like(likes: Likes):
    try:
        likes_create = likes.dict()
        resp = user_likedb.insert_one(dict(likes_create))
        return {"status_code": 200, "id": str(resp.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")
    
@router.get("/likes/{uid}")
async def get_likes(uid: str):
    try:
        data = list(user_likedb.find({"uid": uid}))
        return all_likes(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")

app.include_router(router)