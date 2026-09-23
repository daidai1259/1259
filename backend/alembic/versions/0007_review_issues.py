from alembic import op
import sqlalchemy as sa

revision = "0007_review_issues"
down_revision = "0006_page_texts"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("review_tasks", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("review_tasks", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("review_tasks", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "review_issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("review_id", sa.Integer(), sa.ForeignKey("review_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_id", sa.Integer(), sa.ForeignKey("drawing_pages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rule_id", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("x0", sa.Float(), nullable=True),
        sa.Column("y0", sa.Float(), nullable=True),
        sa.Column("x1", sa.Float(), nullable=True),
        sa.Column("y1", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_issues_review_id", "review_issues", ["review_id"])
    op.create_index("ix_review_issues_page_id", "review_issues", ["page_id"])

def downgrade():
    op.drop_index("ix_review_issues_page_id", table_name="review_issues")
    op.drop_index("ix_review_issues_review_id", table_name="review_issues")
    op.drop_table("review_issues")
    op.drop_column("review_tasks", "finished_at")
    op.drop_column("review_tasks", "started_at")
    op.drop_column("review_tasks", "attempts")
