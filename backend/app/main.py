from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from .api.items import router as items_router
from .api.sessions import router as sessions_router

from data.database import supabase  # <-- our Supabase client


# FastAPI connection point
app = FastAPI(title="CIBC Controling Testing App") # Literally takes the lifespan context manager def from above

# Include your API routes under /api
app.include_router(items_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")

# Potential landing page
@app.get("/")
def read_root():
    return {"message": "Landing page placeholder"}