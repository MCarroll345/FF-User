from fastapi import FastAPI, APIRouter, Body, Request, Response, HTTPException, status
from fastapi.responses import FileResponse
from .routes.genRoute import grouter
from .routes.userRoute import urouter

app = FastAPI()

app.include_router(grouter)
app.include_router(urouter)