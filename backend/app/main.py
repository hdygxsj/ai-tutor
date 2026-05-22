from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.agent import router as agent_router
from app.api.routes.assignments import router as assignments_router
from app.api.routes.courses import router as courses_router
from app.api.routes.health import router as health_router
from app.api.routes.learning import router as learning_router
from app.api.routes.runtime import router as runtime_router
from app.api.routes.settings import router as settings_router
from app.db.migrate import run_migrations


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    yield


app = FastAPI(title="AI Dream API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(courses_router, prefix="/api")
app.include_router(learning_router, prefix="/api")
app.include_router(assignments_router, prefix="/api")
app.include_router(runtime_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
