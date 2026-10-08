# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tentativi falliti di accesso (limitazione della forza bruta).

Revisione: 0003
Precedente: 0002
Creata il: 2026-10-08
Issue: M1-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tentativo_fallito",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ambito", sa.String(length=20), nullable=False),
        sa.Column("chiave", sa.String(length=300), nullable=False),
        sa.Column(
            "avvenuto_il",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tentativo_fallito")),
    )
    op.create_index(
        "ix_tentativo_fallito_ricerca",
        "tentativo_fallito",
        ["ambito", "chiave", "avvenuto_il"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tentativo_fallito_ricerca", table_name="tentativo_fallito")
    op.drop_table("tentativo_fallito")
