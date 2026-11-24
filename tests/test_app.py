import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", copy.deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_root_redirects_to_activity_page(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Basketball Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up student@mergington.edu for Basketball Club"
    }
    assert "student@mergington.edu" in client.get("/activities").json()[
        "Basketball Club"
    ]["participants"]


def test_signup_rejects_duplicate_participant(client):
    client.post(
        "/activities/Basketball Club/signup",
        params={"email": "student@mergington.edu"},
    )

    response = client.post(
        "/activities/Basketball Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_all_matching_participant_entries(client):
    email = "student@mergington.edu"
    app_module.activities["Basketball Club"]["participants"].extend([email, email])

    response = client.delete(
        "/activities/Basketball Club/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered student@mergington.edu from Basketball Club"
    }
    assert email not in client.get("/activities").json()["Basketball Club"]["participants"]


def test_unregister_rejects_unregistered_participant(client):
    response = client.delete(
        "/activities/Basketball Club/participants",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/participants",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
