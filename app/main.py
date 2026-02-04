from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.database import init_db
from app.api import purchases, auth, materials, projects, stock, costs, balance, settings, invoices

app = FastAPI(
    title="PV Management App",
    version="1.0.0",
    description="PV installation management system"
)

# Add CORS middleware with configurable origins
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

# Include all routers
app.include_router(auth.router)
app.include_router(materials.router)
app.include_router(projects.router)
app.include_router(stock.router)
app.include_router(costs.router)
app.include_router(balance.router)
app.include_router(settings.router)
app.include_router(invoices.router)
app.include_router(purchases.router)  # Keep legacy purchases endpoint

@app.get("/api/v1")
def root():
    return {"ok": True}
