from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from data_service import cache, load_data, analyze, get_tasks_from_file, save_tasks_to_file

load_dotenv()

app = FastAPI()


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


@app.get("/tasks")
def get_tasks():
    result = get_tasks_from_file()

    if not result:
        raise HTTPException(status_code=503, detail="Data source unavailable")

    return result


@app.post("/tasks")
def get_tasks():
    pass


@app.get("/tasks/overdue")
def get_tasks():
    pass


@app.get("/tasks/{task_id}")
def get_task_by_id(task_id: int):
    pass

    # for task in tasks:
    #     if task["id"] == task_id:
    #         return task

    # raise HTTPException(
    #     status_code=404, detail=f"Task with id: {task_id} doesn't exist")


@app.get("/tasks/{task_id}")
def get_task_by_id(task_id: int):
    pass
