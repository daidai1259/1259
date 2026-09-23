from alembic import op
import sqlalchemy as sa
revision = "0004_page_thumbnails"
down_revision = "0003_drawing_pages"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("drawing_pages") as batch:
        batch.add_column(sa.Column("thumbnail_name", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("thumbnail_width", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("thumbnail_height", sa.Integer(), nullable=True))
        batch.create_unique_constraint("uq_drawing_pages_thumbnail_name", ["thumbnail_name"])

def downgrade():
    with op.batch_alter_table("drawing_pages") as batch:
        batch.drop_constraint("uq_drawing_pages_thumbnail_name", type_="unique")
        batch.drop_column("thumbnail_height")
        batch.drop_column("thumbnail_width")
        batch.drop_column("thumbnail_name")
