from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

class DecisionType(StrEnum):
    APPROVE = "approve"
    DENY = "deny"
    PEND = "pend"

class Citation(BaseModel):
    model_config = ConfigDict(frozen=True)
    policy_id: str = Field(min_length=1)
    passage_id: str = Field(min_length=1)

class Recommendation(BaseModel):
    model_config = ConfigDict(frozen=True)
    claim_id: str = Field(min_length=1)
    decision: DecisionType
    rationale: str = Field(min_length=1)
    citations: tuple[Citation, ...] = ()
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def denial_requires_citation(self)-> Self:
        if self.decision is DecisionType.DENY and not self.citations:
            raise ValueError("a denial must cite at least one policy passage")
        return self

    

