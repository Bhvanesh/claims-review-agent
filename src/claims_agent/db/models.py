from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKeyConstraint, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class ClaimRow(Base):
    __tablename__ = "claims"

    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    patient_ref: Mapped[str] = mapped_column(String(64))
    provider_ref: Mapped[str] = mapped_column(String(64))
    service_date: Mapped[date]= mapped_column(Date)

    lines: Mapped[list["ClaimLineRow"]] = relationship(
        back_populates = "claim",
        cascade = "all, delete-orphan",
        order_by = "ClaimLineRow.line_no",
    )

class ClaimLineRow(Base):
    __tablename__ = "claim_lines"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "claim_id"],
            ["claims.tenant_id", "claims.claim_id"],
            ondelete = "CASCADE",
        ),
    )
    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    line_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    procedure_code: Mapped[str] = mapped_column(String(10))
    diagnosis_code: Mapped[str] = mapped_column(String(10))
    charge_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    claim: Mapped[ClaimRow] = relationship(back_populates="lines")