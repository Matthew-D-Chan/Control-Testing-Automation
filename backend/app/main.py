from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from .api.items import router as items_router
from .api.sessions import router as sessions_router

# FastAPI connection point
app = FastAPI(title="CIBC Controling Testing App") # Literally takes the lifespan context manager def from above

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include your API routes under /api
app.include_router(items_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")

# Potential landing page
@app.get("/")
def read_root():
    return {"message": "Landing page placeholder"}