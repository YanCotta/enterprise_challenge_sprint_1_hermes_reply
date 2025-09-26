"""placeholder_recovered_missing_revision

Revision ID: 71994744cf8e
Revises: 27b669e05b9d
Create Date: 2025-09-26 (reconstructed)

Context:
The Alembic environment referenced a revision '71994744cf8e' that no longer existed
in the versions directory, causing new revision generation to fail with:
  "Can't locate revision identified by '71994744cf8e'".

This placeholder reintroduces that revision as a no-op to restore a contiguous
history chain. If the original migration performed schema changes, they are
already assumed to be present in the live database; autogenerate on subsequent
revisions will detect and include any drift if it still exists.

DO NOT add schema-altering operations here retroactively. Instead, create a new
forward migration if adjustments are required.
"""
from typing import Sequence, Union

from alembic import op  # noqa: F401  (kept for interface consistency)
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "71994744cf8e"
down_revision: Union[str, None] = "27b669e05b9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:  # pragma: no cover
    # Intentionally no-op placeholder.
    pass


def downgrade() -> None:  # pragma: no cover
    # Intentionally no-op; removing this placeholder would re-break history.
    pass
