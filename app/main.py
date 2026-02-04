from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve frontend
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")

# Catch-all route for SPA (Single Page Application)
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # Don't catch API routes
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
        return {"error": "Not found"}
    return FileResponse("frontend/index.html")
