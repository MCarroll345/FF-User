from fastapi import FastAPI, APIRouter, Body, Request, Response, HTTPException, status, File, UploadFile
from fastapi.responses import FileResponse
from ..models import Likes, uploadImage
from ..config import userdb, cdb, user_imgdb
import requests
import base64
from bson import ObjectId
import os
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel, Image as VertexImage

vertexai.init(project="fitfinder-491412", location="us-central1")
model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")
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
        clothing_images = img_return(item_urls)
        prompt = "Dress the person in all of the provided clothing items together as a complete outfit. Keep the person's face, body, and likeness exactly the same."
        if not userIMG:
            raise HTTPException(status_code=400, detail="No user image found")
        user_image = VertexImage(image_bytes=base64.b64decode(userIMG["base64"]))
        images = model.edit_image(
            base_image=user_image,
            prompt=prompt,
            reference_images=clothing_images,
            number_of_images=1,
            safety_filter_level="block_some",
            person_generation="allow_adult",
        )
        return Response(content=images[0]._image_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {e}")

def img_return(item_urls):
    return [VertexImage(image_bytes=requests.get(item["url"]).content) for item in item_urls]