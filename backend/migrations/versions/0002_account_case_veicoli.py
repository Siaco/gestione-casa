# SPDX-License-Identifier: AGPL-3.0-or-later
"""Account (inviti, recupero password, sessioni), case e veicoli; email unica senza maiuscole.

Revisione: 0002
Precedente: 0001
Creata il: 2026-10-07
Issue: M1-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "casa",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("indirizzo", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "creato_il", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "modificato_il",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_casa")),
    )
    op.create_table(
        "veicolo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("targa", sa.String(length=15), nullable=True),
        sa.Column("tipo", sa.String(length=20), server_default="auto", nullable=False),
        sa.Column("anno", sa.SmallInteger(), nullable=True),
        sa.Column(
            "creato_il", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "modificato_il",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "tipo IN ('auto', 'moto', 'furgone', 'altro')", name=op.f("ck_veicolo_tipo_valido")
        ),
        sa.CheckConstraint("anno BETWEEN 1900 AND 2100", name=op.f("ck_veicolo_anno_valido")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_veicolo")),
    )
    op.create_index(
        "uq_veicolo_targa",
        "veicolo",
        ["targa"],
        unique=True,
        postgresql_where=sa.text("targa IS NOT NULL"),
    )
    op.create_table(
        "invito",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("creato_da_id", sa.Integer(), nullable=False),
        sa.Column("impronta_token", sa.String(length=64), nullable=False),
        sa.Column("scade_il", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usato_il", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "creato_il", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["creato_da_id"],
            ["utente.id"],
            name=op.f("fk_invito_creato_da_id_utente"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invito")),
        sa.UniqueConstraint("impronta_token", name=op.f("uq_invito_impronta_token")),
    )
    op.create_index(op.f("ix_invito_creato_da_id"), "invito", ["creato_da_id"], unique=False)
    op.create_table(
        "sessione",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("utente_id", sa.Integer(), nullable=False),
        sa.Column("impronta_token", sa.String(length=64), nullable=False),
        sa.Column(
            "creata_il", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("scade_il", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "ultimo_uso",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("dispositivo", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["utente_id"],
            ["utente.id"],
            name=op.f("fk_sessione_utente_id_utente"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessione")),
        sa.UniqueConstraint("impronta_token", name=op.f("uq_sessione_impronta_token")),
    )
    op.create_index(op.f("ix_sessione_scade_il"), "sessione", ["scade_il"], unique=False)
    op.create_index(op.f("ix_sessione_utente_id"), "sessione", ["utente_id"], unique=False)
    op.create_table(
        "token_recupero_password",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("utente_id", sa.Integer(), nullable=False),
        sa.Column("impronta_token", sa.String(length=64), nullable=False),
        sa.Column("scade_il", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usato_il", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "creato_il", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["utente_id"],
            ["utente.id"],
            name=op.f("fk_token_recupero_password_utente_id_utente"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_token_recupero_password")),
        sa.UniqueConstraint(
            "impronta_token", name=op.f("uq_token_recupero_password_impronta_token")
        ),
    )
    op.create_index(
        op.f("ix_token_recupero_password_utente_id"),
        "token_recupero_password",
        ["utente_id"],
        unique=False,
    )
    op.drop_constraint(op.f("uq_utente_email"), "utente", type_="unique")
    op.create_index(
        "uq_utente_email_minuscole", "utente", [sa.literal_column("lower(email)")], unique=True
    )


def downgrade() -> None:
    op.drop_index("uq_utente_email_minuscole", table_name="utente")
    op.create_unique_constraint(op.f("uq_utente_email"), "utente", ["email"])
    op.drop_index(
        op.f("ix_token_recupero_password_utente_id"), table_name="token_recupero_password"
    )
    op.drop_table("token_recupero_password")
    op.drop_index(op.f("ix_sessione_utente_id"), table_name="sessione")
    op.drop_index(op.f("ix_sessione_scade_il"), table_name="sessione")
    op.drop_table("sessione")
    op.drop_index(op.f("ix_invito_creato_da_id"), table_name="invito")
    op.drop_table("invito")
    op.drop_index(
        "uq_veicolo_targa", table_name="veicolo", postgresql_where=sa.text("targa IS NOT NULL")
    )
    op.drop_table("veicolo")
    op.drop_table("casa")
