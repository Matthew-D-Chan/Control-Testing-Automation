from fastapi import FastAPI
from .api.items import router as items_router
from .api.sessions import router as sessions_router

app = FastAPI(title="CIBC Controling Testing App")

# Include your API routes under /api
app.include_router(items_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")

# Potential landing page
@app.get("/")
def read_root():
    return {"message": "Backend is running!"}