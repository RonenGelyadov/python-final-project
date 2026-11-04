import os
import json
import time

from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
import anthropic

from data_service import cache, load_data, analyze, get_tasks_from_file, save_tasks_to_file
from ai_service import ask, write_log

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


class AskIn(BaseModel):
    conversation_id: str
    prompt: str


class AskOut(BaseModel):
    conversation_id: str
    answer: str


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
async def json_decode_error_handler(req: Request, exc: json.JSONDecodeError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Data source is not valid JSON"},
    )


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(req: Request, exc: TaskNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Task with id {exc.task_id} was not found"},
    )


def pagination_params(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": limit}


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.environ.get("APP_API_KEY"):
        raise HTTPException(status_code=401, detail="Invaild API key")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    response.headers["X-process-Time"] = str(duration)

    print(
        f"Personal Log: {request.method} - {request.url} - {response.status_code}")

    return response


@app.get("/")
def greet():
    return {"message": "Welcome to my Python api service"}


@app.get("/stats/users")
def get_users(pagination: dict = Depends(pagination_params)):
    if not load_data():
        raise HTTPException(status_code=503, detail="Data source unavailable")

    users = cache["users"].to_dict(orient="records")

    skip = pagination["skip"]
    limit = pagination["limit"]

    return {
        "total": len(users),
        "skip": skip,
        "limit": limit,
        "users": users[skip: skip + limit],
    }


@app.get("/stats/summary")
def get_summary(pagination: dict = Depends(pagination_params)):
    result = analyze()

    if not result:
        raise HTTPException(status_code=503, detail="Data source unavailable")

    stats = result["stats"]

    skip = pagination["skip"]
    limit = pagination["limit"]

    return {
        "total": len(stats),
        "skip": skip,
        "limit": limit,
        "stats": stats[skip: skip + limit],
    }


@app.get("/stats/low-performers")
def get_low_performers(pagination: dict = Depends(pagination_params)):
    result = analyze()

    if not result:
        raise HTTPException(status_code=503, detail="Data source unavailable")

    stats = result["below_avg"]

    skip = pagination["skip"]
    limit = pagination["limit"]

    return {
        "total": len(stats),
        "skip": skip,
        "limit": limit,
        "stats": stats[skip: skip + limit],
    }


@app.get("/stats/cities")
def get_cities(pagination: dict = Depends(pagination_params)):
    result = analyze()

    if not result:
        raise HTTPException(status_code=503, detail="Data source unavailable")

    cities = result["pivot"]

    skip = pagination["skip"]
    limit = pagination["limit"]

    return {
        "total": len(cities),
        "skip": skip,
        "limit": limit,
        "cities": cities[skip: skip + limit],
    }


@app.get("/tasks")
def get_tasks(pagination: dict = Depends(pagination_params)):
    tasks = get_tasks_from_file()

    skip = pagination["skip"]
    limit = pagination["limit"]

    return {
        "total": len(tasks),
        "skip": skip,
        "limit": limit,
        "tasks": tasks[skip: skip + limit],
    }


@app.post("/tasks", response_model=TaskOut, status_code=201)
def add_task(task: TaskIn, api_key: str = Depends(verify_api_key)):
    verified_title = task.title.strip()
    if not verified_title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    if not 1 <= task.priority <= 3:
        raise HTTPException(
            status_code=400, detail="Priority must be between 1 and 3")

    tasks = get_tasks_from_file()
    new_id = max((t["id"] for t in tasks), default=0) + 1

    new_task = {
        "id": new_id,
        "title": verified_title,
        "user_id": task.user_id,
        "due_date": task.due_date,
        "priority": task.priority,
        "done": task.done,
        "notes": task.notes if task.notes is not None else ""
    }

    tasks.append(new_task)
    save_tasks_to_file(tasks)
    return new_task


@app.get("/tasks/overdue")
def get_tasks_overdue(pagination: dict = Depends(pagination_params)):
    tasks = get_tasks_from_file()


@app.get("/tasks/{task_id}")
def get_task_by_id(task_id: int):
    tasks = get_tasks_from_file()

    for task in tasks:
        if task["id"] == task_id:
            return task

    raise TaskNotFoundError(task_id)


@app.put("/tasks/{task_id}", response_model=TaskOut)
def edit_task(task_id: int, task: TaskIn, api_key: str = Depends(verify_api_key)):
    verified_title = task.title.strip()
    if not verified_title:
        raise HTTPException(
            status_code=400, detail="Title cannot be empty")

    if not 1 <= task.priority <= 3:
        raise HTTPException(
            status_code=400, detail="Priority must be between 1 and 3")

    tasks = get_tasks_from_file()

    edited_task = next((t for t in tasks if t["id"] == task_id), None)

    if edited_task is None:
        raise TaskNotFoundError(task_id)

    edited_task["title"] = verified_title
    edited_task["due_date"] = task.due_date
    edited_task["priority"] = task.priority
    edited_task["done"] = task.done
    edited_task["notes"] = task.notes if task.notes is not None else ""

    save_tasks_to_file(tasks)

    return edited_task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, api_key: str = Depends(verify_api_key)):
    tasks = get_tasks_from_file()

    deleted_task = next((t for t in tasks if t["id"] == task_id), None)

    if deleted_task is None:
        raise TaskNotFoundError(task_id)

    tasks.remove(deleted_task)

    save_tasks_to_file(tasks)

    return deleted_task


@app.post("/ai/ask", response_model=AskOut)
def ask_ai(body: AskIn):
    status = "success"

    prompt = body.prompt.strip()
    prompt_length = len(prompt)

    try:
        if not prompt or prompt_length > 500:
            raise HTTPException(
                status_code=400, detail="Prompt must be 1-500 characters")

        answer = ask(prompt, body.conversation_id)
        return {"conversation_id": body.conversation_id, "answer": answer}

    except HTTPException:
        status = "bad_request"
        raise

    except anthropic.AuthenticationError:
        status = "auth_error"
        raise HTTPException(status_code=502, detail="Invalid API key")

    except anthropic.APIError:
        status = "service_error"
        raise HTTPException(status_code=502, detail="AI service error")

    except Exception:
        status = "error"
        raise HTTPException(
            status_code=500, detail="AI model error or API key not valid")

    finally:
        write_log(prompt_length, status)
