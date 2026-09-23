from alembic import op
import sqlalchemy as sa

revision = "0002_drawing_processing"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("drawings") as batch:
        batch.add_column(sa.Column("sha256", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("processing_progress", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("error", sa.Text(), nullable=True))
    op.create_index("ix_drawings_sha256", "drawings", ["sha256"])
    op.execute("UPDATE drawings SET sha256 = '' WHERE sha256 IS NULL")
    with op.batch_alter_table("drawings") as batch:
        batch.alter_column("sha256", nullable=False)

def downgrade():
    op.drop_index("ix_drawings_sha256", table_name="drawings")
    with op.batch_alter_table("drawings") as batch:
        batch.drop_column("error")
        batch.drop_column("processing_progress")
        batch.drop_column("sha256")
