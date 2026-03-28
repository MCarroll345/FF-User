from fastapi import FastAPI, APIRouter, Body, Request, Response, HTTPException, status, File, UploadFile
from fastapi.responses import FileResponse
from ..models import Likes, uploadImage
from ..config import userdb, cdb, user_imgdb
import PIL.Image
from io import BytesIO
import requests
import time
import base64
from google import genai
from google.genai import types
from bson import ObjectId
import os

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-3.1-flash-image-preview"

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

        prompt = (
            "Generate a full-body fashion photo of the person shown in this image "
            "wearing all of the clothing items also shown as a complete outfit. "
            "Preserve the person's face, skin tone, and body exactly."
        )

        user_b64 = userIMG["base64"] if userIMG else None

        contents = [prompt]
        if user_b64:
            contents.append(PIL.Image.open(BytesIO(base64.b64decode(user_b64))).convert("RGB"))
        for _, img_bytes, _ in image_files:
            img_bytes.seek(0)
            contents.append(PIL.Image.open(img_bytes).convert("RGB"))

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE", "TEXT"]
                    )
                )
                break
            except Exception as e:
                err = str(e)
                if "429" in err and attempt < 2:
                    import re
                    match = re.search(r'retryDelay.*?(\d+)s', err)
                    wait = int(match.group(1)) + 5 if match else 60
                    time.sleep(wait)
                else:
                    raise

        image_data = next(
            (part.inline_data.data for part in response.candidates[0].content.parts
             if part.inline_data and part.inline_data.mime_type.startswith("image")),
            None
        )
        if not image_data:
            raise HTTPException(status_code=500, detail="No image returned from model")

        return Response(content=image_data, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {e}")

def img_return(item_urls):
    files = []
    for item in item_urls:
        img_bytes = BytesIO(requests.get(item["url"]).content)
        files.append((f"{item['id']}.png", img_bytes, "image/png"))
    return files
