"""
Тесты для аутентификации
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from database import get_session
import models


# Тестовая БД
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_register_user(client: TestClient):
    """Тест регистрации пользователя"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPass123",
            "confirm_password": "TestPass123",
            "full_name": "Test User"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "password" not in data


def test_login_user(client: TestClient):
    """Тест входа пользователя"""
    # Сначала регистрируем
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "TestPass123",
            "confirm_password": "TestPass123"
        }
    )

    # Потом входим
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "login@example.com",
            "password": "TestPass123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_protected_endpoint(client: TestClient):
    """Тест защищенного эндпоинта"""
    # Регистрируем и входим
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "protected@example.com",
            "username": "protected",
            "password": "TestPass123",
            "confirm_password": "TestPass123"
        }
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "protected@example.com",
            "password": "TestPass123"
        }
    )

    token = login_response.json()["access_token"]

    # Пробуем получить профиль
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "protected@example.com"