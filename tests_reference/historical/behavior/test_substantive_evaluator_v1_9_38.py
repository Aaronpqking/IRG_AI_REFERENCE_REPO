from copy import deepcopy

import pytest

from src.docling_structural.substantive_evaluator_v1_9_38 import (
    ABSENT,
    CONTROL_DIAGNOSTIC_FIELDS,
    DIMENSIONS,
    FAIL,
    NOT_APPLICABLE,
    PASS,
    PRESENT,
    UNRESOLVED_DISCRIMINATOR,
    aggregate_scores,
    apply_qualification_gates,
    contract_manifest,
    denominator_contract,
    qualification_threshold_contract,
    score_case,
)


def fact(
    fact_id: str,
    *,
    evidence_ids: tuple[str, ...] = ("evidence:1",),
    identifiers: tuple[str, ...] = ("MODEL-1",),
    values: tuple[str, ...] = ("4",),
    units: tuple[str, ...] = ("inches",),
) -> dict:
    return {
        "fact_id": fact_id,
        "identifiers": list(identifiers),
        "values": list(values),
        "units": list(units),
        "allowed_evidence_ids": list(evidence_ids),
    }


def authority(
    case_id: str,
    *,
    facts: tuple[dict, ...] = (),
    state: str = PRESENT,
    adjacent: tuple[dict, ...] = (),
    discriminator: str | None = None,
) -> dict:
    return {
        "case_id": case_id,
        "question": f"Question for {case_id}?",
        "requested_fact_state": state,
        "required_facts": list(facts),
        "allowed_adjacent_facts": list(adjacent),
        "required_discriminator": discriminator,
    }


def binding(evidence_id: str = "evidence:1", status: str = "SUPPORTED") -> dict:
    return {
        "binding_id": "binding:1",
        "status": status,
        "source_identity": {"evidence_id": evidence_id},
    }


def claim(
    fact_id: str,
    *,
    evidence_status: str = "SUPPORTED",
    factual_status: str = "CORRECT",
    identifier_fidelity: str = PASS,
    value_fidelity: str = PASS,
    unit_fidelity: str = PASS,
    bindings: tuple[dict, ...] = (None,),
) -> dict:
    resolved_bindings = (
        [binding()] if bindings == (None,) else list(bindings)
    )
    return {
        "claim_id": f"claim:{fact_id}",
        "claim_type": "FACTUAL",
        "fact_id": fact_id,
        "factual_status": factual_status,
        "evidence_status": evidence_status,
        "scope_status": PASS,
        "identifier_fidelity": identifier_fidelity,
        "value_fidelity": value_fidelity,
        "unit_fidelity": unit_fidelity,
        "citation_required": True,
        "citation_bindings": resolved_bindings,
    }


def observation(case_id: str, claims: tuple[dict, ...] = (), **overrides) -> dict:
    payload = {
        "case_id": case_id,
        "answer_text": "Fixture answer.",
        "claims": list(claims),
        "user_actionability": PASS,
    }
    payload.update(overrides)
    return payload


def test_contract_has_exact_independent_substantive_dimensions():
    manifest = contract_manifest()

    assert tuple(manifest["dimensions"]) == DIMENSIONS
    assert manifest["control_fields_consumed_by_primary_score"] == []
    assert set(manifest["control_diagnostic_fields"]) == set(
        CONTROL_DIAGNOSTIC_FIELDS
    )


def test_single_answer_fixture_passes_without_control_stack_dependency():
    auth = authority("single", facts=(fact("f1"),))
    baseline = score_case(auth, observation("single", (claim("f1"),)))
    with_controls = observation("single", (claim("f1"),))
    for index, field in enumerate(CONTROL_DIAGNOSTIC_FIELDS):
        with_controls[field] = f"arbitrary-{index}"
    controlled = score_case(auth, with_controls)

    assert baseline.primary_substantive_pass is True
    assert controlled.primary_substantive_pass is True
    assert baseline.dimensions == controlled.dimensions
    assert controlled.response_policy_diagnostics[
        "excluded_from_primary_score"
    ] is True


def test_multi_evidence_fixture_passes():
    source_ids = ("evidence:a", "evidence:b")
    auth = authority(
        "multi-evidence",
        facts=(fact("f1", evidence_ids=source_ids),),
    )
    observed_claim = claim(
        "f1",
        bindings=(binding(source_ids[0]), binding(source_ids[1])),
    )

    result = score_case(auth, observation("multi-evidence", (observed_claim,)))

    assert result.primary_substantive_pass is True
    assert result.dimensions["CITATION_ENTAILMENT"].denominator == 2


def test_explicitly_enumerated_variants_fixture_passes():
    first = fact("variant-a", evidence_ids=("evidence:a",), values=("4",))
    second = fact("variant-b", evidence_ids=("evidence:b",), values=("6",))
    auth = authority("variants", facts=(first, second))
    a = claim("variant-a", bindings=(binding("evidence:a"),))
    b = claim("variant-b", bindings=(binding("evidence:b"),))

    result = score_case(auth, observation("variants", (a, b)))

    assert result.primary_substantive_pass is True
    assert result.dimensions["ANSWER_COVERAGE"].numerator == 2


def test_true_clarification_required_fixture_passes():
    auth = authority(
        "clarification",
        state=UNRESOLVED_DISCRIMINATOR,
        discriminator="fuel_type",
    )
    observed = observation(
        "clarification",
        asked_necessary_clarification=True,
        clarification_discriminator="fuel_type",
    )

    result = score_case(auth, observed)

    assert result.primary_substantive_pass is True
    assert result.dimensions["ANSWER_COVERAGE"].status == PASS
    assert result.dimensions["FACTUAL_CORRECTNESS"].status == NOT_APPLICABLE


def test_absent_requested_fact_with_supported_adjacent_fact_passes():
    adjacent = fact(
        "adjacent",
        evidence_ids=("evidence:adjacent",),
        identifiers=(),
        values=(),
        units=(),
    )
    auth = authority(
        "absent",
        state=ABSENT,
        adjacent=(adjacent,),
    )
    adjacent_claim = claim(
        "adjacent",
        bindings=(binding("evidence:adjacent"),),
    )

    result = score_case(
        auth,
        observation(
            "absent",
            (adjacent_claim,),
            supported_absence_statement=True,
        ),
    )

    assert result.primary_substantive_pass is True
    assert result.dimensions["ANSWER_COVERAGE"].status == PASS


def test_shared_provenance_value_fixture_passes():
    sources = ("evidence:owner-a", "evidence:owner-b")
    shared = fact("shared", evidence_ids=sources)
    shared_claim = claim(
        "shared",
        bindings=(binding(sources[0]), binding(sources[1])),
    )

    result = score_case(
        authority("shared", facts=(shared,)),
        observation("shared", (shared_claim,)),
    )

    assert result.primary_substantive_pass is True
    assert result.dimensions["CITATION_MISBINDING"].status == PASS


def test_unsupported_answer_fixture_fails_substantively():
    bad = claim(
        "invented",
        evidence_status="UNSUPPORTED",
        factual_status="INCORRECT",
    )

    result = score_case(
        authority("unsupported", facts=(fact("required"),)),
        observation("unsupported", (bad,)),
    )

    assert result.primary_substantive_pass is False
    assert result.dimensions["FACTUAL_CORRECTNESS"].status == FAIL
    assert result.dimensions["UNSUPPORTED_CLAIMS"].status == FAIL


def test_wrong_identifier_fixture_fails_identifier_fidelity():
    wrong = claim("f1", identifier_fidelity=FAIL)

    result = score_case(
        authority("wrong-id", facts=(fact("f1"),)),
        observation("wrong-id", (wrong,)),
    )

    assert result.primary_substantive_pass is False
    assert result.dimensions["IDENTIFIER_FIDELITY"].status == FAIL
    assert result.dimensions["VALUE_FIDELITY"].status == PASS


def test_citation_misbinding_fixture_fails_only_binding_relation():
    misbound = claim(
        "f1",
        bindings=(binding("evidence:wrong"),),
    )

    result = score_case(
        authority("misbound", facts=(fact("f1"),)),
        observation("misbound", (misbound,)),
    )

    assert result.primary_substantive_pass is False
    assert result.dimensions["CITATION_MISBINDING"].status == FAIL
    assert result.dimensions["CITATION_ENTAILMENT"].status == PASS


def test_citation_missing_fixture_fails_completeness():
    missing = claim("f1", bindings=())

    result = score_case(
        authority("citation-missing", facts=(fact("f1"),)),
        observation("citation-missing", (missing,)),
    )

    assert result.primary_substantive_pass is False
    assert result.dimensions["CITATION_COMPLETENESS"].status == FAIL
    assert result.dimensions["CITATION_BINDING_VALIDITY"].status == (
        NOT_APPLICABLE
    )


def test_validator_uncertainty_fixture_is_not_an_unsupported_claim():
    uncertain = claim(
        "f1",
        evidence_status="VALIDATOR_UNCERTAIN",
        bindings=(binding(status="VALIDATOR_UNCERTAIN"),),
    )

    result = score_case(
        authority("uncertain", facts=(fact("f1"),)),
        observation("uncertain", (uncertain,)),
    )

    assert result.primary_substantive_pass is False
    assert result.dimensions["EVIDENCE_SUPPORT"].status == FAIL
    assert result.dimensions["UNSUPPORTED_CLAIMS"].status == PASS
    assert result.dimensions["CITATION_BINDING_VALIDITY"].status == PASS
    assert result.dimensions["CITATION_ENTAILMENT"].status == FAIL


def test_aggregate_and_denominator_contracts_are_dimension_specific():
    first_authority = authority("one", facts=(fact("f1"),))
    second_authority = authority("two", state=ABSENT)
    scores = [
        score_case(first_authority, observation("one", (claim("f1"),))),
        score_case(
            second_authority,
            observation("two", supported_absence_statement=True),
        ),
    ]

    aggregate = aggregate_scores(scores)
    denominators = denominator_contract(
        [first_authority, second_authority]
    )

    assert aggregate["primary_substantive_score"] == 1.0
    assert aggregate["dimensions"]["IDENTIFIER_FIDELITY"] == {
        "passed_cases": 1,
        "applicable_cases": 1,
        "rate": 1.0,
    }
    assert denominators["total_cases"] == 2
    assert denominators["cases_by_requested_fact_state"] == {
        PRESENT: 1,
        ABSENT: 1,
        UNRESOLVED_DISCRIMINATOR: 0,
    }


def test_contract_rejects_invalid_authority_and_observation_states():
    with pytest.raises(ValueError, match="PRESENT authority requires facts"):
        score_case(
            authority("invalid"),
            observation("invalid"),
        )

    invalid_claim = deepcopy(claim("f1"))
    invalid_claim["evidence_status"] = "MAYBE"
    with pytest.raises(ValueError, match="evidence status"):
        score_case(
            authority("invalid-claim", facts=(fact("f1"),)),
            observation("invalid-claim", (invalid_claim,)),
        )


def test_qualification_thresholds_are_complete_and_fail_closed():
    contract = qualification_threshold_contract()
    passing = {
        **{
            name: threshold
            for name, threshold in contract["minimums"].items()
        },
        **{
            name: threshold
            for name, threshold in contract["maximums"].items()
        },
    }

    assert apply_qualification_gates(passing)["status"] == PASS
    below = dict(passing)
    below["primary_substantive_score"] = 0.949
    failed = apply_qualification_gates(below)
    assert failed["status"] == FAIL
    assert failed["failed_gates"] == ["primary_substantive_score"]
    del below["citation_entailment"]
    missing = apply_qualification_gates(below)
    assert "citation_entailment" in missing["failed_gates"]
    assert contract_manifest()["qualification_thresholds"] == contract
