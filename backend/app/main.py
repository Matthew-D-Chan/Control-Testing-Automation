from fastapi import FastAPI
from .api.items import router as items_router
from .api.chats import router as chats_router

app = FastAPI(title="CIBC Controling Testing App")

# Include your API routes under /api
app.include_router(items_router, prefix="/api")
app.include_router(chats_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Backend is running!"}