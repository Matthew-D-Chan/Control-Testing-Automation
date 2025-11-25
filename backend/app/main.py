from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from .api.items import router as items_router
from .api.sessions import router as sessions_router
from .schema.schemas import sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    session_id = "sess_123"
    if session_id not in sessions:
        sessions[session_id] = {
            "createdAt": datetime.now(timezone.utc),
            "messages": [],
        }
        print(f"[startup] Dummy session created with id: {session_id}")
    yield
    print("[shutdown] App shutting down...")


# FastAPI connection point
app = FastAPI(title="CIBC Controling Testing App", lifespan=lifespan) # Literally takes the lifespan context manager def from above

# Include your API routes under /api
app.include_router(items_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")

# Potential landing page
@app.get("/")
def read_root():
    return {"message": "Landing page placeholder"}