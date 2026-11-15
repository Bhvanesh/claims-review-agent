from datetime import date
from enum import StrEnum
from typing import Self
from pydantic import BaseModel, ConfigDict, Field, model_validator

class CoveragePeriod(BaseModel):
    model_config = ConfigDict(frozen=True)
    tenant_id: str = Field(min_length = 1, max_length=64)
    patient_ref: str = Field(min_length=1, max_length=64)
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def end_not_defore_start(self) -> Self:
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end date must not be before start_date")
        return self

    def contains(self, day:date)-> bool:
        return self.start_date <= day and (self.end_date is None or day <= self.end_date)
        
class EligibilityStatus(StrEnum):
    COVERED = "covered"
    NOT_COVERED_ON_DATE = "not_covered_on_date"
    NO_COVERAGE_RECORD = "no_coverage_record"

class EligibilityResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    status: EligibilityStatus
    covering_period: CoveragePeriod | None = None