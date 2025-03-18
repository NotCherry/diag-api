from dotenv import load_dotenv
from typing import Annotated
from fastapi import Depends, FastAPI, Request, WebSocket
import sentry_sdk
import time

from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import SQLModel, Session, select

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.crud import get_current_user

from src.tests.initialize_data import init_node_type, init_status_code

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

# sentry_sdk.init(
#     dsn="https://8ac3a0361c80254fba65ac1194c102ff@o4508319072518144.ingest.de.sentry.io/4508319140347984",
#     traces_sample_rate=1.0,
#     _experiments={
#         "continuous_profiling_auto_start": True,
#     },
# )

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    if (len(Session(engine).exec(select(models.ProjectStatusCode)).all()) == 3):
        return
    with Session(engine) as session:
        init_status_code(session)
    if (len(Session(engine).exec(select(models.NodeType)).all()) == 2):
        return
    with Session(engine) as session:
        init_node_type(session)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    body = await request.body()
    print(body.decode('utf-8'))
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


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

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         data = await websocket.receive_text()
        
#         await websocket.send_text(f"You sent: {data}")