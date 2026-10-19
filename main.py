from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def greet():
    return {"message": "Welcome to my python api service"}

