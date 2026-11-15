from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKeyConstraint, Index, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class ClaimRow(Base):
    __tablename__ = "claims"
    __table_args__ = (Index("ix_claims_tenant_patient", "tenant_id", "patient_ref"),)
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

class CoveragePeriodRow(Base):
    __tablename__ = "coverage_periods"
    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_coverage_end_not_before_start",
        ),
        Index("ix_coverage_tenant_patient", "tenant_id", "patient_ref"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64))
    patient_ref: Mapped[str] = mapped_column(String(64))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    