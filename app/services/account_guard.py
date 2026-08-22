import re
from typing import Optional

from app.database.repository import (
    lookup_account,
    get_all_accounts,
)


class AccountAccessError(Exception):
    """Raised when cross-account access is attempted."""
    pass


class AccountAccessGuard:

    def __init__(self, account_id: Optional[str]):

        self.account_id = account_id

        if account_id:
            self.account = lookup_account(account_id)
        else:
            self.account = None

    # ============================================================
    # ACCOUNT VALIDATION
    # ============================================================

    def validate_account(self):

        if not self.account_id:
            return

        if not self.account:

            raise AccountAccessError(
                f"Account {self.account_id} was not found."
            )

    # ============================================================
    # ORDER ACCESS
    # ============================================================

    def validate_order_access(self, order):

        if not order:
            return

        if not self.account_id:

            raise AccountAccessError(
                "Account context is required to access order data."
            )

        if order.get("account_id") != self.account_id:

            raise AccountAccessError(
                "Access denied: this order belongs to another account."
            )

    # ============================================================
    # TICKET ACCESS
    # ============================================================

    def validate_ticket_access(self, ticket):

        if not ticket:
            return

        if not self.account_id:

            raise AccountAccessError(
                "Account context is required to access ticket data."
            )

        if ticket.get("account_id") != self.account_id:

            raise AccountAccessError(
                "Access denied: this ticket belongs to another account."
            )

    # ============================================================
    # CROSS ACCOUNT QUESTION
    # ============================================================

    def validate_question(self, question: str):

        if not self.account_id:
            return

        current_account_name = (
            self.account.get("account_name", "")
            if self.account
            else ""
        )

        question_lower = question.lower()

        # --------------------------------------------------------
        # Check explicit account IDs
        # --------------------------------------------------------

        account_ids = re.findall(
            r"\bACCT-\d+\b",
            question,
            flags=re.IGNORECASE,
        )

        for requested_id in account_ids:

            requested_id = requested_id.upper()

            if requested_id != self.account_id.upper():

                raise AccountAccessError(
                    "Access denied: you cannot access "
                    "another customer's account information."
                )

        # --------------------------------------------------------
        # Check customer names
        # --------------------------------------------------------

        accounts = get_all_accounts()

        for account in accounts:

            other_account_id = account.get("account_id")
            other_account_name = (
                account.get("account_name") or ""
            )

            if not other_account_name:
                continue

            # Ignore the currently authorized account.
            if other_account_id == self.account_id:
                continue

            if other_account_name.lower() in question_lower:

                raise AccountAccessError(
                    "Access denied: you cannot access "
                    "another customer's account information."
                )