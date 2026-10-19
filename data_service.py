import requests
import pandas as pd

BASE_URL = "https://jsonplaceholder.typicode.com"

cache = {"users": None, "tasks": None}


def fetch_json(path: str):
    try:
        response = requests.get(path, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def load_data():
    if cache["users"] is not None and cache["tasks"] is not None:
        return True

    users_data = fetch_json(f"{BASE_URL}/users")
    tasks_data = fetch_json(f"{BASE_URL}/todos")

    if users_data is None or tasks_data is None:
        return False

    users = pd.DataFrame(
        [
            {
                "user_id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "city": user["address"]["city"],
            }
            for user in users_data
        ]
    )

    tasks = pd.DataFrame(
        [
            {
                "id": task["id"],
                "user_id": task["userId"],
                "title": task["title"],
                "completed": task["completed"],
            }
            for task in tasks_data
        ]
    )

    tasks["completed"] = tasks["completed"].astype(bool)

    cache["users"] = users
    cache["tasks"] = tasks

    return True
