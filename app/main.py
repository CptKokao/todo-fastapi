from fastapi import FastAPI,status, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models.base import Base
from db.session import engine
from api.routers.tasks import router as task_router

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router=task_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
)




