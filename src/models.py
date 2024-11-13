from datetime import datetime
from typing import List, Union
from sqlmodel import Field, Relationship, SQLModel


class RecordExtender():
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now(
    ), sa_column_kwargs={"onupdate": lambda: datetime.now()})


class Diagram(SQLModel, RecordExtender, table=True):
    __tablename__ = "diagrams"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: str = Field(index=True)
    config: str = Field()
    project_id: int = Field(foreign_key="project.id")

class UserProject(SQLModel, RecordExtender, table=True):
    manager: bool = Field(default=False)
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    project_id: int = Field(foreign_key="project.id", primary_key=True)

class UserOrganization(SQLModel, RecordExtender, table=True):
    manager: bool = Field(default=False)
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    organization_id: int | None = Field(foreign_key="organization.id")

    user: "User" = Relationship(back_populates="organization_link")
    organization: "Organization" = Relationship(back_populates="user_links")

class User(SQLModel, RecordExtender, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    password: str = Field()
    is_active: bool = Field(default=True)

    projects: list["Project"] = Relationship(back_populates="users", link_model=UserProject)

    organization_link: list[UserOrganization] = Relationship(back_populates="user")

class Project(SQLModel, RecordExtender, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field()
    description: str = Field()
    status_code: int = Field(foreign_key="projectstatuscode.id", default=1)
    owner_id: int = Field(foreign_key="organization.id")
    owner_is_org: bool = Field(default=False)
    
    users : list[User] = Relationship(back_populates="projects", link_model=UserProject)

class Organization(SQLModel, RecordExtender, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field()
    description: str = Field()
    owner_id: int = Field(foreign_key="user.id")

    user_links: List[UserOrganization] = Relationship(back_populates="organization")

class ProjectStatusCode(SQLModel, RecordExtender, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: str = Field(default="In Progress")

class Token(SQLModel, RecordExtender, table=False):
    id: int | None = Field(default=None, primary_key=True)
    access_token: str
    token_type: str

class TokenData(SQLModel, RecordExtender, table=False):
    id: int | None = Field(default=None, primary_key=True)
    username: Union[str, None] = None

class LastUsedDiagram(SQLModel, RecordExtender, table=True):
    id: int | None = Field(default=None, primary_key=True)
    diagram_id : int = Field(foreign_key="diagrams.id")
    user_id: int = Field(foreign_key="user.id")
