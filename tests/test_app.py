from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(deepcopy(original_activities))


def test_root_redirects_to_static_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_details():
    # Arrange
    expected_activity = "Chess Club"
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")
    response_body = response.json()

    # Assert
    assert response.status_code == 200
    assert expected_activity in response_body
    assert expected_fields.issubset(response_body[expected_activity])
    assert "michael@mergington.edu" in response_body[expected_activity]["participants"]


def test_signup_adds_participant_to_activity():
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    activity_path = quote(activity_name)

    # Act
    response = client.post(f"/activities/{activity_path}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    activity_path = quote(activity_name)

    # Act
    response = client.post(f"/activities/{activity_path}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up for this activity"}


def test_signup_rejects_unknown_activity():
    # Arrange
    activity_name = "Robotics Club"
    email = "new.student@mergington.edu"
    activity_path = quote(activity_name)

    # Act
    response = client.post(f"/activities/{activity_path}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant_from_activity():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    activity_path = quote(activity_name)

    # Act
    response = client.delete(f"/activities/{activity_path}/unregister", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity():
    # Arrange
    activity_name = "Robotics Club"
    email = "new.student@mergington.edu"
    activity_path = quote(activity_name)

    # Act
    response = client.delete(f"/activities/{activity_path}/unregister", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_missing_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "not.registered@mergington.edu"
    activity_path = quote(activity_name)

    # Act
    response = client.delete(f"/activities/{activity_path}/unregister", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}