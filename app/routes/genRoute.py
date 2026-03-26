from fastapi import FastAPI, APIRouter, Body, Request, Response, HTTPException, status, File, UploadFile
from fastapi.responses import FileResponse
from ..models import Likes, uploadImage
from ..config import userdb, cdb, user_imgdb
from PIL import Image
from io import BytesIO
import requests
from openai import OpenAI
import base64
from bson import ObjectId
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
grouter = APIRouter()

@grouter.post("/{uid}/upload")
async def upload_image(uid: str, file: UploadFile):
    try:
        b64 = base64.b64encode(await file.read()).decode('utf-8')
        user_imgdb.insert_one({"uid": uid, "base64": b64})
        return {"status": "Image uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {e}")

@grouter.post("/generate")
async def generate_img(likes: Likes):
    try:
        ids = [likes.item_id1, likes.item_id2, likes.item_id3, likes.item_id4]
        item_urls = []
        userIMG = user_imgdb.find_one({"uid": likes.uid})
        for cloth in cdb.list_collection_names():
            for item_id in filter(None, ids):
                item = cdb[cloth].find_one({"_id": ObjectId(item_id)})
                if item:
                    item_urls.append({"id": item_id, "url": item["img_url"]})
        image_files = img_return(item_urls)
        if userIMG:
            image_files.insert(0, ("user.webp", BytesIO(base64.b64decode(userIMG["base64"])), "image/webp"))
        result = client.images.edit(
            model="gpt-image-1",
            prompt="Generate an image of the person in user.webp wearing all of these clothing items together as an outfit. Focus on making the person look as much like their reference photo as possible. NEVER change the face",
            image=image_files
        )
        image_base64 = result.data[0].b64_json

        image_bytes = base64.b64decode(image_base64)
        return Response(content=image_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {e}")

def img_return(item_urls):
    files = []
    for item in item_urls:
        img_bytes = BytesIO(requests.get(item["url"]).content)
        files.append((f"{item['id']}.png", img_bytes, "image/png"))
    return files