from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from claims_agent.domain.claim import Claim, ClaimLine

class ClaimInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    claim_id: str = Field(min_length=1, max_length=64)
    patient_ref: str = Field(min_length=1, max_length=64)
    provider_ref: str = Field(min_length=1, max_length=64)
    service_date:date
    lines: tuple[ClaimLine, ...] = Field(min_length=1)

    def to_claim(self, tenant_id: str) -> Claim:
        return Claim(
            claim_id = self.claim_id,
            tenant_id=tenant_id,
            patient_ref=self.patient_ref,
            provider_ref=self.provider_ref,
            service_date=self.service_date,
            lines=self.lines
        )