from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    account_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    csm: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    contract_file: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    premium_support: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="account",
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="account",
    )


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    account_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("accounts.account_id"),
        nullable=False,
        index=True,
    )

    carrier: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    booked_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    pickup_window_start: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    pickup_window_end: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    pickup_actual_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    shipment_fee_inr: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    carrier_fault: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    customer_fault: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    cancellation_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    account: Mapped["Account"] = relationship(
        back_populates="orders",
    )


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    account_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("accounts.account_id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    subject: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    assigned_to: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    last_customer_message_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    historical_resolution: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    account: Mapped["Account"] = relationship(
        back_populates="tickets",
    )