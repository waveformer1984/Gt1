import json
import os
from dotenv import load_dotenv
from notion_sync import send_to_notion
from jira_sync import create_jira_ticket

load_dotenv()

def load_questions():
    with open("questions.json", "r") as f:
        return json.load(f)

def collect_responses(questions):
    print("Welcome to SurveyBot!\n")
    response = {}
    for q in questions:
        answer = input(f"{q['question']} ")
        if q["type"] == "rating":
            try:
                answer = int(answer)
            except ValueError:
                answer = 0
            response["rating"] = answer
        else:
            response["feedback"] = answer
    response["user_id"] = input("Enter your name (or leave blank): ") or "Anonymous"
    return response

def save_response(response):
    file_path = "responses.csv"
    headers = ["user_id", "rating", "feedback"]
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write(",".join(headers) + "\n")
    with open(file_path, "a") as f:
        f.write(f"{response['user_id']},{response['rating']},{response['feedback']}\n")

def trigger_integrations(response):
    send_to_notion(response)
    if response.get("rating", 5) <= 2:
        create_jira_ticket(
            summary=f"Low Rating from {response['user_id']}",
            description=response.get("feedback", "No feedback provided")
        )

if __name__ == "__main__":
    questions = load_questions()
    response = collect_responses(questions)
    save_response(response)
    trigger_integrations(response)
    print("\n✅ Response saved and synced.")
