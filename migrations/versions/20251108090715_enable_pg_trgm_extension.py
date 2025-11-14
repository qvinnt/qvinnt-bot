"""enable_pg_trgm_extension

Revision ID: 7c04e846c3d0
Revises: 6e857bc50c61
Create Date: 2025-11-08 09:07:15.925521

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c04e846c3d0'
down_revision: Union[str, None] = '6e857bc50c61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for fuzzy text search
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    
    # Create GIN indexes for better trigram search performance
    op.create_index(
        'idx_tracks_title_trgm',
        'tracks',
        [sa.text('title gin_trgm_ops')],
        postgresql_using='gin',
    )
    op.create_index(
        'idx_tracks_artist_trgm',
        'tracks',
        [sa.text('artist gin_trgm_ops')],
        postgresql_using='gin',
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_tracks_artist_trgm', table_name='tracks')
    op.drop_index('idx_tracks_title_trgm', table_name='tracks')
    
    # Drop pg_trgm extension
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')
