from alembic import op
import sqlalchemy as sa
revision = "0005_page_metadata"
down_revision = "0004_page_thumbnails"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("drawing_pages") as batch:
        batch.add_column(sa.Column("metadata_status", sa.String(length=30), nullable=False, server_default="pending"))
        batch.add_column(sa.Column("extracted_text", sa.Text(), nullable=True))
        batch.add_column(sa.Column("drawing_number", sa.String(length=100), nullable=True))
        batch.add_column(sa.Column("drawing_title", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("detected_discipline", sa.String(length=50), nullable=True))
        batch.add_column(sa.Column("scale_text", sa.String(length=100), nullable=True))

def downgrade():
    with op.batch_alter_table("drawing_pages") as batch:
        batch.drop_column("scale_text")
        batch.drop_column("detected_discipline")
        batch.drop_column("drawing_title")
        batch.drop_column("drawing_number")
        batch.drop_column("extracted_text")
        batch.drop_column("metadata_status")
