import logging

from passlib.context import CryptContext

from app.database import database, user_table

logger = logging.getLogger(__name__)

# defining the hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"])


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
