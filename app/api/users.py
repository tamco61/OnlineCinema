from fastapi import  APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import user as schemas
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.post("/register", response_model=schemas.UserCreate)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    pass


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    pass


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user = Depends(user_service.get_current_user)):
    return current_user

