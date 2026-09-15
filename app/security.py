import datetime
import logging
from typing import Annotated, Literal

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.config import config
from app.database import database, user_table

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
Oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
# defining the hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"])


def create_credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=detail,
        headers={"www.authenticate": "Bearer"},
    )


# for testing
def access_token_expire_minutes() -> int:
    return 30


def confirm_token_expire_minutes() -> int:
    return 1440  # 24 hours


def create_access_token(email: str):
    logger.debug("Creating access token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(jwt_data, key=config.JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def create_confirmation_token(email: str):
    logger.debug("Creating confirmation token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirm_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "confirmation"}
    encoded_jwt = jwt.encode(jwt_data, key=config.JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def get_subject_for_token_type(
    token: str, type: Literal["access", "confirmation"]
) -> str:
    try:
        payload = jwt.decode(token, key=config.JWT_SECRET, algorithms=ALGORITHM)
    except ExpiredSignatureError as e:
        raise create_credentials_exception("Token has expired") from e
    except JWTError as e:
        raise create_credentials_exception("Invalid token") from e

    email = payload.get("sub")
    if email is None:
        raise create_credentials_exception("Token is missing 'sub' field")

    token_type = payload.get("type")
    if type is None or token_type != type:
        raise create_credentials_exception(
            f"Token has incorrect type, expected '{type}'"
        )

    return email


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def get_user_by_email(email: str):
    query = user_table.select().where(user_table.c.email == email)

    # 'extra' is to add the custom email censoring filter
    logger.debug("Getting user by email", extra={"email": email})
    logger.info(query)

    result = await database.fetch_one(query)
    if result:
        return result


async def authenticate_user(email: str, password: str):
    logger.debug("Authenticating user", extra={"email": email})
    user = await get_user_by_email(email)
    if not user:
        raise create_credentials_exception("Invalid email or password")
    if not verify_password(password, user.password):
        raise create_credentials_exception("Invalid email or password")
    if not user.confirmed:
        raise create_credentials_exception("User has not confirmed email")
    return user


async def get_current_user(token: Annotated[str, Depends(Oauth2_scheme)]):
    email = get_subject_for_token_type(token, "access")
    user = await get_user_by_email(email=email)
    if user is None:
        raise create_credentials_exception("Could not find user for this token")
    return user
