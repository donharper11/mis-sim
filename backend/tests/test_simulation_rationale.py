from app.simulation.rationale import review_rationale
from app.simulation.types import RationaleReviewV1


def test_disabled_review_is_explicit_and_neutral():
    review = review_rationale(
        note="The open signal is an operating risk.", event="event", option="fund",
        rationale_tag="capacity_risk", option_tags=["capacity_risk"],
    )
    assert review.status == "not_scored"
    assert review.provider == "disabled"
    assert review.modifier == 1.0


class _Provider:
    def evaluate(self, **_kwargs):
        return {"quality": 0.8, "modifier": 1.08, "provider": "test", "model": "fake"}


def test_provider_output_is_bounded_and_instructor_visible():
    review = review_rationale(
        note="The open signal is an operating risk.", event="event", option="fund",
        rationale_tag="capacity_risk", option_tags=["capacity_risk"], evaluator=_Provider(),
    )
    assert review.status == "scored"
    assert review.quality == 0.8
    assert review.modifier == 1.08
    assert review.model == "fake"


class _Malformed:
    def evaluate(self, **_kwargs):
        return {"quality": 1.4, "modifier": 1.2}


def test_malformed_provider_degrades_without_blocking():
    review = review_rationale(
        note="A note", event="event", option="fund", rationale_tag="tag",
        option_tags=["tag"], evaluator=_Malformed(),
    )
    assert review.status == "unavailable"
    assert review.modifier == 1.0


def test_non_scored_review_cannot_carry_a_modifier():
    try:
        RationaleReviewV1(status="not_scored", provider="test", modifier=1.01)
    except ValueError as exc:
        assert "neutral" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("non-scored review accepted a non-neutral modifier")
