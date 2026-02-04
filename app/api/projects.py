from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models import Project, User
from app.database import get_session
from app.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/projects", tags=["Projects"])

# Schemas
class ProjectCreate(BaseModel):
    name: str
    client_name: str
    client_address: str
    system_kw: float

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    client_address: Optional[str] = None
    system_kw: Optional[float] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    client_name: str
    client_address: str
    system_kw: float
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# Endpoints
@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    project_data: ProjectCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    db_project = Project(**project_data.dict())
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@router.get("/", response_model=List[ProjectResponse])
def get_projects(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all projects, optionally filter by status"""
    query = select(Project)
    if status:
        query = query.where(Project.status == status)
    
    projects = session.exec(query.offset(skip).limit(limit)).all()
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get project by ID"""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update project"""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_data.dict(exclude_unset=True)
    
    # If status is being set to COMPLETED, set completed_at
    if "status" in update_data and update_data["status"] == "COMPLETED":
        project.completed_at = datetime.utcnow()
    
    for key, value in update_data.items():
        setattr(project, key, value)
    
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete project"""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    session.delete(project)
    session.commit()
    return {"message": "Project deleted successfully"}
