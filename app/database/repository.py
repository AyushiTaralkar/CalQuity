from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database.connection import SessionLocal
from app.database.models import Account, Order, Ticket


# ============================================================
# ACCOUNT QUERIES
# ============================================================

def lookup_account(account_id: str) -> dict | None:
    """
    Look up a single account by account ID.

    Example:
        lookup_account("ACCT-001")
    """

    with SessionLocal() as session:
        account = session.scalar(
            select(Account)
            .where(Account.account_id == account_id)
        )

        if account is None:
            return None

        return {
            "account_id": account.account_id,
            "account_name": account.account_name,
            "plan": account.plan,
            "status": account.status,
            "csm": account.csm,
            "contract_file": account.contract_file,
            "premium_support": account.premium_support,
            "notes": account.notes,
        }


# ============================================================
# ORDER QUERIES
# ============================================================

def lookup_order(order_id: str) -> dict | None:
    """
    Look up a single order by order ID.

    Also returns the associated account name.

    Example:
        lookup_order("ORD-1001")
    """

    with SessionLocal() as session:
        order = session.scalar(
            select(Order)
            .options(joinedload(Order.account))
            .where(Order.order_id == order_id)
        )

        if order is None:
            return None

        return {
            "order_id": order.order_id,
            "account_id": order.account_id,
            "account_name": order.account.account_name,
            "carrier": order.carrier,
            "status": order.status,

            "booked_at": (
                order.booked_at.isoformat()
                if order.booked_at
                else None
            ),

            "pickup_window_start": (
                order.pickup_window_start.isoformat()
                if order.pickup_window_start
                else None
            ),

            "pickup_window_end": (
                order.pickup_window_end.isoformat()
                if order.pickup_window_end
                else None
            ),

            "pickup_actual_at": (
                order.pickup_actual_at.isoformat()
                if order.pickup_actual_at
                else None
            ),

            "shipment_fee_inr": order.shipment_fee_inr,
            "carrier_fault": order.carrier_fault,
            "customer_fault": order.customer_fault,

            "cancellation_requested_at": (
                order.cancellation_requested_at.isoformat()
                if order.cancellation_requested_at
                else None
            ),

            "notes": order.notes,
        }


# ============================================================
# TICKET QUERIES
# ============================================================

def lookup_ticket(ticket_id: str) -> dict | None:
    """
    Look up a single ticket by ticket ID.

    Example:
        lookup_ticket("TKT-505")
    """

    with SessionLocal() as session:
        ticket = session.scalar(
            select(Ticket)
            .options(joinedload(Ticket.account))
            .where(Ticket.ticket_id == ticket_id)
        )

        if ticket is None:
            return None

        return {
            "ticket_id": ticket.ticket_id,
            "account_id": ticket.account_id,
            "account_name": ticket.account.account_name,

            "created_at": (
                ticket.created_at.isoformat()
                if ticket.created_at
                else None
            ),

            "status": ticket.status,
            "subject": ticket.subject,
            "description": ticket.description,
            "channel": ticket.channel,
            "assigned_to": ticket.assigned_to,

            "last_customer_message_at": (
                ticket.last_customer_message_at.isoformat()
                if ticket.last_customer_message_at
                else None
            ),

            # IMPORTANT:
            # This is historical context only.
            # The AI must NOT treat it as authoritative policy.
            "historical_resolution": ticket.historical_resolution,
        }


# ============================================================
# ACCOUNT → ORDERS
# ============================================================

def get_account_orders(account_id: str) -> list[dict]:
    """
    Get all orders belonging to an account.

    Example:
        get_account_orders("ACCT-001")
    """

    with SessionLocal() as session:
        orders = session.scalars(
            select(Order)
            .where(Order.account_id == account_id)
            .order_by(Order.booked_at)
        ).all()

        return [
            {
                "order_id": order.order_id,
                "carrier": order.carrier,
                "status": order.status,
                "shipment_fee_inr": order.shipment_fee_inr,
                "carrier_fault": order.carrier_fault,
                "customer_fault": order.customer_fault,

                "booked_at": (
                    order.booked_at.isoformat()
                    if order.booked_at
                    else None
                ),
            }
            for order in orders
        ]


# ============================================================
# ACCOUNT → TICKETS
# ============================================================

def get_account_tickets(account_id: str) -> list[dict]:
    """
    Get all tickets belonging to an account.

    Example:
        get_account_tickets("ACCT-001")
    """

    with SessionLocal() as session:
        tickets = session.scalars(
            select(Ticket)
            .where(Ticket.account_id == account_id)
            .order_by(Ticket.created_at)
        ).all()

        return [
            {
                "ticket_id": ticket.ticket_id,
                "status": ticket.status,
                "subject": ticket.subject,
                "description": ticket.description,
                "channel": ticket.channel,
                "assigned_to": ticket.assigned_to,

                "created_at": (
                    ticket.created_at.isoformat()
                    if ticket.created_at
                    else None
                ),
            }
            for ticket in tickets
        ]

def get_all_accounts():
    """
    Return all customer accounts.

    Used only for account authorization / tenant isolation.
    """

    with SessionLocal() as db:

        accounts = db.query(Account).all()

        return [
            {
                "account_id": account.account_id,
                "account_name": account.account_name,
            }
            for account in accounts
        ]
def account_exists(account_id: str) -> bool:
    with SessionLocal() as db:
        return db.query(Account).filter(
            Account.account_id == account_id
        ).first() is not None


def order_belongs_to_account(
    order_id: str,
    account_id: str
) -> bool:
    with SessionLocal() as db:
        order = db.query(Order).filter(
            Order.order_id == order_id
        ).first()

        if not order:
            return False

        return order.account_id == account_id


def ticket_belongs_to_account(
    ticket_id: str,
    account_id: str
) -> bool:
    with SessionLocal() as db:
        ticket = db.query(Ticket).filter(
            Ticket.ticket_id == ticket_id
        ).first()

        if not ticket:
            return False

        return ticket.account_id == account_id