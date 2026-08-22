from app.agent.tools import (
    lookup_account_tool,
    lookup_order_tool,
    lookup_ticket_tool,
)


def test_lookup_account():
    result = lookup_account_tool("ACCT-001")

    assert result["success"] is True
    assert result["account"]["account_id"] == "ACCT-001"


def test_lookup_order():
    result = lookup_order_tool("ORD-1001")

    assert result["success"] is True
    assert result["order"]["order_id"] == "ORD-1001"


def test_lookup_ticket():
    result = lookup_ticket_tool("TKT-505")

    assert result["success"] is True
    assert result["ticket"]["ticket_id"] == "TKT-505"


def test_unknown_order():
    result = lookup_order_tool("ORD-DOES-NOT-EXIST")

    assert result["success"] is False