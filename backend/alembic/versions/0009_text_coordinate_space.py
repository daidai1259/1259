from alembic import op
import sqlalchemy as sa

revision = "0009_text_coordinate_space"
down_revision = "0008_issue_coordinate_space"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "drawing_page_texts",
        sa.Column("coordinate_space", sa.String(length=20), nullable=False, server_default="source"),
    )

def downgrade():
    op.drop_column("drawing_page_texts", "coordinate_space")
