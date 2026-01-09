
import os
from jira import JIRA
import logging

logger = logging.getLogger(__name__)

class JiraService:
    def __init__(self):
        self.server = os.getenv("JIRA_SERVER", "https://jventures.atlassian.net")
        self.user = os.getenv("JIRA_USER", "phariyawit@jventures.co.th")
        self.token = os.getenv("JIRA_API_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "CS")
        
        self.client = None
        if self.token:
            try:
                # JVC uses Cloud Jira which requires API v3
                self.client = JIRA(
                    server=self.server,
                    basic_auth=(self.user, self.token),
                    options={"rest_api_version": "3"}
                )
                logger.info(f"Jira Service initialized for {self.server} (Project: {self.project_key})")
            except Exception as e:
                logger.error(f"Failed to initialize Jira Client: {e}")
        else:
            logger.warning("JIRA_API_TOKEN not set. Jira Service disabled.")

    def create_ticket(self, summary: str, description: str, user_id: str):
        if not self.client:
            return None
        
        try:
            full_description = f"{description}\n\n[Reported by Line User: {user_id}]"
            
            # Convert description to Atlassian Document Format (ADF) for API v3
            adf_description = {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": full_description
                            }
                        ]
                    }
                ]
            }

            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': adf_description,
                'issuetype': {'name': 'Task'},
            }
            new_issue = self.client.create_issue(fields=issue_dict)
            logger.info(f"Created Jira Ticket: {new_issue.key}")
            return {
                "key": new_issue.key,
                "url": f"{self.server}/browse/{new_issue.key}"
            }
        except Exception as e:
            logger.error(f"Failed to create Jira ticket: {e}")
            return None
