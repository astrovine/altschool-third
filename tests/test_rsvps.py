import pytest
from httpx import AsyncClient


class TestCreateRSVP:
    async def test_create_rsvp_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        event_response = await client.post(
            "/v1/events/",
            data=sample_event_data,
            headers=auth_headers,
        )
        event_id = event_response.json()["id"]

        response = await client.post(
            f"/v1/events/{event_id}/rsvp",
            json={"status": "going"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "going"
        assert data["checked_in"] is False

    async def test_rsvp_capacity_limit(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        event_response = await client.post(
            "/v1/events/",
            data={
                "title": "Small Event",
                "description": "Limited capacity",
                "date": "2026-06-15T10:00:00Z",
                "location": "Small Room",
                "capacity": "1",
                "is_public": "true",
            },
            headers=auth_headers,
        )
        event_id = event_response.json()["id"]

        await client.post(
            f"/v1/events/{event_id}/rsvp",
            json={"status": "going"},
            headers=auth_headers,
        )

        await client.post(
            "/v1/auth/register",
            json={
                "email": "second@example.com",
                "password": "secondpassword123",
                "full_name": "Second User",
            },
        )
        login_response = await client.post(
            "/v1/auth/login",
            data={"username": "second@example.com", "password": "secondpassword123"},
        )
        second_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        response = await client.post(
            f"/v1/events/{event_id}/rsvp",
            json={"status": "going"},
            headers=second_headers,
        )

        assert response.status_code == 409
        assert "capacity" in response.json()["detail"].lower()

    async def test_rsvp_maybe_no_capacity_check(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        event_response = await client.post(
            "/v1/events/",
            data={
                "title": "Small Event",
                "description": "Limited capacity",
                "date": "2026-06-15T10:00:00Z",
                "location": "Small Room",
                "capacity": "1",
                "is_public": "true",
            },
            headers=auth_headers,
        )
        event_id = event_response.json()["id"]

        await client.post(
            f"/v1/events/{event_id}/rsvp",
            json={"status": "going"},
            headers=auth_headers,
        )

        await client.post(
            "/v1/auth/register",
            json={
                "email": "maybe@example.com",
                "password": "maybepassword123",
                "full_name": "Maybe User",
            },
        )
        login_response = await client.post(
            "/v1/auth/login",
            data={"username": "maybe@example.com", "password": "maybepassword123"},
        )
        maybe_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        response = await client.post(
            f"/v1/events/{event_id}/rsvp",
            json={"status": "maybe"},
            headers=maybe_headers,
        )

        assert response.status_code == 201


class TestMyRSVP:
    async def test_get_my_rsvp_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        event_response = await client.post(
            "/v1/events/",
            data=sample_event_data,
            headers=auth_headers,
        )
        event_id = event_response.json()["id"]

        await client.post(
            f"/v1/events/{event_id}/rsvp",
            json={"status": "going"},
            headers=auth_headers,
        )

        response = await client.get(
            f"/v1/events/{event_id}/rsvps/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "going"

    async def test_get_my_rsvp_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        event_response = await client.post(
            "/v1/events/",
            data=sample_event_data,
            headers=auth_headers,
        )
        event_id = event_response.json()["id"]

        await client.post(
            "/v1/auth/register",
            json={
                "email": "norsvp@example.com",
                "password": "norsvppassword123",
                "full_name": "No RSVP User",
            },
        )
        login_response = await client.post(
            "/v1/auth/login",
            data={"username": "norsvp@example.com", "password": "norsvppassword123"},
        )
        no_rsvp_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        response = await client.get(
            f"/v1/events/{event_id}/rsvps/me",
            headers=no_rsvp_headers,
        )

        assert response.status_code == 404


class TestDeleteRSVP:
    async def test_delete_rsvp_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        event_response = await client.post(
            "/v1/events/",
            data=sample_event_data,
            headers=auth_headers,
        )
        event_id = event_response.json()["id"]

        await client.post(
            f"/v1/events/{event_id}/rsvp",
            json={"status": "going"},
            headers=auth_headers,
        )

        response = await client.delete(
            f"/v1/events/{event_id}/rsvp",
            headers=auth_headers,
        )

        assert response.status_code == 204


class TestCheckIn:
    async def test_checkin_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ) -> None:
        event_response = await client.post(
            "/v1/events/",
            data=sample_event_data,
            headers=auth_headers,
        )
        event_id = event_response.json()["id"]

        await client.post(
            "/v1/auth/register",
            json={
                "email": "attendee@example.com",
                "password": "attendeepassword123",
                "full_name": "Attendee User",
            },
        )
        login_response = await client.post(
            "/v1/auth/login",
            data={"username": "attendee@example.com", "password": "attendeepassword123"},
        )
        attendee_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        rsvp_response = await client.post(
            f"/v1/events/{event_id}/rsvp",
            json={"status": "going"},
            headers=attendee_headers,
        )
        user_id = rsvp_response.json()["user_id"]

        response = await client.post(
            f"/v1/events/{event_id}/checkin",
            json={"user_id": user_id},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["checked_in"] is True
        assert data["checked_in_at"] is not None
