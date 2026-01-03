from io import BytesIO

import pytest
from httpx import AsyncClient


class TestCreateEvent:
    async def test_create_event_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        response = await client.post(
            "/v1/events/",
            data=sample_event_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_event_data["title"]
        assert data["capacity"] == 100
        assert data["is_public"] is True
        assert "organizer_id" in data

    async def test_create_event_unauthorized(
        self,
        client: AsyncClient,
        sample_event_data: dict,
    ) -> None:
        response = await client.post(
            "/v1/events/",
            data=sample_event_data,
        )

        assert response.status_code == 401

    async def test_create_event_with_flyer(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
        sample_flyer: BytesIO,
    ) -> None:
        files = {"flyer": ("test_flyer.png", sample_flyer, "image/png")}

        response = await client.post(
            "/v1/events/",
            data=sample_event_data,
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["flyer_filename"] is not None
        assert data["flyer_url"] is not None

    async def test_create_private_event(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        sample_event_data["is_public"] = "false"

        response = await client.post(
            "/v1/events/",
            data=sample_event_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_public"] is False


class TestListEvents:
    async def test_list_events_empty(self, client: AsyncClient) -> None:
        response = await client.get("/v1/events/")

        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["total"] == 0

    async def test_list_events_with_search(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        await client.post("/v1/events/", data=sample_event_data, headers=auth_headers)

        response = await client.get("/v1/events/", params={"q": "Tech"})

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) > 0

    async def test_list_events_filter_public(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        await client.post("/v1/events/", data=sample_event_data, headers=auth_headers)

        response = await client.get("/v1/events/", params={"is_public": "true"})

        assert response.status_code == 200
        data = response.json()
        for event in data["events"]:
            assert event["is_public"] is True

    async def test_list_events_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        for i in range(5):
            sample_event_data["title"] = f"Event {i}"
            await client.post("/v1/events/", data=sample_event_data, headers=auth_headers)

        response = await client.get("/v1/events/", params={"page": 1, "per_page": 2})

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 2
        assert data["total"] == 5


class TestUpdateEvent:
    async def test_update_event_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        create_response = await client.post(
            "/v1/events/",
            data=sample_event_data,
            headers=auth_headers,
        )
        event_id = create_response.json()["id"]

        response = await client.patch(
            f"/v1/events/{event_id}",
            data={"title": "Updated Title"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    async def test_update_event_not_organizer(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        create_response = await client.post(
            "/v1/events/",
            data=sample_event_data,
            headers=auth_headers,
        )
        event_id = create_response.json()["id"]

        await client.post(
            "/v1/auth/register",
            json={
                "email": "other@example.com",
                "password": "otherpassword123",
                "full_name": "Other User",
            },
        )
        login_response = await client.post(
            "/v1/auth/login",
            data={"username": "other@example.com", "password": "otherpassword123"},
        )
        other_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        response = await client.patch(
            f"/v1/events/{event_id}",
            data={"title": "Hacked Title"},
            headers=other_headers,
        )

        assert response.status_code == 403


class TestDeleteEvent:
    async def test_delete_event_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        create_response = await client.post(
            "/v1/events/",
            data=sample_event_data,
            headers=auth_headers,
        )
        event_id = create_response.json()["id"]

        response = await client.delete(
            f"/v1/events/{event_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        get_response = await client.get(f"/v1/events/{event_id}")
        assert get_response.status_code == 404
