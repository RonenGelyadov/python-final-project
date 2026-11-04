import csv
import os
from datetime import datetime

import anthropic
from dotenv import load_dotenv

from data_service import analyze


load_dotenv()

api_key = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key) if api_key else None

LOG_FILE = "ai_logs.csv"

MOCK_ANSWER = (
    "Mock mode: no API key is configured, so this is a fixed response. "
    "Add ANTHROPIC_API_KEY to your .env file to get real answers."
)

UNAVAILABLE_SYSTEM_PROMPT = (
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
        return UNAVAILABLE_SYSTEM_PROMPT

    stats = result["stats"]

    top3 = ", ".join(
        f"{s['name']} ({s['completion_precent']}%)" for s in stats[:3]
    )

    pivot = result["pivot"]

    best_city = max(pivot, key=lambda city: city[True])["city"]

    return (
        "You are a data analysis assistant for a task management system. "
        f"Top 3 users by completion rate: {top3}. "
        f"Average completion rate: {result['completion_avg']}%. "
        f"Strongest city (most completed tasks): {best_city}."
    )


def ask(prompt: str, conversation_id: str):
    system_prompt = build_system_prompt()

    history = conversations.setdefault(conversation_id, [])
    history.append({"role": "user", "content": prompt})

    if client is None:
        answer = MOCK_ANSWER
    else:
        response = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=300,
            system=system_prompt,
            messages=history,
        )

        answer = response.content[0].text

    history.append({"role": "assistant", "content": answer})
    return answer


def write_log(prompt_length: int, status: str):
    needs_header = (
        not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0
    )

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if needs_header:
            writer.writerow(["timestamp", "prompt_length", "status"])

        writer.writerow([datetime.now().isoformat(), prompt_length, status])
