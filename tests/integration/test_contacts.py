import pytest
import pytest_asyncio
from src.services.auth import auth_service
from tests.factories import ContactsFactory


@pytest_asyncio.fixture
async def test_contact(test_db, test_user):
    contact = await ContactsFactory.create_(test_db, user_id=test_user.id)
    return contact


@pytest.mark.asyncio
async def test_create_contact(test_client):
    contact_data = ContactsFactory.build().__dict__
    contact_data.pop("_sa_instance_state", None)
    contact_data["birthday"] = str(contact_data["birthday"])
    response = await test_client.post("/api/contacts/", json=contact_data)
    assert response.status_code == 201
    assert response.json()["first_name"] == contact_data["first_name"]


@pytest.mark.asyncio
async def test_get_contacts(test_client, test_contact):  # <- use fixture here
    response = await test_client.get("/api/contacts/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["first_name"] == test_contact.first_name


@pytest.mark.asyncio
async def test_get_contact_by_id(test_client, test_contact):
    response = await test_client.get(f"/api/contacts/{test_contact.id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == test_contact.first_name


@pytest.mark.asyncio
async def test_get_contact_by_id_not_found(test_client):
    response = await test_client.get("/api/contacts/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_contact(test_client, test_contact):
    updated_data = {
        "first_name": "updated_contact",
        "last_name": test_contact.last_name,
        "email": test_contact.email,
        "phone": test_contact.phone,
        "birthday": str(test_contact.birthday),
        "info": test_contact.info,
    }
    response = await test_client.patch(
        f"/api/contacts/{test_contact.id}", json=updated_data
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "updated_contact"


@pytest.mark.asyncio
async def test_update_contact_not_found(test_client, test_contact):
    updated_data = {
        "first_name": "updated_contact",
        "last_name": test_contact.last_name,
        "email": test_contact.email,
        "phone": test_contact.phone,
        "birthday": str(test_contact.birthday),
        "info": test_contact.info,
    }
    response = await test_client.patch("/api/contacts/999", json=updated_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_contact(test_client, test_contact):
    response = await test_client.delete(f"/api/contacts/{test_contact.id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_contact_not_found(test_client):
    response = await test_client.delete("/api/contacts/999")
    assert response.status_code == 404
