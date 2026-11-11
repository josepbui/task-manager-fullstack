from fastapi import FastAPI, HTTPException, status
from task_manager import TaskManager, TaskNotFoundError, InvalidTaskError
from typing import Optional
from pydantic import BaseModel
import os
import tempfile

app = FastAPI(title="Task Manager API")

# Pydantic Models
class TaskCreate(BaseModel):
    title: str
    description: str = ""

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    completed: bool
    created_at: str

# Initialize TaskManager
TASK_FILE = os.getenv("TASK_FILE", os.path.join(tempfile.gettempdir(), "task_manager.json"))
manager = TaskManager(TASK_FILE)

@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate):
    try:
        task = manager.add_task(task_data.title, task_data.description)
        return task.to_dict()
    except InvalidTaskError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(include_completed: bool = True):
    tasks = manager.list_tasks(include_completed)
    return [task.to_dict() for task in tasks]

@app.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate
):
    try:
        task = manager.update_task(
            task_id,
            title=task_data.title,
            description=task_data.description,
            completed=task_data.completed,
        )
        return task.to_dict()
    except TaskNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidTaskError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str):
    try:
        manager.delete_task(task_id)
    except TaskNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )