from unittest.mock import Mock
from sqlalchemy.ext.asyncio import AsyncSession
import pytest
from sqlalchemy import select

from src.database.models import User
from src.services.auth import auth_service

from src.services.auth import auth_service
from src.services.users import UserService

user_data = {
    "username": "testuser1",
    "email": "test1@test.com",
    "password": "testpassword1",
    "role": "user",
}


# -------------------------- Helpers --------------------------
async def confirm_user(session: AsyncSession, email: str):
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.confirmed = True
        session.add(user)
        await session.commit()
        await session.refresh(user)


async def unconfirm_user(session: AsyncSession, email: str):
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.confirmed = False
        session.add(user)
        await session.commit()
        await session.refresh(user)


# -------------------------- Tests --------------------------


# Signup tests: use user_data for new user creation
@pytest.mark.asyncio
async def test_signup(unauthenticated_client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    response = await unauthenticated_client.post("/api/auth/signup", json=user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert mock_send_email.call_count == 1


@pytest.mark.asyncio
async def test_signup_repeat(unauthenticated_client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    # Register first time
    await unauthenticated_client.post("/api/auth/signup", json=user_data)

    # Register again
    response = await unauthenticated_client.post("/api/auth/signup", json=user_data)

    assert response.status_code == 409
    assert response.json() == {"detail": "User with this email already exist"}


@pytest.mark.asyncio
async def test_signup_repeat_username(unauthenticated_client, monkeypatch, test_user):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    new_user = test_user.copy()
    new_user["email"] = (
        "unique_email@test.com"  # Change email to test username conflict
    )
    response = await unauthenticated_client.post("/api/auth/signup", json=new_user)

    assert response.status_code == 409
    assert response.json() == {"detail": "User with this name already exist"}


# Login and related tests: use test_user because it's fixture user in DB
@pytest.mark.asyncio
async def test_not_confirmed_login(unauthenticated_client, test_user, test_db):
    new_user = {
        "username": "unconfirmed_user",
        "email": "unconfirmed@example.com",
        "password": "test123456",
        "avatar": "https://example.com/avatar.jpg",
    }

    # create user manually
    user = User(
        username=new_user["username"],
        email=new_user["email"],
        password=auth_service.get_password_hash(new_user["password"]),
        confirmed_email=False,
    )
    test_db.add(user)
    await test_db.commit()

    response = await unauthenticated_client.post(
        "/api/auth/login",
        data={"username": new_user["username"], "password": new_user["password"]},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email not confirmed"


@pytest.mark.asyncio
async def test_login(unauthenticated_client, test_db, test_user):
    await confirm_user(test_db, test_user["email"])

    user_service = UserService(test_db)
    user = await user_service.get_user_by_email(test_user["email"])

    assert user is not None, "❌ User not found"
    assert user.confirmed_email is True, "❌ User is not confirmed"
    assert auth_service.verify_password(
        test_user["password"], user.password
    ), "❌ Wrong password"

    response = await unauthenticated_client.post(
        "/api/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data


@pytest.mark.asyncio
async def test_login_wrong_password(unauthenticated_client, test_user):
    response = await unauthenticated_client.post(
        "/api/auth/login",
        data={"username": test_user["username"], "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid login or password"


@pytest.mark.asyncio
async def test_login_wrong_username(unauthenticated_client, test_user):
    response = await unauthenticated_client.post(
        "/api/auth/login",
        data={"username": "wrong", "password": test_user["password"]},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid login or password"


@pytest.mark.asyncio
async def test_validation_error_login(unauthenticated_client, test_user):
    response = await unauthenticated_client.post(
        "/api/auth/login", data={"password": test_user["password"]}
    )
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_refresh_token(test_client, test_db, test_user):
    await confirm_user(test_db, test_user["email"])

    user_result = await test_db.execute(
        select(User).where(User.email == test_user["email"])
    )
    user = user_result.scalar_one()

    # Ensure the user has a refresh token (if not saved before)
    if not user.refresh_token:
        token = auth_service.create_refresh_token(data={"sub": user.email})
        user.refresh_token = token
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

    response = await test_client.post(
        "/api/auth/refresh_token",
        json={"refresh_token": user.refresh_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_confirmed_email(unauthenticated_client, test_user):
    token = auth_service.create_email_token(data={"sub": test_user["email"]})
    response = await unauthenticated_client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 200
    assert response.json() == {"message": "Your email is already confirmed"}


@pytest.mark.asyncio
async def test_confirmed_email_already_confirmed(test_client, test_user):
    token = auth_service.create_email_token(data={"sub": test_user["email"]})
    response = await test_client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 200
    assert response.json() == {"message": "Your email is already confirmed"}


@pytest.mark.asyncio
async def test_confirmed_email_invalid_token(unauthenticated_client):
    response = await unauthenticated_client.get(
        "/api/auth/confirmed_email/invalid_token"
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid token for email verification"}


@pytest.mark.asyncio
async def test_request_email_already_confirmed(test_client, test_user):
    response = await test_client.post(
        "/api/auth/request_email", json={"email": test_user["email"]}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Your email is already confirmed"}


@pytest.mark.asyncio
async def test_request_email(unauthenticated_client, test_db, test_user):
    await unconfirm_user(test_db, test_user["email"])

    response = await unauthenticated_client.post(
        "/api/auth/request_email", json={"email": test_user["email"]}
    )
    assert response.status_code == 200
    assert response.json()["message"] in [
        "Check your email for confirmation",
        "Your email is already confirmed",
    ]


@pytest.mark.asyncio
async def test_request_email_invalid_email(unauthenticated_client):
    response = await unauthenticated_client.post(
        "/api/auth/request_email", json={"email": "bad@notfound"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_forgot_password_email_not_confirmed(unauthenticated_client, test_user):
    response = await unauthenticated_client.post(
        "/api/auth/forgot_password", json={"email": test_user["email"]}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Check your email for confirmation"}


@pytest.mark.asyncio
async def test_forgot_password_wrong_email(unauthenticated_client):
    response = await unauthenticated_client.post(
        "/api/auth/forgot_password", json={"email": "not@found.com"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Verification error"}


@pytest.mark.asyncio
async def test_forgot_password(unauthenticated_client, test_db, test_user):
    await confirm_user(test_db, test_user["email"])

    response = await unauthenticated_client.post(
        "/api/auth/forgot_password", json={"email": test_user["email"]}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Check your email for confirmation"}


@pytest.mark.asyncio
async def test_post_reset_password(unauthenticated_client, test_db, test_user):
    await confirm_user(test_db, test_user["email"])

    token = auth_service.create_email_token(data={"sub": test_user["email"]})
    response = await unauthenticated_client.post(
        f"/api/auth/reset_password/{token}", data={"password": "newpassword123"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Password successfully changed"}

    # assert response.json() == {"message": "Password successfully changed"}


# from unittest.mock import Mock

# import pytest
# from sqlalchemy import select

# from src.database.models import User
# from src.services.auth import auth_service


# test_user = {
#     "username": "testuser",
#     "email": "test@test.com",
#     "password": "testpassword",
#     "role": "USER",
#     "avatar": "https://example.com/avatar.jpg",
# }


# @pytest.mark.asyncio
# async def test_signup(unauthenticated_client, monkeypatch):
#     mock_send_email = Mock()
#     monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
#     response = await unauthenticated_client.post("/api/auth/signup", json=test_user)

#     assert response.status_code == 201
#     data = response.json()
#     assert data["username"] == test_user["username"]
#     assert data["email"] == test_user["email"]
#     assert mock_send_email.call_count == 1


# def test_signup_repeat(unauthenticated_client, monkeypatch):
#     mock_send_email = Mock()
#     monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
#     response = unauthenticated_client.post("/api/auth/signup", json=test_user)

#     assert response.status_code == 409
#     assert response.json() == {"detail": "User with this email already exist"}


# def test_signup_repeat_username(unauthenticated_client, monkeypatch):
#     mock_send_email = Mock()
#     monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
#     new_user = test_user.copy()
#     new_user["email"] = "unique_email@test.com"
#     response = unauthenticated_client.post("/api/auth/signup", json=new_user)

#     assert response.status_code == 409
#     assert response.json() == {"detail": "User with this name already exist"}


# def test_not_confirmed_login(unauthenticated_client):
#     response = unauthenticated_client.post(
#         "/api/auth/login",
#         data={
#             "username": test_user["username"],
#             "password": test_user["password"],
#         },
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "Email not confirmed"


# @pytest.mark.asyncio
# async def test_login(unauthenticated_client, test_db):
#     user = await test_db.execute(select(User).where(User.email == test_user["email"]))
#     user = user.scalar_one_or_none()
#     if user:
#         user.is_confirmed = True
#         await test_db.commit()

#     response = unauthenticated_client.post(
#         "/api/auth/login",
#         data={
#             "username": test_user["username"],
#             "password": test_user["password"],
#         },
#     )
#     assert response.status_code == 200
#     data = response.json()
#     assert "access_token" in data
#     assert "refresh_token" in data
#     assert "token_type" in data


# def test_login_wrong_password(unauthenticated_client):
#     response = unauthenticated_client.post(
#         "/api/auth/login",
#         data={"username": test_user["username"], "password": "wrong"},
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "Invalid login or password"


# def test_login_wrong_username(unauthenticated_client):
#     response = unauthenticated_client.post(
#         "/api/auth/login",
#         data={"username": "wrong", "password": test_user["password"]},
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "Invalid login or password"


# def test_validation_error_login(unauthenticated_client):
#     response = unauthenticated_client.post(
#         "/api/auth/login", data={"password": test_user["password"]}
#     )
#     assert response.status_code == 422
#     assert "detail" in response.json()


# @pytest.mark.asyncio
# async def test_refresh_token(test_client, test_db):
#     user = await test_db.execute(select(User).where(User.email == test_user["email"]))
#     user = user.scalar_one_or_none()
#     if user:
#         user.is_confirmed = True
#         await test_db.commit()

#     response = test_client.post(
#         "/api/auth/refresh_token", json={"refresh_token": user.refresh_token}
#     )
#     assert response.status_code == 200
#     data = response.json()
#     assert "access_token" in data
#     assert "refresh_token" in data


# @pytest.mark.asyncio
# async def test_confirmed_email(unauthenticated_client):
#     token = auth_service.create_email_token(data={"sub": test_user["email"]})
#     response = unauthenticated_client.get(f"/api/auth/confirmed_email/{token}")
#     assert response.status_code == 200
#     assert response.json() == {"message": "Email confirmed"}


# def test_confirmed_email_already_confirmed(test_client):
#     token = auth_service.create_email_token(data={"sub": test_user["email"]})
#     response = test_client.get(f"/api/auth/confirmed_email/{token}")
#     assert response.status_code == 409
#     assert response.json() == {"detail": "Your email is already confirmed"}


# def test_confirmed_email_invalid_token(unauthenticated_client):
#     response = unauthenticated_client.get("/api/auth/confirmed_email/invalid_token")
#     assert response.status_code == 422
#     assert response.json() == {"detail": "Invalid token for email verification"}


# def test_request_email_already_confirmed(test_client):
#     response = test_client.post(
#         "/api/auth/request_email", json={"email": test_user["email"]}
#     )
#     assert response.status_code == 409
#     assert response.json() == {"detail": "Your email is already confirmed"}


# @pytest.mark.asyncio
# async def test_request_email(unauthenticated_client, test_db):
#     user = await test_db.execute(select(User).where(User.email == test_user["email"]))
#     user = user.scalar_one_or_none()
#     if user:
#         user.is_confirmed = False
#         await test_db.commit()

#     response = unauthenticated_client.post(
#         "/api/auth/request_email", json={"email": test_user["email"]}
#     )
#     assert response.status_code == 200
#     assert response.json() == {"message": "Check your email for confirmation"}


# def test_request_email_invalid_email(unauthenticated_client):
#     response = unauthenticated_client.post(
#         "/api/auth/request_email", json={"email": "bad@notfound"}
#     )
#     assert response.status_code == 422


# def test_forgot_password_email_not_confirmed(unauthenticated_client):
#     response = unauthenticated_client.post(
#         "/api/auth/forgot_password", json={"email": test_user["email"]}
#     )
#     assert response.status_code == 401
#     assert response.json() == {"detail": "Email not confirmed"}


# def test_forgot_password_wrong_email(unauthenticated_client):
#     response = unauthenticated_client.post(
#         "/api/auth/forgot_password", json={"email": "not@found.com"}
#     )
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Verification error"}


# @pytest.mark.asyncio
# async def test_forgot_password(unauthenticated_client, test_db):
#     user = await test_db.execute(select(User).where(User.email == test_user["email"]))
#     user = user.scalar_one_or_none()
#     if user:
#         user.is_confirmed = True
#         await test_db.commit()

#     response = unauthenticated_client.post(
#         "/api/auth/forgot_password", json={"email": test_user["email"]}
#     )
#     assert response.status_code == 200
#     assert response.json() == {"message": "Check your email for confirmation"}


# @pytest.mark.asyncio
# async def test_post_reset_password(unauthenticated_client):
#     token = auth_service.create_email_token(data={"sub": test_user["email"]})
#     response = unauthenticated_client.post(
#         f"/api/auth/reset_password/{token}", data={"password": "newpassword123"}
#     )
#     assert response.status_code == 200
#     assert response.json() == {"message": "Password successfully changed"}
