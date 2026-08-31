"""Initial AlgoRecall schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("settings", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("red_interval", sa.Integer(), nullable=False), sa.Column("yellow_first_interval", sa.Integer(), nullable=False), sa.Column("yellow_repeat_interval", sa.Integer(), nullable=False), sa.Column("green_first_interval", sa.Integer(), nullable=False), sa.Column("green_second_interval", sa.Integer(), nullable=False), sa.Column("notifications_enabled", sa.Boolean(), nullable=False), sa.Column("notification_time", sa.String(5), nullable=False))
    op.create_table("tags", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(50), nullable=False, unique=True), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("problems", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("leetcode_id", sa.Integer(), nullable=False), sa.Column("title", sa.String(200), nullable=False), sa.Column("title_en", sa.String(200)), sa.Column("leetcode_url", sa.String(500)), sa.Column("difficulty", sa.String(20), nullable=False), sa.Column("rating", sa.String(20), nullable=False), sa.Column("review_stage", sa.String(30), nullable=False), sa.Column("mistake_reason", sa.Text()), sa.Column("my_solution", sa.Text()), sa.Column("correct_solution", sa.Text()), sa.Column("key_points", sa.Text()), sa.Column("time_complexity", sa.String(100)), sa.Column("space_complexity", sa.String(100)), sa.Column("code", sa.Text()), sa.Column("last_reviewed_at", sa.DateTime()), sa.Column("next_review_at", sa.Date()), sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    for name, col, unique in [("ix_problems_leetcode_id", "leetcode_id", True), ("ix_problems_next_review_at", "next_review_at", False), ("ix_problems_rating", "rating", False), ("ix_problems_review_stage", "review_stage", False), ("ix_problems_is_archived", "is_archived", False)]: op.create_index(name, "problems", [col], unique=unique)
    op.create_table("problem_tags", sa.Column("problem_id", sa.Integer(), sa.ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True), sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True))
    op.create_index("ix_problem_tags_tag_id", "problem_tags", ["tag_id"])
    op.create_table("review_records", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("problem_id", sa.Integer(), sa.ForeignKey("problems.id", ondelete="CASCADE"), nullable=False), sa.Column("reviewed_at", sa.DateTime(), nullable=False), sa.Column("rating", sa.String(20), nullable=False), sa.Column("stage_before", sa.String(30)), sa.Column("stage_after", sa.String(30), nullable=False), sa.Column("scheduled_interval_days", sa.Integer()), sa.Column("next_review_at", sa.Date()), sa.Column("duration_minutes", sa.Integer()), sa.Column("used_hint", sa.Boolean(), nullable=False), sa.Column("viewed_solution", sa.Boolean(), nullable=False), sa.Column("note", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_review_records_problem_id", "review_records", ["problem_id"])
    op.create_index("ix_review_records_reviewed_at", "review_records", ["reviewed_at"])


def downgrade() -> None:
    op.drop_table("review_records")
    op.drop_table("problem_tags")
    op.drop_table("problems")
    op.drop_table("tags")
    op.drop_table("settings")

