import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from claims_agent.synthetic.dataset import build_dataset, dataset_from_json, dataset_to_json

COMMITTED_FILE = Path(__file__).resolve().parents[1] / "evals" / "datasets" / "synthetic_cases_v1.json"


def test_dataset_survives_a_json_round_trip():
    dataset = build_dataset(seed=1, per_scenario=3)
    assert dataset_from_json(dataset_to_json(dataset)) == dataset


def test_same_seed_writes_identical_json():
    first = dataset_to_json(build_dataset(seed=1, per_scenario=2))
    second = dataset_to_json(build_dataset(seed=1, per_scenario=2))
    assert first == second


def test_hand_edited_wrong_label_is_rejected():
    data = json.loads(dataset_to_json(build_dataset(seed=1, per_scenario=2)))
    data["cases"][0]["expected_decision"] = "deny"
    with pytest.raises(ValidationError):
        dataset_from_json(json.dumps(data))


def test_missing_case_is_rejected():
    data = json.loads(dataset_to_json(build_dataset(seed=1, per_scenario=2)))
    data["cases"].pop()
    with pytest.raises(ValidationError):
        dataset_from_json(json.dumps(data))


def test_unknown_format_version_is_rejected():
    data = json.loads(dataset_to_json(build_dataset(seed=1, per_scenario=2)))
    data["format_version"] = 2
    with pytest.raises(ValidationError):
        dataset_from_json(json.dumps(data))


def test_committed_file_matches_the_generator():
    committed = dataset_from_json(COMMITTED_FILE.read_text(encoding="utf-8"))
    assert committed == build_dataset(seed=committed.seed, per_scenario=committed.per_scenario)