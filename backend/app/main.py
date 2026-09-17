import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api import (
    auth,
    dashboard,
    health,
    instructor,
    platform,
    runtime_components,
    runtime_controls,
    runtime_debrief,
    runtime_platform,
    runtime_review,
    runtime_rollout,
    runtime_round_control,
)
from app.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup complete")
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="MIS Simulation",
        description="Management Information Systems simulation platform",
        version="0.2.0",
        lifespan=lifespan,
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(instructor.router, prefix="/api")
    app.include_router(platform.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
    app.include_router(runtime_platform.router, prefix="/api")
    app.include_router(runtime_components.router, prefix="/api")
    app.include_router(runtime_rollout.router, prefix="/api")
    app.include_router(runtime_review.router, prefix="/api")
    app.include_router(runtime_debrief.router, prefix="/api")
    app.include_router(runtime_controls.router, prefix="/api")
    app.include_router(runtime_round_control.router, prefix="/api")

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request, exc: IntegrityError):
        """Catch unhandled DB constraint violations and return a user-friendly 409."""
        detail = str(exc.orig) if exc.orig else str(exc)
        if "foreign key" in detail.lower() or "violates foreign key" in detail.lower():
            msg = "Cannot complete this action — other records still reference this item. Remove related data first."
        elif "unique" in detail.lower() or "duplicate" in detail.lower():
            msg = "A record with this value already exists."
        else:
            msg = "A database constraint prevented this action."
        logger.warning("IntegrityError on %s %s: %s", request.method, request.url.path, detail)
        return JSONResponse(status_code=409, content={"detail": msg})

    return app


app = create_app()
