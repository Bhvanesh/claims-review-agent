from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from claims_agent.domain.claim import Claim
from claims_agent.domain.coverage import CoveragePeriod
from claims_agent.domain.decision import DecisionType


class Scenario(StrEnum):
    COVERED_NO_DUPLICATE = "covered_no_duplicate"
    DUPLICATE_CLAIM = "duplicate_claim"
    NOT_COVERED_ON_DATE = "not_covered_on_date"
    NO_COVERAGE_RECORD = "no_coverage_record"


EXPECTED_DECISION: dict[Scenario, DecisionType] = {
    Scenario.COVERED_NO_DUPLICATE: DecisionType.APPROVE,
    Scenario.DUPLICATE_CLAIM: DecisionType.DENY,
    Scenario.NOT_COVERED_ON_DATE: DecisionType.DENY,
    Scenario.NO_COVERAGE_RECORD: DecisionType.PEND,
}


class LabeledCase(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: str = Field(min_length=1)
    scenario: Scenario
    expected_decision: DecisionType
    claim: Claim
    history: tuple[Claim, ...] = ()
    coverage: tuple[CoveragePeriod, ...] = ()

    @model_validator(mode="after")
    def decision_matches_scenario(self) -> Self:
        if self.expected_decision is not EXPECTED_DECISION[self.scenario]:
            raise ValueError("expected_decision does not match the scenario")
        return self