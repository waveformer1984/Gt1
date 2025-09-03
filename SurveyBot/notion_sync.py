from notion_client import Client
import os
import json

notion = Client(auth=os.getenv("NOTION_TOKEN"))
database_id = os.getenv("NOTION_DATABASE_ID")

def send_to_notion(response_data):
    notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Name": {"title": [{"text": {"content": response_data.get("user_id", "Anonymous")}}]},
            "Feedback": {"rich_text": [{"text": {"content": response_data.get("feedback", "")}}]},
            "Rating": {"number": int(response_data.get("rating", 0))}
        }
    )
