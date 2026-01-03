import asyncio
import os
from datetime import datetime, timezone
from io import BytesIO
from typing import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from application.main import app
from application.models.user import User, UserRole
from application.utilities.database import Base, get_db
from application.utilities.security import get_password_hash


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        role=UserRole.USER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    await client.post(
        "/v1/auth/register",
        json={
            "email": "authuser@example.com",
            "password": "authpassword123",
            "full_name": "Auth User",
        },
    )
    response = await client.post(
        "/v1/auth/login",
        data={"username": "authuser@example.com", "password": "authpassword123"},
    )
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
async def admin_auth_headers(client: AsyncClient, db_session: AsyncSession) -> dict:
    admin = User(
        email="adminauth@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin Auth User",
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    await db_session.commit()

    response = await client.post(
        "/v1/auth/login",
        data={"username": "adminauth@example.com", "password": "adminpassword123"},
    )
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def sample_event_data() -> dict:
    return {
        "title": "Tech Conference 2026",
        "description": "Annual technology conference featuring industry leaders",
        "date": datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        "location": "Convention Center, Lagos",
        "capacity": "100",
        "is_public": "true",
    }


@pytest.fixture
def sample_flyer() -> BytesIO:
    content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x00\x00\x00\x00:~\x9bU\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x05\xfeD\x00\x00\x00\x00IEND\xaeB`\x82'
    return BytesIO(content)


@pytest.fixture(autouse=True)
def setup_upload_dir() -> Generator[None, None, None]:
    os.makedirs("uploads", exist_ok=True)
    yield
    for file in os.listdir("uploads"):
        if file != ".gitkeep":
            os.remove(os.path.join("uploads", file))
