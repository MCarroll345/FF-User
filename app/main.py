from fastapi import FastAPI, APIRouter, Body, Request, Response, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .routes.genRoute import grouter
from .routes.userRoute import urouter

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(grouter)
app.include_router(urouter)