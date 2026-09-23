from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("projects", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(length=200), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("drawings", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False), sa.Column("original_name", sa.String(length=255), nullable=False), sa.Column("stored_name", sa.String(length=255), nullable=False, unique=True), sa.Column("mime_type", sa.String(length=100), nullable=False), sa.Column("size_bytes", sa.Integer(), nullable=False), sa.Column("sha256", sa.String(length=64), nullable=False), sa.Column("page_count", sa.Integer(), nullable=True), sa.Column("drawing_number", sa.String(length=100), nullable=True), sa.Column("discipline", sa.String(length=50), nullable=True), sa.Column("status", sa.String(length=30), nullable=False, server_default="uploaded"), sa.Column("processing_progress", sa.Integer(), nullable=False, server_default="0"), sa.Column("error", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_drawings_sha256", "drawings", ["sha256"])
    op.create_table("drawing_pages", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("drawing_id", sa.Integer(), sa.ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False), sa.Column("page_number", sa.Integer(), nullable=False), sa.Column("image_name", sa.String(length=255), nullable=False, unique=True), sa.Column("width", sa.Integer(), nullable=False), sa.Column("height", sa.Integer(), nullable=False), sa.Column("dpi", sa.Integer(), nullable=False), sa.Column("status", sa.String(length=30), nullable=False, server_default="rendered"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_drawing_pages_drawing_id", "drawing_pages", ["drawing_id"])
    op.create_table("review_tasks", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False), sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"), sa.Column("progress", sa.Integer(), nullable=False, server_default="0"), sa.Column("error", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

def downgrade():
    op.drop_table("drawing_pages")
    op.drop_index("ix_drawings_sha256", table_name="drawings")
    op.drop_table("review_tasks")
    op.drop_table("drawings")
    op.drop_table("projects")
