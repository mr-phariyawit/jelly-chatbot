"""
Function Calling / Tool Use
Defines tools that the AI can invoke via Gemini function calling.
Tools enable structured actions like creating tickets, searching knowledge base, etc.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a callable tool for the AI."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for parameters
    handler: Optional[Callable] = None


# Tool definitions in Gemini function calling format
TOOL_DEFINITIONS = [
    {
        "name": "search_knowledge_base",
        "description": "Search the knowledge base for information relevant to the user's question. Use this when the user asks about company policies, product features, or technical documentation.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant information"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_support_ticket",
        "description": "Create a support ticket when the issue needs human attention. Use this for billing issues, account problems, or when the user explicitly asks to escalate.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief summary of the issue"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Priority level of the ticket"
                },
                "category": {
                    "type": "string",
                    "description": "Category of the issue (e.g., billing, technical, account)"
                }
            },
            "required": ["summary"]
        }
    },
    {
        "name": "get_business_hours",
        "description": "Get the current business hours and availability status. Use when user asks about operating hours or when staff are available.",
        "parameters": {
            "type": "object",
            "properties": {},
        }
    },
]


class ToolExecutor:
    """Executes tool calls from the AI and returns results."""

    def __init__(self, rag_service=None, jira_service=None):
        self.rag_service = rag_service
        self.jira_service = jira_service
        self._handlers = {
            "search_knowledge_base": self._handle_search,
            "create_support_ticket": self._handle_create_ticket,
            "get_business_hours": self._handle_business_hours,
        }

    def execute(self, tool_name: str, args: Dict[str, Any], **context) -> Dict[str, Any]:
        """Execute a tool call and return the result."""
        handler = self._handlers.get(tool_name)
        if not handler:
            logger.warning(f"Unknown tool: {tool_name}")
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = handler(args, **context)
            logger.info(f"Tool '{tool_name}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution failed: {e}")
            return {"error": str(e)}

    def _handle_search(self, args: Dict, **context) -> Dict:
        """Search the knowledge base."""
        db = context.get("db")
        bot_id = context.get("bot_id")

        if not self.rag_service or not db or not bot_id:
            return {"result": "Knowledge base search not available"}

        query = args.get("query", "")
        results = self.rag_service.search(db, bot_id, query)
        return {"result": results if results else "No relevant information found."}

    def _handle_create_ticket(self, args: Dict, **context) -> Dict:
        """Create a support ticket via Jira."""
        if not self.jira_service:
            return {"result": "Ticket system not configured", "ticket_key": None}

        user_id = context.get("user_id", "Unknown")
        summary = args.get("summary", "Support request")
        priority = args.get("priority", "medium")
        category = args.get("category", "General")

        try:
            result = self.jira_service.create_ticket(
                summary=summary,
                description=f"User ID: {user_id}\nPriority: {priority}\nCategory: {category}",
                user_id=user_id,
            )
            ticket_key = result.get("key") if result else None
            return {"result": f"Ticket created: {ticket_key}" if ticket_key else "Failed to create ticket", "ticket_key": ticket_key}
        except Exception as e:
            return {"result": f"Failed to create ticket: {e}", "ticket_key": None}

    def _handle_business_hours(self, args: Dict, **context) -> Dict:
        """Return business hours info."""
        return {
            "result": "เวลาทำการ: วันจันทร์-ศุกร์ 8:30 - 17:30 น. (เว้นวันหยุดราชการ)",
            "is_open": True,
        }

    def get_gemini_tools_config(self) -> List[Dict]:
        """Get tool definitions in Gemini API format."""
        return [{
            "function_declarations": TOOL_DEFINITIONS
        }]
