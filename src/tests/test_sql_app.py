from fastapi.testclient import TestClient

from sqlmodel import SQLModel, Session, create_engine

from src.tests.initialize_data import init_status_code

from ..main import app
from ..util import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

def init_db():
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = Session(engine)
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

TEST_USER = {"email": "deadpool@example.com",
             "password": "chimichangas4life",
             "username": "testerjordan", "id": 1}

TEST_PROJECT = { "name": "Test Project", "description": "This is a test project", "status_code": 1}

TEST_ORGANIZATION = {"name": "Test Organization", "description": "This is a test organization", "owner_id": 1}


TEST_DIAGRAM = {"title": "Test Diagram", "description": "This is a test diagram", "config": "asdasdqaw3f2r21q125", "project_id": 1}

def create_user():
    response = client.post(
        "/users/",
        json=TEST_USER,
    )
    assert response.status_code == 200, response.text

    return response.json()

def get_token():
    response = client.post(
        "/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]},
    )
    assert response.status_code == 200, response.text

    return response.json()["access_token"]

def auth_header():
    return {"Authorization": f"Bearer {get_token()}"}

def test_create_user():
    init_db()

    data = create_user()

    assert "id" in data
    assert data["email"] == TEST_USER["email"]
    assert data["username"] == TEST_USER["username"]
    assert data["password"] is None


def test_get_user_by_id():
    response = client.get(f"/users/{TEST_USER['id']}")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["username"] == TEST_USER["username"]

    
def test_create_user_project():
    init_status_code(Session(engine))

    response = client.post(
        "/project",
        json=TEST_PROJECT,
        headers=auth_header()
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["name"] == TEST_PROJECT["name"]
    assert data["description"] == TEST_PROJECT["description"]
    assert data["status_code"] == 1


def test_get_user_projects():
    response = client.get(f"/project", headers=auth_header())
   
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == TEST_PROJECT["name"]
    assert data[0]["description"] == TEST_PROJECT["description"]
    assert data[0]["status_code"] == 1

def test_create_diagram_in_project():
    response = client.post(f"/project/{1}/diagram", json=TEST_DIAGRAM, headers=auth_header())

    data = response.json()
    assert data["title"] == TEST_DIAGRAM["title"]
    assert data["description"] == TEST_DIAGRAM["description"]
    assert data["config"] == TEST_DIAGRAM["config"]
    assert data["project_id"] == 1

def test_get_diagrams_by_project():
    response = client.get(f"/project/{1}/diagram", headers=auth_header())

    data = response.json()
    print(data)
    assert len(data) == 1
    assert data[0]["title"] == TEST_DIAGRAM["title"]
    assert data[0]["description"] == TEST_DIAGRAM["description"]
    assert data[0]["config"] == TEST_DIAGRAM["config"]
    assert data[0]["project_id"] == 1

def test_get_diagram_by_id():
    response = client.get(f"/diagram/{1}", headers=auth_header())

    data = response.json()

    print(data)
    assert data["title"] == TEST_DIAGRAM["title"]
    assert data["description"] == TEST_DIAGRAM["description"]
    assert data["config"] == TEST_DIAGRAM["config"]
    assert data["project_id"] == 1

def test_get_project_by_id():
    response = client.get(f"/project/{1}", headers=auth_header())

    data = response.json()
    assert data["name"] == TEST_PROJECT["name"]
    assert data["description"] == TEST_PROJECT["description"]
    assert data["status_code"] == 1


def test_create_org():
    response = client.post(f"/organization", json=TEST_ORGANIZATION, headers=auth_header())
   
    data = response.json()
    assert data["name"] == TEST_ORGANIZATION["name"]
    assert data["description"] == TEST_ORGANIZATION["description"]
    assert data["owner_id"] == TEST_USER["id"]

def test_get_org_by_id():
    response = client.get(f"/organization/1",headers=auth_header())

    data = response.json()
    print(data)
    assert data["name"] == TEST_ORGANIZATION["name"]
    assert data["description"] == TEST_ORGANIZATION["description"]
    assert data["owner_id"] == TEST_USER["id"]



def test_create_org_project():
    for x in range(2):
        post_data = {
        "org_id": 1,
        "project": TEST_PROJECT
        }

        response = client.post(f"/organization/project", json=post_data, headers=auth_header())
    
        data = response.json()
        print(data)
        assert data["name"] == TEST_PROJECT["name"]
        assert data["description"] == TEST_PROJECT["description"]
        assert data["status_code"] == 1

def test_get_org_projects():
    response = client.get(f"/organization/{1}/project",headers=auth_header())

    data = response.json()
    print(data)
    assert len(data) == 2
    assert data[0]["name"] == TEST_PROJECT["name"]
    assert data[0]["description"] == TEST_PROJECT["description"]
    assert data[0]["status_code"] == 1
    assert data[1]["name"] == TEST_PROJECT["name"]
    assert data[1]["description"] == TEST_PROJECT["description"]
    assert data[1]["status_code"] == 1
