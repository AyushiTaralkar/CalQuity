from pathlib import Path

import pandas as pd
from sqlalchemy import select

from app.database.connection import SessionLocal, engine
from app.database.models import Base, Account, Order, Ticket


EXCEL_FILE = Path("data/raw/parcelpilot_data.xlsx")


ORDER_DATETIME_COLUMNS = [
    "booked_at",
    "pickup_window_start",
    "pickup_window_end",
    "pickup_actual_at",
    "cancellation_requested_at",
]

TICKET_DATETIME_COLUMNS = [
    "created_at",
    "last_customer_message_at",
]


def load_excel():
    accounts = pd.read_excel(
        EXCEL_FILE,
        sheet_name="accounts",
    )

    orders = pd.read_excel(
        EXCEL_FILE,
        sheet_name="orders",
    )

    tickets = pd.read_excel(
        EXCEL_FILE,
        sheet_name="tickets",
    )

    return accounts, orders, tickets


def normalize_data(
    accounts: pd.DataFrame,
    orders: pd.DataFrame,
    tickets: pd.DataFrame,
):
    for column in ORDER_DATETIME_COLUMNS:
        orders[column] = pd.to_datetime(
            orders[column],
            errors="coerce",
        )

    for column in TICKET_DATETIME_COLUMNS:
        tickets[column] = pd.to_datetime(
            tickets[column],
            errors="coerce",
        )

    return accounts, orders, tickets


def validate_data(
    accounts: pd.DataFrame,
    orders: pd.DataFrame,
    tickets: pd.DataFrame,
):
    print("\nRunning validation...")

    if accounts["account_id"].duplicated().any():
        raise ValueError(
            "Duplicate account_id found."
        )

    if orders["order_id"].duplicated().any():
        raise ValueError(
            "Duplicate order_id found."
        )

    if tickets["ticket_id"].duplicated().any():
        raise ValueError(
            "Duplicate ticket_id found."
        )

    account_ids = set(
        accounts["account_id"]
    )

    invalid_order_accounts = (
        set(orders["account_id"]) - account_ids
    )

    invalid_ticket_accounts = (
        set(tickets["account_id"]) - account_ids
    )

    if invalid_order_accounts:
        raise ValueError(
            f"Orders reference unknown accounts: "
            f"{invalid_order_accounts}"
        )

    if invalid_ticket_accounts:
        raise ValueError(
            f"Tickets reference unknown accounts: "
            f"{invalid_ticket_accounts}"
        )

    print("✅ Primary keys are unique.")
    print("✅ Order account references are valid.")
    print("✅ Ticket account references are valid.")


def insert_data(
    accounts: pd.DataFrame,
    orders: pd.DataFrame,
    tickets: pd.DataFrame,
):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with SessionLocal() as session:

        for _, row in accounts.iterrows():
            session.add(
                Account(
                    account_id=row["account_id"],
                    account_name=row["account_name"],
                    plan=row["plan"],
                    status=row["status"],
                    csm=row["csm"],
                    contract_file=row["contract_file"]
                    if pd.notna(row["contract_file"])
                    else None,
                    premium_support=bool(
                        row["premium_support"]
                    ),
                    notes=row["notes"],
                )
            )

        for _, row in orders.iterrows():
            session.add(
                Order(
                    order_id=row["order_id"],
                    account_id=row["account_id"],
                    carrier=row["carrier"],
                    status=row["status"],
                    booked_at=row["booked_at"],
                    pickup_window_start=row[
                        "pickup_window_start"
                    ],
                    pickup_window_end=row[
                        "pickup_window_end"
                    ],
                    pickup_actual_at=row[
                        "pickup_actual_at"
                    ]
                    if pd.notna(row["pickup_actual_at"])
                    else None,
                    shipment_fee_inr=int(
                        row["shipment_fee_inr"]
                    ),
                    carrier_fault=bool(
                        row["carrier_fault"]
                    ),
                    customer_fault=bool(
                        row["customer_fault"]
                    ),
                    cancellation_requested_at=row[
                        "cancellation_requested_at"
                    ]
                    if pd.notna(
                        row["cancellation_requested_at"]
                    )
                    else None,
                    notes=row["notes"],
                )
            )

        for _, row in tickets.iterrows():
            session.add(
                Ticket(
                    ticket_id=row["ticket_id"],
                    account_id=row["account_id"],
                    created_at=row["created_at"],
                    status=row["status"],
                    subject=row["subject"],
                    description=row["description"],
                    channel=row["channel"],
                    assigned_to=row["assigned_to"],
                    last_customer_message_at=row[
                        "last_customer_message_at"
                    ],
                    historical_resolution=row[
                        "historical_resolution"
                    ]
                    if pd.notna(
                        row["historical_resolution"]
                    )
                    else None,
                )
            )

        session.commit()


def verify_database():
    print("\nVerifying database...")

    with SessionLocal() as session:

        accounts = session.scalars(
            select(Account)
        ).all()

        orders = session.scalars(
            select(Order)
        ).all()

        tickets = session.scalars(
            select(Ticket)
        ).all()

        print(
            f"Accounts : {len(accounts)}"
        )

        print(
            f"Orders   : {len(orders)}"
        )

        print(
            f"Tickets  : {len(tickets)}"
        )

        print("\nAccounts:")

        for account in accounts:
            print(
                f"  {account.account_id} → "
                f"{account.account_name}"
            )

        print("\nOrders:")

        for order in orders:
            print(
                f"  {order.order_id} → "
                f"{order.account_id} → "
                f"{order.status}"
            )

        print("\nTickets:")

        for ticket in tickets:
            print(
                f"  {ticket.ticket_id} → "
                f"{ticket.account_id} → "
                f"{ticket.status}"
            )


def main():

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Excel file not found: {EXCEL_FILE}"
        )

    print("Loading Excel...")

    accounts, orders, tickets = load_excel()

    print("Normalizing data...")

    accounts, orders, tickets = normalize_data(
        accounts,
        orders,
        tickets,
    )

    validate_data(
        accounts,
        orders,
        tickets,
    )

    print("\nCreating database...")

    insert_data(
        accounts,
        orders,
        tickets,
    )

    verify_database()

    print(
        "\n🎉 ParcelPilot database created successfully!"
    )


if __name__ == "__main__":
    main()