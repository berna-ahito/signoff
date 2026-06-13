"""add procure to pay controls

Revision ID: 9c2f1a4b8e21
Revises: f8c64ab2a625
Create Date: 2026-06-13 18:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c2f1a4b8e21"
down_revision: Union[str, Sequence[str], None] = "f8c64ab2a625"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("departments", sa.Column("code", sa.String(length=20), nullable=True))
    op.add_column("departments", sa.Column("monthly_budget", sa.Float(), nullable=False, server_default="0"))
    op.add_column("departments", sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()))
    op.create_index("uq_departments_code", "departments", ["code"], unique=True)

    op.add_column("vendors", sa.Column("contact_name", sa.String(length=255), nullable=True))
    op.add_column("vendors", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("vendors", sa.Column("phone", sa.String(length=50), nullable=True))
    op.add_column("vendors", sa.Column("category", sa.String(length=100), nullable=True))
    op.add_column("vendors", sa.Column("payment_terms", sa.String(length=100), nullable=True))
    op.add_column("vendors", sa.Column("is_preferred", sa.Boolean(), nullable=True, server_default=sa.false()))
    op.add_column("vendors", sa.Column("notes", sa.Text(), nullable=True))
    op.execute("UPDATE vendors SET email = contact_email WHERE email IS NULL AND contact_email IS NOT NULL")

    with op.batch_alter_table("purchase_requests") as batch_op:
        batch_op.add_column(sa.Column("vendor_name", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("department_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("submitted_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("approval_due_at", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            "fk_purchase_requests_department_id_departments",
            "departments",
            ["department_id"],
            ["id"],
        )
        batch_op.create_index("idx_requests_department_id", ["department_id"])
        batch_op.create_index("idx_requests_approval_due_at", ["approval_due_at"])

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("po_number", sa.String(length=20), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["request_id"], ["purchase_requests.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("po_number"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index(op.f("ix_purchase_orders_id"), "purchase_orders", ["id"], unique=False)
    op.create_index(op.f("ix_purchase_orders_po_number"), "purchase_orders", ["po_number"], unique=True)

    op.create_table(
        "purchase_order_line_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("total_price", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_purchase_order_line_items_id"), "purchase_order_line_items", ["id"], unique=False)

    op.create_table(
        "receiving_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("received_by", sa.Integer(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.ForeignKeyConstraint(["received_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_receiving_records_id"), "receiving_records", ["id"], unique=False)

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("invoice_number", sa.String(length=100), nullable=False),
        sa.Column("invoice_amount", sa.Float(), nullable=False),
        sa.Column("invoice_date", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("attachment_id", sa.Integer(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["attachment_id"], ["request_attachments.id"]),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_invoices_id"), "invoices", ["id"], unique=False)

    op.create_table(
        "request_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["request_id"], ["purchase_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_request_comments_id"), "request_comments", ["id"], unique=False)
    op.create_index("idx_request_comments_request_id", "request_comments", ["request_id"])


def downgrade() -> None:
    op.drop_index("idx_request_comments_request_id", table_name="request_comments")
    op.drop_index(op.f("ix_request_comments_id"), table_name="request_comments")
    op.drop_table("request_comments")
    op.drop_index(op.f("ix_invoices_id"), table_name="invoices")
    op.drop_table("invoices")
    op.drop_index(op.f("ix_receiving_records_id"), table_name="receiving_records")
    op.drop_table("receiving_records")
    op.drop_index(op.f("ix_purchase_order_line_items_id"), table_name="purchase_order_line_items")
    op.drop_table("purchase_order_line_items")
    op.drop_index(op.f("ix_purchase_orders_po_number"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_id"), table_name="purchase_orders")
    op.drop_table("purchase_orders")
    with op.batch_alter_table("purchase_requests") as batch_op:
        batch_op.drop_index("idx_requests_approval_due_at")
        batch_op.drop_index("idx_requests_department_id")
        batch_op.drop_constraint("fk_purchase_requests_department_id_departments", type_="foreignkey")
        batch_op.drop_column("approval_due_at")
        batch_op.drop_column("submitted_at")
        batch_op.drop_column("department_id")
        batch_op.drop_column("vendor_name")
    op.drop_column("vendors", "notes")
    op.drop_column("vendors", "is_preferred")
    op.drop_column("vendors", "payment_terms")
    op.drop_column("vendors", "category")
    op.drop_column("vendors", "phone")
    op.drop_column("vendors", "email")
    op.drop_column("vendors", "contact_name")
    op.drop_index("uq_departments_code", table_name="departments")
    op.drop_column("departments", "is_active")
    op.drop_column("departments", "monthly_budget")
    op.drop_column("departments", "code")
