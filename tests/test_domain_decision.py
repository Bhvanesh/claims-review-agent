import pytest
from pydantic import ValidationError

from claims_agent.domain.decision import Citation, DecisionType, Recommendation


def make_rec(decision, citations, confidence=0.8) -> Recommendation:
    return Recommendation(
        claim_id="c-1",
        decision=decision,
        rationale="Reason",
        citations=citations,
        confidence=confidence,
    )


def test_deny_without_citation_rejected():
    with pytest.raises(ValidationError):
        make_rec(DecisionType.DENY, [])


def test_deny_with_citation_accepted():
    rec = make_rec(DecisionType.DENY, [Citation(policy_id="pol-1", passage_id="p-3")])
    assert rec.decision is DecisionType.DENY


def test_pend_without_citation_accepted():
    assert make_rec(DecisionType.PEND, []).decision is DecisionType.PEND


def test_confidence_out_of_range_rejected():
    with pytest.raises(ValidationError):
        make_rec(DecisionType.APPROVE, [], confidence=1.5)