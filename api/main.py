from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from .routes import router
from .model_loader import get_model_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load model
    model_manager = get_model_manager()
    model_manager.initialize()
    yield
    # Shutdown: cleanup

app = FastAPI(
    title='Traffic Accident Severity Prediction API',
    description='Predict accident severity using ML model',
    version='1.0.0',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routes from routes.py
app.include_router(router)
