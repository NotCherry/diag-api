from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from src.util import get_db

from src.crud import  get_current_user, create_organization, create_project_in_organization, get_organization_by_id, get_projects_by_organization
import src.models as models

router = APIRouter()


@router.get("/organization/{org_id}")
def get_organization(org_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return get_organization_by_id(db, current_user.id, org_id)

@router.post("/organization")
def create_org(org: models.Organization, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return create_organization(db, org, current_user)
    
class OrgProjectData(BaseModel):
    org_id: int
    project: models.Project 

@router.post("/organization/project")
def create_project_in_org(data: OrgProjectData, current_user: Annotated[models.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    return create_project_in_organization(db, data.org_id, data.project, current_user)

@router.get("/organization/{org_id}/project")
def get_projects_in_org(org_id: int, current_user: Annotated[models.User, Depends(get_current_user)], db: Session = Depends(get_db)):
    return get_projects_by_organization(db, org_id, current_user.id)


