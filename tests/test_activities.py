import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


# Preserve original activities to reset between tests
_ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: reset the module-level activities before each test to isolate state."""
    app_module.activities = copy.deepcopy(_ORIGINAL_ACTIVITIES)
    yield
    app_module.activities = copy.deepcopy(_ORIGINAL_ACTIVITIES)


client = TestClient(app_module.app)


def test_get_activities_returns_expected_structure():
    # Arrange: fixture has reset state

    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expect at least one known activity
    assert "Chess Club" in data
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity and isinstance(activity["max_participants"], int)
        assert "participants" in activity and isinstance(activity["participants"], list)


def test_successful_signup_appends_participant_and_returns_message():
    # Arrange
    activity = "Chess Club"
    email = "teststudent@mergington.edu"
    assert email not in app_module.activities[activity]["participants"]

    # Act
    resp = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert resp.status_code == 200
    assert resp.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in app_module.activities[activity]["participants"]


def test_duplicate_signup_returns_400_with_detail():
    # Arrange: take an existing participant
    activity = "Chess Club"
    existing = app_module.activities[activity]["participants"][0]

    # Act
    resp = client.post(f"/activities/{activity}/signup?email={existing}")

    # Assert
    assert resp.status_code == 400
    assert resp.json().get("detail") == "Student already signed up for this activity"
    # participants list unchanged (no duplicate added)
    assert app_module.activities[activity]["participants"].count(existing) == 1


def test_signup_for_nonexistent_activity_returns_404_with_detail():
    # Arrange
    bad_activity = "Nonexistent Activity"

    # Act
    resp = client.post(f"/activities/{bad_activity}/signup?email=foo@bar.com")

    # Assert
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Activity not found"


def test_missing_email_returns_422_validation_error():
    # Arrange
    activity = "Chess Club"

    # Act
    resp = client.post(f"/activities/{activity}/signup")

    # Assert
    assert resp.status_code == 422
    # FastAPI returns a list of validation errors under 'detail'
    assert isinstance(resp.json().get("detail"), list)
