# app/schemas.py
from pydantic import BaseModel, EmailStr, constr, conint
from typing import Optional

class User(BaseModel):
    email:str
    password:str
    first_name:str
    last_name:str

class LoginUser(BaseModel):
    email:str
    password:str

class Likes(BaseModel):
    uid: str
    item_id1: Optional[str] = None
    item_id2: Optional[str] = None
    item_id3: Optional[str] = None
    item_id4: Optional[str] = None

def individual_data(user):
    return{
        "id": str(user["_id"]),
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"]
    }

def likes_get(like):
    return{
        "id": str(like["_id"]),
        "uid": str(like["uid"]),
        "item_id1": like["item_id1"],
        "item_id2": like["item_id2"],
        "item_id3": like["item_id3"],
        "item_id4": like["item_id4"],
    }

def all_users(users):
    return [individual_data(user) for user in users]

def all_likes(likes):
    return [likes_get(like) for like in likes]