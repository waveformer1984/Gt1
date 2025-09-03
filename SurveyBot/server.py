from fastapi import FastAPI, Request
from dotenv import load_dotenv
from notion_sync import send_to_notion
from jira_sync import create_jira_ticket

import uvicorn

app = FastAPI()
load_dotenv()

@app.post("/survey")
async def receive_survey(req: Request):
    data = await req.json()
    send_to_notion(data)
    if data.get("rating", 5) <= 2:
        create_jira_ticket(
            summary=f"Low Rating from {data.get('user_id', 'Anonymous')}",
            description=data.get("feedback", "No feedback provided")
        )
    return {"status": "ok", "message": "Survey received and processed."}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
