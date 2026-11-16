from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from claims_agent.synthetic.cases import LabeledCase, Scenario
from claims_agent.synthetic.generator import generate_cases


class DatasetFile(BaseModel):
    model_config = ConfigDict(frozen=True)

    format_version: Literal[1] = 1
    seed: int
    per_scenario: int = Field(ge=1)
    cases: tuple[LabeledCase, ...]

    @model_validator(mode="after")
    def case_count_matches_header(self) -> Self:
        if len(self.cases) != self.per_scenario * len(Scenario):
            raise ValueError("number of cases does not match per_scenario")
        return self


def build_dataset(seed: int = 7, per_scenario: int = 25) -> DatasetFile:
    return DatasetFile(
        seed=seed, per_scenario=per_scenario, cases=generate_cases(seed, per_scenario)
    )


def dataset_to_json(dataset: DatasetFile) -> str:
    return dataset.model_dump_json(indent=2) + "\n"


def dataset_from_json(text: str) -> DatasetFile:
    return DatasetFile.model_validate_json(text)