from alembic import op
import sqlalchemy as sa

revision = "0008_issue_coordinate_space"
down_revision = "0007_review_issues"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "review_issues",
        sa.Column("coordinate_space", sa.String(length=20), nullable=False, server_default="normalized"),
    )

def downgrade():
    op.drop_column("review_issues", "coordinate_space")
