from fastapi import FastAPI, APIRouter, Body, Request, Response, HTTPException, status
from dotenv import dotenv_values
from .models import User, LoginUser, all_users, Likes, likes_get, all_likes
from .config import user_likedb, userdb
import bcrypt

encrypt = bcrypt.gensalt()

app = FastAPI()
router = APIRouter()

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
        enc_user["password"] = bcrypt.hashpw(b'enc_user["password"]', encrypt)
        resp = userdb.insert_one(dict(enc_user))
        return {"status_code": 200, "id": str(resp.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")

@router.post("/login")
async def login_user(user: LoginUser):
    try:
        enc_user = user.dict()
        doc = userdb.find_one({"email": enc_user["email"]})
        if not doc:
            raise HTTPException(status_code=404, detail="User not found")
        if not bcrypt.checkpw(b'enc_user["password"]', doc["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"status_code": 200, "id": str(doc["_id"])}
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
    
@router.get("/{uid}/likes")
async def get_likes(uid: str):
    try:
        data = list(user_likedb.find({"uid": uid}))
        return all_likes(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")

app.include_router(router)