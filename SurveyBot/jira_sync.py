from jira import JIRA
import os

options = {"server": os.getenv("JIRA_BASE_URL")}
jira = JIRA(options, basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN")))

def create_jira_ticket(summary, description):
    issue_dict = {
        "project": {"key": os.getenv("JIRA_PROJECT_KEY")},
        "summary": summary,
        "description": description,
        "issuetype": {"name": "Task"},
    }
    jira.create_issue(fields=issue_dict)
