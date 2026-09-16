import logging

from fastapi import APIRouter, HTTPException, Request

from app import tasks
from app.database import database, user_table
from app.models.user import UserIn
from app.security import (
    authenticate_user,
    create_access_token,
    create_confirmation_token,
    get_password_hash,
    get_subject_for_token_type,
    get_user_by_email,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=201)
async def register(user: UserIn, request: Request):
    if await get_user_by_email(user.email):
        raise HTTPException(
            status_code=400,
            detail="A user with that email already exists",
        )
    password_hash = get_password_hash(user.password)
    query = user_table.insert().values(email=user.email, password=password_hash)

    logger.debug(query)

    await database.execute(query)
    await tasks.send_user_registration_email(
        user.email,
        confirmation_url=request.url_for(
            "confirm_email", token=create_confirmation_token(user.email)
        ),
    )
    return {"detail": "user created. Please confirm your email."}


@router.post("/login")
async def login(user: UserIn):
    user = await authenticate_user(user.email, user.password)
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirm/{token}")
async def confirm_email(token: str):
    email = get_subject_for_token_type(token, "confirmation")
    query = (
        user_table.update().where(user_table.c.email == email).values(confirmed=True)
    )

    logger.info("Confirming a token")
    logger.debug(query)

    await database.execute(query)
    return {"detail": "User confirmed"}
