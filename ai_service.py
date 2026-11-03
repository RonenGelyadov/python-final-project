import csv
import os
from datetime import datetime

import anthropic
from dotenv import load_dotenv

from data_service import analyze

load_dotenv()

client = anthropic.Anthropic()

LOG_FILE = "ai_logs.csv"

UNAVAILABLE_NOTE = (
    "You are a data analysis assistant for a task management system. "
    "The analysis data (top users, completion averages, city statistics) "
    "is currently unavailable. If the user asks about specific numbers, "
    "users, or cities, tell them the data is temporarily unavailable. "
    "Do not guess or invent figures."
)

conversations: dict[str, list[dict]] = {}


def build_system_prompt():
    result = analyze()

    if result is None:
        return UNAVAILABLE_NOTE

    stats = result["stats"]

    top3 = ", ".join(
        f"{s['name']} ({s['completion_precent']}%)" for s in stats[:3]
    )

    pivot = result["pivot"]

    best_city = max(pivot, key=lambda city: city["True"])["city"]

    return (
        "You are a data analysis assistant for a task management system. "
        f"Top 3 users by completion rate: {top3}. "
        f"Average completion rate: {result['completion_avg']}%. "
        f"Strongest city (most completed tasks): {best_city}."
    )
