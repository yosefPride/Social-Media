import os
from collections.abc import AsyncGenerator, Generator

import httpx
import pytest
from fastapi.testclient import TestClient

os.environ["ENV_STATE"] = "test"

from app.database import database, user_table
from app.main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture(autouse=True)
async def db(anyio_backend) -> AsyncGenerator:
    await database.connect()
    yield
    await database.disconnect()


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url=client.base_url,
    ) as ac:
        yield ac


@pytest.fixture()
async def registered_user(async_client: httpx.AsyncClient) -> dict:
    user_details = {"email": "test@example.net", "password": "1234"}
    await async_client.post("register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details


@pytest.fixture()
async def logged_in_token(
    async_client: httpx.AsyncClient, registered_user: dict
) -> str:
    response = await async_client.post("/login", json=registered_user)
    return response.json()["access_token"]
