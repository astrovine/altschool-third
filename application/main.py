from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from application.middleware.logging_middleware import LoggingMiddleware
from application.routers.v1 import admin, auth, events, invitations, rsvps
from application.utilities.config import settings
from application.utilities.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Application startup", extra={"debug": settings.debug})
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(exist_ok=True)
    yield
    logger.info("Application shutdown")


def create_application() -> FastAPI:
    app = FastAPI(
        title="Event RSVP API",
        description="Production-grade event platform for creating events and managing RSVPs",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    app.add_middleware(LoggingMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/v1")
    app.include_router(events.router, prefix="/v1")
    app.include_router(rsvps.router, prefix="/v1")
    app.include_router(invitations.router, prefix="/v1")
    app.include_router(admin.router, prefix="/v1")

    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        return {"status": "healthy", "version": "2.0.0"}

    return app


app = create_application()
