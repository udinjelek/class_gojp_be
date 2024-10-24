from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.ai import assistants
from routers.classgojp import auth

from routers.classgojp import auth
from db import get_db  # Import get_db from db.py
from config import Config  # Import Config class from config.py
app = FastAPI()
app.config = {
    'SQLALCHEMY_DATABASE_URI': Config.SQLALCHEMY_DATABASE_URI,
    'SQLALCHEMY_TRACK_MODIFICATIONS': Config.SQLALCHEMY_TRACK_MODIFICATIONS
}


# Define your allowed origins
origins = [
    "http://localhost:4001",
    "http://127.0.0.1:4001",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://class-gojp.polaris.my.id",
    # Add other origins as needed
]

# Add CORS middleware to your FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows requests from these origins
    allow_credentials=True,
    allow_methods=["*"],    # Allows all HTTP methods
    allow_headers=["*"],    # Allows all HTTP headers
)

# app.include_router(assistants.router, prefix="/ai")
app.include_router(auth.router, prefix="/classgojp")
