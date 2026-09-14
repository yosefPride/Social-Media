import datetime
import logging
from typing import Annotated

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


credentials_exception = HTTPException(
    status_code=401,
    detail="Could not validate credentials",
    headers={"www.authenticate": "Bearer"},
)


# for testing
def access_token_expire_minutes() -> int:
    return 30


def create_Access_token(email: str):
    logger.debug("Creating access token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire}
    encoded_jwt = jwt.encode(jwt_data, key=config.JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


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
        raise credentials_exception
    if not verify_password(password, user.password):
        raise credentials_exception
    return user


async def get_current_user(token: Annotated[str, Depends(Oauth2_scheme)]):
    try:
        payload = jwt.decode(token, key=config.JWT_SECRET, algorithms=ALGORITHM)
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
            headers={"www.authenticate": "Bearer"},
        ) from e
    except JWTError as e:
        raise credentials_exception from e

    user = await get_user_by_email(email=email)
    if user is None:
        raise credentials_exception
    return user
