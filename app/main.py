"""
FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables
from app.api import auth, companies, materials, purchases, make_webhooks

app = FastAPI(
    title="PVApp Backend",
    description="Multi-company materials management system with eFactura.ro integration",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(materials.router)
app.include_router(purchases.router)
app.include_router(make_webhooks.router)

@app.on_event("startup")
def on_startup():
    """Initialize database on startup"""
    create_db_and_tables()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PVApp Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}