import os
from typing import Annotated
from fastapi import Depends, HTTPException
import jwt

from sqlmodel import Session, select

from src.util import get_password_hash
from . import models
from .util import get_db, oauth2_scheme
from .exceptions import credentials_exception



async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)) -> models.User:
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"),
                             algorithms=[os.getenv("ALGORITHM")])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception
        token_data = models.TokenData(username=username)

    except jwt.InvalidTokenError:
        raise credentials_exception
    user = get_user_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[models.User, Depends(get_current_user)],
):
    if current_user.is_active is False:
        raise HTTPException(status_code=400, detail="Inactive user")

    user = {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
    }
    return user

def create_user(db: Session, email: str, username: str, password: str):
    hashed_password = get_password_hash(password)

    if hashed_password == '':
        raise HTTPException(status_code=400, detail="Password is empty")

    db_user = models.User(email=email, username=username,
                          password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_user_project(db: Session, project: models.Project, user_id: int):
    user = db.exec(select(models.User).where(models.User.id == user_id)).first()
    db_project = models.Project(owner_id=user_id,users=[user], **project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def create_diagram_in_project(db: Session, diagram: models.Diagram, project_id: int, user_id:int):
    db_diagram = models.Diagram(**diagram.model_dump(), owner_id=project_id)
    db.add(db_diagram)
    db.commit()
    db.refresh(db_diagram)


    db_last_diagram = models.LastUsedDiagram(diagram_id=db_diagram.id, user_id=user_id )
    db.add(db_last_diagram)
    db.commit()
    db.refresh(db_last_diagram)
    return db_diagram

def get_last_diagrams(db: Session, user_id):
    try:
        data = db.exec(select(models.Diagram).where(models.Diagram.id == models.LastUsedDiagram.diagram_id).where(models.LastUsedDiagram.user_id == user_id).order_by(models.LastUsedDiagram.updated_at.desc()).limit(5)).all()
        return data
    except Exception:
        print("Error")
def get_projects_by_user(db: Session, id: int):
    return db.exec(select(models.Project).join(models.UserProject).where(models.UserProject.user_id == id)).all()

def get_users(db: Session):
    return db.exec(select(models.User)).all()

def get_user_id(db: Session, id: int):
    return db.exec(select(models.User).where(models.User.id == id)).first()

def get_user_email(db: Session, email: str):
    return db.exec(select(models.User).where(models.User.email == email)).first()

def get_user_username(db: Session, username: str):
    return db.exec(select(models.User).where(models.User.username == username)).first()


def get_diagrams_in_project(db: Session, id: int, user_id: int):
    access = db.exec(select(models.UserProject).where(models.UserProject.user_id == user_id)).first()

    if access is None:
        raise HTTPException(status_code=400, detail="User does not have access to the project")
    
    return db.exec(select(models.Diagram).where(models.Diagram.project_id == id)).all()

def get_diagram_by_id(db: Session, id: int, user_id: int):
    st = db.exec(select(models.Diagram).where(models.Diagram.id == id))
    diagram = st.all()[0]
    
    access = db.exec(select(models.UserProject).where(models.UserProject.user_id == user_id, models.UserProject.project_id == diagram.project_id)).first()
    if access is None:
        raise HTTPException(status_code=400, detail="User does not have access to the project")
    
    if (db.exec(select(models.LastUsedDiagram).order_by(models.LastUsedDiagram.updated_at.desc())).first().diagram_id != id):
        db_last_diagram = models.LastUsedDiagram(diagram_id=diagram.id, user_id=user_id )
        db.add(db_last_diagram)
        db.commit()
        db.refresh(db_last_diagram)

    print("We did it diagram:", diagram, st)
    return diagram

def update_diagram_config(db: Session, diagram_id: int, diagram_config: str, diagram_image: str, user_id: int):
    diagram: models.Diagram = db.exec(select(models.Diagram).where(models.Diagram.id == diagram_id)).first()
    if diagram == None:
        raise HTTPException(404, "Not found")
    
    project: models.Project = db.exec(select(models.Project).where(models.Project.id == diagram.project_id)).first() 
    access = not project.owner_is_org and project.owner_id == user_id
    if not access:
        raise HTTPException(status_code=400, detail="User does not have access to the project")  
    
    diagram.config = diagram_config
    diagram.image = diagram_image
    db.add(diagram)
    db.commit()
    db.refresh(diagram)

    return diagram

def get_project_by_id(db: Session, id: int, user_id: int):
    access = db.exec(select(models.UserProject).where(models.UserProject.user_id == user_id)).first()
    
    if access is None:
        raise HTTPException(status_code=400, detail="User does not have access to the project")
    
    return db.exec(select(models.Project).where(models.Project.id == id)).first()

def get_projects_by_organization(db: Session, org_id: int, user_id: int):
    access = db.exec(select(models.UserOrganization).where(models.UserOrganization.user_id == user_id)).first()

    if access is None:
        raise HTTPException(status_code=400, detail="User does not have access to the organization")
    

    return db.exec(select(models.Project).where(models.Project.owner_id == org_id).where(models.Project.owner_is_org == True)).all()

def get_organization_by_id(db: Session, user_id: int, org_id: int):
    access = db.exec(select(models.UserOrganization).where(models.UserOrganization.user_id == user_id)).first()

    if access is None:
        raise HTTPException(status_code=400, detail="User does not have access to the organization")

    db_org = db.exec(select(models.Organization).where(models.Organization.id == org_id)).first()

    return db_org

def create_organization(db: Session,org: models.Organization, user: models.User):
    db_org = models.Organization(name=org.name, description=org.description, owner_id=user.id)
    org_link = models.UserOrganization(user=user, organization=db_org, manager=True)

    db.add(org_link)
    db.commit()
    db.refresh(org_link)
    return org_link.organization

def create_project_in_organization(db: Session, org_id: str, proj: models.Project, user):

    is_manager = db.exec(select(models.UserOrganization).where(models.UserOrganization.user_id == user.id)).first().manager

    if not is_manager:
        raise HTTPException(status_code=400, detail="User is not a manager of the organization")

    db_project= models.Project(owner_id=org_id, owner_is_org=True, **proj.model_dump(exclude={"owner_is_org"}))
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project

def create_generated_conted(db: Session, content: models.GeneratedContent):
    db.add(content)
    db.commit()
    db.refresh(content)

def create_executed_config(db: Session, diagram_id: int, config: str):
    config = models.ExecutedDiagramConfig(diagram_id=diagram_id, config=config)
    db.add(config)
    db.commit()
    db.refresh(config)

    return config
