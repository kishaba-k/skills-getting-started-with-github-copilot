import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    # Arrange: Create test client
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: Snapshot original activities state before each test
    original_state = copy.deepcopy(activities)
    yield
    # Cleanup: Restore activities back to initial state
    activities.clear()
    activities.update(original_state)


def test_root_redirects_to_static_index(client):
    # Arrange
    target_url = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == target_url


def test_get_activities_returns_all_activities(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert expected_activity in data
    assert "description" in data[expected_activity]
    assert "schedule" in data[expected_activity]
    assert "max_participants" in data[expected_activity]
    assert "participants" in data[expected_activity]


def test_signup_for_activity_success(client):
    # Arrange
    activity_name = "Basketball Club"
    new_email = "alice@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={new_email}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
    assert new_email in activities[activity_name]["participants"]


def test_signup_for_nonexistent_activity_returns_404(client):
    # Arrange
    nonexistent_activity = "Underwater Basket Weaving"
    email = "someone@mergington.edu"

    # Act
    response = client.post(f"/activities/{nonexistent_activity}/signup?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_student_returns_400(client):
    # Arrange
    activity_name = "Chess Club"
    already_signed_up_email = "michael@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={already_signed_up_email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_unregister_participant_success(client):
    # Arrange
    activity_name = "Chess Club"
    existing_participant = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants?email={existing_participant}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {existing_participant} from {activity_name}"
    assert existing_participant not in activities[activity_name]["participants"]


def test_unregister_participant_from_nonexistent_activity_returns_404(client):
    # Arrange
    nonexistent_activity = "Nonexistent Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{nonexistent_activity}/participants?email={email}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_non_participant_returns_404(client):
    # Arrange
    activity_name = "Chess Club"
    not_registered_email = "stranger@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants?email={not_registered_email}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in activity"
