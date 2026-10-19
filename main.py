from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from data_service import cache, load_data

load_dotenv()

app = FastAPI()


@app.get("/")
def greet():
    return {"message": "Welcome to my python api service"}


@app.get("/users")
def get_users():
    if not load_data():
        raise HTTPException(status_code=503, detail="Data source unavailable")
    return cache["users"].to_dict(orient="records")


@app.get("/tasks")
def get_tasks():
    if not load_data():
        raise HTTPException(status_code=503, detail="Data source unavailable")
    return cache["tasks"].to_dict(orient="records")
