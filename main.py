import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
from data_service import cache, load_data, analyze, get_tasks_from_file, save_tasks_to_file

load_dotenv()

app = FastAPI()


class TaskIn(BaseModel):
    title: str
    user_id: int
    due_date: str
    priority: int
    done: bool
    notes: Optional[str] = None


class TaskOut(BaseModel):
    id: int
    title: str
    user_id: int
    due_date: str
    priority: int
    done: bool


class TaskNotFoundError(Exception):
    def __init__(self, task_id: int):
        self.task_id = task_id


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(req: Request, exc: FileNotFoundError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Data source unavailable"},
    )


@app.exception_handler(json.JSONDecodeError)
async def file_not_found_handler(req: Request, exc: json.JSONDecodeError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Data source is not valid JSON"},
    )


@app.exception_handler(TaskNotFoundError)
async def file_not_found_handler(req: Request, exc: TaskNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Task with id {exc.task_id} was not found"},
    )


@app.get("/")
def greet():
    return {"message": "Welcome to my Python api service"}


@app.get("/stats/users")
def get_users():
    if not load_data():
        raise HTTPException(status_code=503, detail="Data source unavailable")
    return cache["users"].to_dict(orient="records")


@app.get("/stats/summary")
def get_summary():
    result = analyze()

    if not result:
        raise HTTPException(status_code=503, detail="Data source unavailable")

    return result


@app.get("/stats/low-performers")
def get_low_performers():
    result = analyze()

    if not result:
        raise HTTPException(status_code=503, detail="Data source unavailable")

    return result["below_avg"]


@app.get("/stats/cities")
def get_cities():
    result = analyze()

    if not result:
        raise HTTPException(status_code=503, detail="Data source unavailable")

    return result["pivot"]


# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------


@app.get("/tasks")
def get_tasks():
    return get_tasks_from_file()


@app.post("/tasks", response_model=TaskOut, status_code=201)
def add_task(task: TaskIn):
    return task


@app.get("/tasks/overdue")
def get_tasks():
    pass


@app.get("/tasks/{task_id}")
def get_task_by_id(task_id: int):
    tasks = get_tasks_from_file()

    for task in tasks:
        if task["id"] == task_id:
            return task

    raise TaskNotFoundError(task_id)


@app.put("/tasks/{task_id}")
def get_task_by_id(task_id: int):
    pass


@app.delete("/tasks/{task_id}")
def get_task_by_id(task_id: int):
    pass
