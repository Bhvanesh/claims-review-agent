from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

class ClaimLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    procedure_code: str = Field(min_length=1, max_length=10)
    diagnosis_code: str = Field(min_length=1, max_length=10)
    charge_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)

class Claim(BaseModel):
    model_config = ConfigDict(frozen=True)
    claim_id: str = Field(min_length=1, max_length=64)
    tenant_id: str = Field(min_length=1, max_length=64)
    patient_ref: str = Field(min_length=1, max_length=64)
    provider_ref: str = Field(min_length=1, max_length=64)
    service_date: date
    lines: tuple[ClaimLine, ...] = Field(min_length=1)
    @property
    def total_charge(self) -> Decimal:
        return sum((line.charge_amount for line in self.lines), Decimal("0"))


    

