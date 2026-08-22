from typing import Optional

from app.database.repository import (
    lookup_account,
    lookup_order,
    lookup_ticket,
)

from app.rag.retriever import Retriever


# ============================================================
# DATABASE TOOLS
# ============================================================

def lookup_account_tool(account_id: str) -> dict:
    """
    Look up a single account.
    """

    account = lookup_account(account_id)

    if account is None:
        return {
            "success": False,
            "error": "Account not found",
            "account_id": account_id,
        }

    return {
        "success": True,
        "account": account,
    }


def lookup_order_tool(order_id: str) -> dict:
    """
    Look up a single order.
    """

    order = lookup_order(order_id)

    if order is None:
        return {
            "success": False,
            "error": "Order not found",
            "order_id": order_id,
        }

    return {
        "success": True,
        "order": order,
    }


def lookup_ticket_tool(ticket_id: str) -> dict:
    """
    Look up a single support ticket.
    """

    ticket = lookup_ticket(ticket_id)

    if ticket is None:
        return {
            "success": False,
            "error": "Ticket not found",
            "ticket_id": ticket_id,
        }

    return {
        "success": True,
        "ticket": ticket,
    }


# ============================================================
# RAG TOOL
# ============================================================

_retriever = None


def search_documents(
    query: str,
    account_id: Optional[str] = None,
    top_k: int = 3,
) -> list:
    """
    Search ParcelPilot documentation using the existing
    FAISS retriever.

    This does NOT call Gemini.
    """

    global _retriever

    if _retriever is None:
        _retriever = Retriever(top_k=top_k)

    results = _retriever.retrieve(
        query=query,
        account_id=account_id,
    )

    return results[:top_k]


# ============================================================
# TOOL DISPATCHER
# ============================================================

def execute_tool(
    tool_name: str,
    **kwargs,
):
    """
    Execute one of the supported agent tools.

    This gives the future LLM agent a single controlled
    interface for calling application tools.
    """

    tools = {
        "lookup_account": lookup_account_tool,
        "lookup_order": lookup_order_tool,
        "lookup_ticket": lookup_ticket_tool,
        "search_documents": search_documents,
    }

    tool = tools.get(tool_name)

    if tool is None:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
        }

    try:
        return tool(**kwargs)

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
        }