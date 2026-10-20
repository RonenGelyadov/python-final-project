import requests
import json
import pandas as pd
import numpy as np

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
                "userId": task["userId"],
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


def analyze():
    if not load_data():
        return None

    users = cache["users"]
    tasks = cache["tasks"].rename(columns={"userId": "user_id"})

    merged = pd.merge(tasks, users, on="user_id")

    stats = merged.groupby(["user_id", "name"]).agg(
        total_tasks=("id", "count"),
        completed_tasks=("completed", "sum"),
    ).reset_index()

    stats["completion_precent"] = (
        stats["completed_tasks"] / stats["total_tasks"] * 100
    ).round(2)

    stats = stats.sort_values("completion_precent", ascending=False)

    completion_avg = np.mean(stats["completion_precent"]).round(2)
    completion_std = np.std(stats["completion_precent"])
    below_avg = stats[stats["completion_precent"] < completion_avg]

    pivot = pd.pivot_table(
        merged,
        values="id",
        index="city",
        columns="completed",
        aggfunc="count",
        fill_value=0,
    ).reset_index()

    # print(stats)

    return {
        "merged": merged.to_dict(orient="records"),
        "stats": stats.to_dict(orient="records"),
        "completion_avg": float(completion_avg),
        "completion_std": float(completion_std),
        "below_avg": below_avg.to_dict(orient="records"),
        "pivot": pivot.to_dict(orient="records"),
    }


def get_tasks_from_file():
    try:
        with open("tasks.json", "r") as f:
            tasks = json.load(f)
            print(tasks)
            return tasks

    except FileNotFoundError:
        print("tasks.json was not found")
        return None

    except json.JSONDecodeError:
        print("tasks.json contains invalid JSON")
        return None


def save_tasks_to_file():
    pass
