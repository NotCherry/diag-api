from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.crud import get_current_user, get_last_diagrams
from src.models import User
from src.util import get_db

router = APIRouter()

@router.get("/recent/diagrams")
def diagrams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_last_diagrams(db, user.id)
