import pytest


@pytest.mark.asyncio
async def test_get_me(test_client):
    response = await test_client.get("/api/users/me")
    print("RESPONSE:", response.status_code, response.text)
    assert response.status_code == 200, response.text
