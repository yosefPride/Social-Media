import logging

from fastapi import APIRouter, HTTPException

from app.database import database, user_table
from app.models.user import UserIn
from app.security import get_password_hash, get_user_by_email

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=201)
async def register(user: UserIn):
    if await get_user_by_email(user.email):
        raise HTTPException(
            status_code=400,
            detail="A user with that email already exists",
        )
    password_hash = get_password_hash(user.password)
    query = user_table.insert().values(email=user.email, password=password_hash)

    logger.debug(query)

    await database.execute(query)
    return {"detail": "user created"}


@router.post("/login", status_code=200)
async def login(user: UserIn):
    if not await get_user_by_email(user.email):
        raise HTTPException(
            status_code=401,
            detail="Wrong email or password",
        )
