from alembic import op
import sqlalchemy as sa

revision = "0006_page_texts"
down_revision = "0005_page_metadata"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "drawing_page_texts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("page_id", sa.Integer(), sa.ForeignKey("drawing_pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("x0", sa.Float(), nullable=False),
        sa.Column("y0", sa.Float(), nullable=False),
        sa.Column("x1", sa.Float(), nullable=False),
        sa.Column("y1", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("block_no", sa.Integer(), nullable=True),
        sa.Column("line_no", sa.Integer(), nullable=True),
        sa.Column("word_no", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_drawing_page_texts_page_id", "drawing_page_texts", ["page_id"])

def downgrade():
    op.drop_index("ix_drawing_page_texts_page_id", table_name="drawing_page_texts")
    op.drop_table("drawing_page_texts")
