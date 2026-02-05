"""
Authentication and User Management
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from passlib.context import CryptContext

from app.models import User, Company
from app.database import get_session

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/register")
async def register_user(
    email: str,
    password: str,
    full_name: str,
    company_id: int,
    session: Session = Depends(get_session)
):
    """Register new user"""
    # Check if user exists
    statement = select(User).where(User.email == email)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Verify company exists
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Create user
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        company_id=company_id
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {"message": "User registered successfully", "user_id": user.id}

@router.post("/login")
async def login(
    email: str,
    password: str,
    session: Session = Depends(get_session)
):
    """Login user"""
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is disabled")
    
    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "company_id": user.company_id,
            "is_admin": user.is_admin
        }
    }

@router.get("/users", response_model=List[User])
async def list_users(
    company_id: int,
    session: Session = Depends(get_session)
):
    """List all users for a company"""
    statement = select(User).where(User.company_id == company_id)
    users = session.exec(statement).all()
    return users

@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, session: Session = Depends(get_session)):
    """Get user by ID"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    full_name: str = None,
    is_active: bool = None,
    is_admin: bool = None,
    session: Session = Depends(get_session)
):
    """Update user"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if full_name:
        user.full_name = full_name
    if is_active is not None:
        user.is_active = is_active
    if is_admin is not None:
        user.is_admin = is_admin
    
    session.commit()
    session.refresh(user)
    
    return {"message": "User updated successfully", "user": user}