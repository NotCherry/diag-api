from dotenv import load_dotenv
from typing import Annotated
from fastapi import Depends, FastAPI

from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, Session, select

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.crud import get_current_user

from src.tests.initialize_data import init_status_code

from .routers import limiter
from .routers import auth
from .routers import graph_processor
from .routers import user
from .routers import project
from .routers import organizations
from .routers import diagram
from .routers import recent
from . import models
from .database import engine

load_dotenv()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    if (len(Session(engine).exec(select(models.ProjectStatusCode)).all()) == 3):
        return
    with Session(engine) as session:
        init_status_code(session)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(graph_processor.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(project.router)
app.include_router(organizations.router)
app.include_router(diagram.router)
app.include_router(recent.router)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
async def get(user: Annotated[str, Depends(get_current_user)]):
    return JSONResponse(content={"message": "Hello, World"}, status_code=200)
