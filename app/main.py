import logging
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler

from app.database import database
from app.logging_conf import configure_logging
from app.routers.post import router as post_router
from app.routers.upload import router as upload_router
from app.routers.user import router as user_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)

app.include_router(post_router)
app.include_router(user_router)
app.include_router(upload_router)


# will log every http exception that gets raised in the app.
@app.exception_handler(HTTPException)
async def http_exception_handle_logging(request, exception):
    logger.error(f"HTTPException: {exception.status_code} {exception.detail}")
    return await http_exception_handler(request, exception)
