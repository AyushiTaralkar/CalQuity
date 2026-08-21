from pprint import pprint

from app.database.repository import (
    lookup_account,
    lookup_order,
    lookup_ticket,
    get_account_orders,
    get_account_tickets,
)


def main():

    print("\n" + "=" * 60)
    print("ACCOUNT")
    print("=" * 60)

    pprint(lookup_account("ACCT-001"))

    print("\n" + "=" * 60)
    print("ORDER")
    print("=" * 60)

    pprint(lookup_order("ORD-1001"))

    print("\n" + "=" * 60)
    print("TICKET")
    print("=" * 60)

    pprint(lookup_ticket("TKT-505"))

    print("\n" + "=" * 60)
    print("ACCOUNT ORDERS")
    print("=" * 60)

    pprint(get_account_orders("ACCT-001"))

    print("\n" + "=" * 60)
    print("ACCOUNT TICKETS")
    print("=" * 60)

    pprint(get_account_tickets("ACCT-001"))

    print("\n" + "=" * 60)
    print("MISSING ORDER")
    print("=" * 60)

    pprint(lookup_order("ORD-9999"))


if __name__ == "__main__":
    main()