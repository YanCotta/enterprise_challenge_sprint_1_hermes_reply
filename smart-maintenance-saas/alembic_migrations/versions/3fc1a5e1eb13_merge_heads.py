"""merge_heads

Revision ID: 3fc1a5e1eb13
Revises: 4a7245cea299, 0907b6dcc25b
Create Date: 2025-09-02 15:18:02.717204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fc1a5e1eb13'
down_revision: Union[str, None] = ('4a7245cea299', '0907b6dcc25b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
