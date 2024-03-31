import pytest
from fastapi.testclient import TestClient
from sqlmodel import Field, Session, SQLModel, create_engine, select
from simple_hero_api.main import app, get_session
from simple_hero_api.model import Hero
from simple_hero_api import settings


@pytest.fixture(name="session")  
def session_fixture():  
    connection_string = str(settings.TEST_DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg")

    engine = create_engine(
        connection_string, connect_args={"sslmode": "require"}, pool_recycle=300)

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

def test_read_main():
    client = TestClient(app=app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

def test_write_main(client:TestClient):
        
        response = client.post(
            "/heroes/", json={"name": "Ameen Alam", "secret_name": "AM"}
        )
        data = response.json()
        assert response.status_code == 200
        assert data["name"] == "Ameen Alam"
        assert data["secret_name"] == "AM"
        assert data["age"] is None
        assert data["id"] is not None

def test_create_hero_incomplete(client: TestClient):
    # No secret_name
    response = client.post("/heroes/", json={"name": "Ameen Aalam"})
    assert response.status_code == 422


def test_create_hero_invalid(client: TestClient):
    # secret_name has an invalid type
    response = client.post(
        "/heroes/",
        json={
            "name": "Ameen Aalam",
            "secret_name": {"message": "Do you wanna know my secret identity?"},
        },
    )
    assert response.status_code == 422



def test_update_hero(session: Session, client: TestClient):
    hero_1 = Hero(name="Ajmal Khan", secret_name="AK")
    session.add(hero_1)
    session.commit()

    response = client.patch(f"/heroes/{hero_1.id}", json={"name": "Nizamani"})
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == "Nizamani"
    assert data["secret_name"] == "AK"
    assert data["age"] is None
    assert data["id"] == hero_1.id


def test_delete_hero(session: Session, client: TestClient):
    hero_1 = Hero(name="Ajmal Khan", secret_name="AK")
    session.add(hero_1)
    session.commit()

    response = client.delete(f"/heroes/{hero_1.id}")

    hero_in_db = session.get(Hero, hero_1.id)

    assert response.status_code == 200

    assert hero_in_db is None