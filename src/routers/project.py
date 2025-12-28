from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.models import Diagram, Project, User
from src.crud import (
    create_diagram_in_project,
    create_user_project,
    get_current_user,
    get_diagrams_in_project,
    get_project_by_id,
    get_projects_by_user,
)
from src.models import Project
from src.util import get_db


router = APIRouter()


@router.post("/project")
def db_create_user_project(
    project: Project,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    print("PROJECT!!!! ", project)
    return create_user_project(db, project, user.id)


@router.get("/project")
def projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_projects_by_user(db, user.id)


@router.get("/project/{project_id}")
def projects(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_project_by_id(db, project_id, user.id)


@router.get("/project/{project_id}/diagram")
def db_create_user_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_diagrams_in_project(db, project_id, user.id)


@router.post("/project/{project_id}/diagram")
def db_create_user_project_diagram(
    project_id: int,
    diagram: Diagram,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return create_diagram_in_project(db, diagram, project_id, user.id)
