from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from sqlmodel import SQLModel, Session

from src.util import get_db


from ..crud import (
    get_current_active_user,
    get_current_user,
    get_user_email,
    get_user_id,
    get_users,
    create_user,
    get_user_username,
)
from ..models import User

router = APIRouter()


@router.get("/users/{id}")
def user(id: int, db: Session = Depends(get_db)):
    user = get_user_id(db, id)
    user.password = None
    return user


@router.get("/users", response_model=list[User])
def users(
    user: Annotated[str, Depends(get_current_user)], db: Session = Depends(get_db)
):
    return get_users(db)


@router.post("/users")
def db_create_user(user: User, db: Session = Depends(get_db)):
    db_user = get_user_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = get_user_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = create_user(
        db, email=user.email, username=user.username, password=user.password
    )
    new_user.password = None
    return new_user


@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
