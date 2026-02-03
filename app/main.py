from fastapi import FastAPI
from app.database import init_db
from app.api import purchases

app = FastAPI(title="PVApp stable backend")

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(purchases.router)

@app.get("/api/v1")
def root():
    return {"ok": True}
