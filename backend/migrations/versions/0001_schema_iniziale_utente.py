# SPDX-License-Identifier: AGPL-3.0-or-later
"""Schema iniziale: tabella utente.

Revisione: 0001
Precedente: nessuna
Creata il: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "utente",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("hash_password", sa.String(length=255), nullable=False),
        sa.Column("lingua", sa.String(length=10), server_default="it", nullable=False),
        sa.Column("attivo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "creato_il", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "modificato_il",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_utente")),
        sa.UniqueConstraint("email", name=op.f("uq_utente_email")),
    )


def downgrade() -> None:
    op.drop_table("utente")
