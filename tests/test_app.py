import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities():
    # Make a deep copy of the in-memory activities and restore after each test
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities = original


def test_get_activities(client):
    r = client.get("/activities")
    assert r.status_code == 200
    data = r.json()
    assert "Chess Club" in data


def test_signup_and_remove_participant(client):
    activity = "Chess Club"
    email = "pytest-student@example.com"

    # Signup
    r = client.post(f"/activities/{urllib.parse.quote(activity)}/signup", params={"email": email})
    assert r.status_code == 200
    assert "Signed up" in r.json().get("message", "")

    # Ensure participant appears in activity
    r2 = client.get("/activities")
    participants = r2.json()[activity]["participants"]
    assert email in participants

    # Remove participant
    r3 = client.delete(f"/activities/{urllib.parse.quote(activity)}/participants", params={"email": email})
    assert r3.status_code == 200
    assert "Removed" in r3.json().get("message", "")

    # Ensure participant removed
    r4 = client.get("/activities")
    participants2 = r4.json()[activity]["participants"]
    assert email not in participants2


def test_cannot_signup_if_already_signed_in_other_activity(client):
    # Pick an existing participant from Chess Club
    existing = app_module.activities["Chess Club"]["participants"][0]
    # Try to signup the same email to Programming Class
    r = client.post("/activities/Programming%20Class/signup", params={"email": existing})
    assert r.status_code == 400
    assert "already signed up" in r.json().get("detail", "").lower()
