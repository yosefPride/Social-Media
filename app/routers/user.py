import logging

from fastapi import APIRouter, HTTPException

from app.database import database, user_table
from app.models.user import UserIn
from app.security import (
    authenticate_user,
    create_Access_token,
    get_password_hash,
    get_user_by_email,
)

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


@router.post("/login")
async def login(user: UserIn):
    user = await authenticate_user(user.email, user.password)
    access_token = create_Access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}
