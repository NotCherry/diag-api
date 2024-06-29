from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.crud import get_current_user, get_diagram_by_id
from src.models import User
from src.util import get_db

router = APIRouter()

@router.get("/diagram/{diagram_id}")
def diagrams(diagram_id:int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_diagram_by_id(db, diagram_id ,user.id)
