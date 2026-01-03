import pytest
from httpx import AsyncClient


class TestRegister:
    async def test_register_success(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient) -> None:
        await client.post(
            "/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password123",
                "full_name": "User One",
            },
        )

        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password456",
                "full_name": "User Two",
            },
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "full_name": "Invalid User",
            },
        )

        assert response.status_code == 422

    async def test_register_weak_password(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "short",
                "full_name": "Weak User",
            },
        )

        assert response.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient) -> None:
        await client.post(
            "/v1/auth/register",
            json={
                "email": "loginuser@example.com",
                "password": "loginpassword123",
                "full_name": "Login User",
            },
        )

        response = await client.post(
            "/v1/auth/login",
            data={"username": "loginuser@example.com", "password": "loginpassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_email(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/auth/login",
            data={"username": "nonexistent@example.com", "password": "password"},
        )

        assert response.status_code == 401

    async def test_login_invalid_password(self, client: AsyncClient) -> None:
        await client.post(
            "/v1/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "correctpassword",
                "full_name": "Wrong Pass User",
            },
        )

        response = await client.post(
            "/v1/auth/login",
            data={"username": "wrongpass@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401


class TestRefreshToken:
    async def test_refresh_success(self, client: AsyncClient) -> None:
        await client.post(
            "/v1/auth/register",
            json={
                "email": "refreshuser@example.com",
                "password": "refreshpassword123",
                "full_name": "Refresh User",
            },
        )

        login_response = await client.post(
            "/v1/auth/login",
            data={"username": "refreshuser@example.com", "password": "refreshpassword123"},
        )
        tokens = login_response.json()

        response = await client.post(
            "/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401


class TestGetMe:
    async def test_get_me_success(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.get("/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "authuser@example.com"
        assert "id" in data

    async def test_get_me_unauthorized(self, client: AsyncClient) -> None:
        response = await client.get("/v1/auth/me")

        assert response.status_code == 401
