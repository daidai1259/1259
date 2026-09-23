from alembic import op
import sqlalchemy as sa

revision = "0003_drawing_pages"
down_revision = "0002_drawing_processing"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("drawing_pages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("drawing_id", sa.Integer(), sa.ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("image_name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("dpi", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="rendered"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_drawing_pages_drawing_id", "drawing_pages", ["drawing_id"])

def downgrade():
    op.drop_index("ix_drawing_pages_drawing_id", table_name="drawing_pages")
    op.drop_table("drawing_pages")
