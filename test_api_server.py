import pytest
from fastapi.testclient import TestClient
from api_server import TASK_FILE
import os
import importlib
import api_server

@pytest.fixture
def client():
    # Đảm bảo reset hoàn toàn trạng thái
    if os.path.exists(TASK_FILE):
        os.remove(TASK_FILE)
    
    # Reload module để tạo mới FastAPI app và TaskManager
    importlib.reload(api_server)
    from api_server import app
    yield TestClient(app)

def test_create_task(client):
    response = client.post(
        "/tasks",
        json={"title": "Test Task", "description": "Test Description"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"
    assert data["completed"] is False
    assert "id" in data
    assert "created_at" in data

def test_create_task_invalid_title(client):
    # Test empty title
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 400
    assert "title must not be empty" in response.text  # Đã sửa từ response.text()

    # Test missing title
    response = client.post("/tasks", json={})
    assert response.status_code == 422

def test_list_tasks(client):
    # Tạo tasks mới (chỉ 2 tasks)
    client.post("/tasks", json={"title": "Task A"})
    client.post("/tasks", json={"title": "Task B"})
    
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 2  # Chỉ kiểm tra 2 tasks vừa tạo
    assert {t["title"] for t in tasks} == {"Task A", "Task B"}

def test_update_task(client):
    task = client.post("/tasks", json={"title": "Old Title"}).json()
    response = client.patch(
        f"/tasks/{task['id']}",
        json={"title": "New Title", "completed": True},
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "New Title"
    assert updated["completed"] is True

def test_update_task_not_found(client):
    response = client.patch("/tasks/invalid-id", json={"title": "X"})
    assert response.status_code == 404

def test_delete_task(client):
    task = client.post("/tasks", json={"title": "To Delete"}).json()
    response = client.delete(f"/tasks/{task['id']}")
    assert response.status_code == 204
    assert len(client.get("/tasks")
               .json()) == 0  # Đảm bảo đã xóa

def test_delete_task_not_found(client):
    response = client.delete("/tasks/invalid-id")
    assert response.status_code == 404