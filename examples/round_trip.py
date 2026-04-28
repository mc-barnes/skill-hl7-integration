#!/usr/bin/env python3
"""Full round-trip: build HL7 message → parse → validate fields match.

Demonstrates:
- Build an ADT^A01 from patient data
- Parse it back into structured data
- Assert every field survives the round-trip
- Build an ACK for the ADT
- Parse and validate the ACK references the original message

This is the correctness proof: if build → parse → compare passes, the
messages are structurally valid HL7, not just string templates.

Requires: Python 3.10+ (stdlib only)
"""
from __future__ import annotations

# Import from sibling examples
from adt_a01 import Patient, build_adt_a01, ICD10_MAP
from ack import build_ack
from parser import parse_message, validate_message, extract_patient_id, extract_observations


def test_adt_round_trip() -> None:
    """Build ADT^A01 → parse → verify all patient fields survive."""
    patient = Patient(
        patient_id="ROUND001",
        gestational_age_weeks=28,
        birth_weight_grams=1100,
        days_since_birth=21,
        spo2_baseline=92.0,
        known_conditions=["apnea_of_prematurity", "bpd", "rop"],
    )

    # Build
    adt_message = build_adt_a01(patient)

    # Parse
    parsed = parse_message(adt_message)
    result = validate_message(parsed)

    # Validate structure
    assert result.valid, f"Validation failed: {result.errors}"
    assert parsed.message_type == "ADT^A01^ADT_A01"
    assert parsed.version == "2.5.1"

    # Verify patient ID round-trip
    assert extract_patient_id(parsed) == patient.patient_id

    # Verify observations round-trip
    obs = extract_observations(parsed)
    obs_by_code: dict[str, dict[str, str]] = {o["code"]: o for o in obs}

    # SpO2 baseline (LOINC 59408-5)
    assert "59408-5" in obs_by_code, "Missing SpO2 observation"
    spo2_obs = obs_by_code["59408-5"]
    assert abs(float(spo2_obs["value"]) - patient.spo2_baseline) < 0.1, (
        f"SpO2 mismatch: {spo2_obs['value']} vs {patient.spo2_baseline}"
    )

    # Gestational age (local code)
    assert "X-GA-WEEKS" in obs_by_code, "Missing GA observation"
    assert int(obs_by_code["X-GA-WEEKS"]["value"]) == patient.gestational_age_weeks

    # Birth weight (local code)
    assert "X-BIRTH-WT" in obs_by_code, "Missing birth weight observation"
    assert int(obs_by_code["X-BIRTH-WT"]["value"]) == patient.birth_weight_grams

    # Verify DG1 segments have correct ICD-10 codes
    dg1_segments = parsed.get_segments("DG1")
    parsed_codes = {seg.get_field(3).split("^")[0] for seg in dg1_segments}
    expected_codes = {ICD10_MAP[c][0] for c in patient.known_conditions if c in ICD10_MAP}
    assert parsed_codes == expected_codes, (
        f"ICD-10 mismatch: got {parsed_codes}, expected {expected_codes}"
    )

    print("ADT round-trip: PASS")
    print(f"  Patient ID:  {extract_patient_id(parsed)} == {patient.patient_id}")
    print(f"  SpO2:        {spo2_obs['value']} == {patient.spo2_baseline}")
    print(f"  GA weeks:    {obs_by_code['X-GA-WEEKS']['value']} == {patient.gestational_age_weeks}")
    print(f"  Birth wt:    {obs_by_code['X-BIRTH-WT']['value']} == {patient.birth_weight_grams}")
    print(f"  ICD-10:      {parsed_codes} == {expected_codes}")
    print(f"  Conditions:  {len(dg1_segments)} DG1 segments for {len(patient.known_conditions)} conditions")


def test_ack_round_trip() -> None:
    """Build ADT → ACK → parse → verify ACK references original."""
    patient = Patient(
        patient_id="ROUND002",
        gestational_age_weeks=34,
        birth_weight_grams=2100,
        days_since_birth=7,
        spo2_baseline=95.5,
    )

    # Build ADT, then ACK
    adt_message = build_adt_a01(patient)
    ack_message = build_ack(adt_message, ack_code="AA")

    # Parse both
    parsed_adt = parse_message(adt_message)
    parsed_ack = parse_message(ack_message)

    # Validate ACK structure
    ack_result = validate_message(parsed_ack)
    assert ack_result.valid, f"ACK validation failed: {ack_result.errors}"

    # Verify sender/receiver swap
    adt_msh = parsed_adt.get_segment("MSH")
    ack_msh = parsed_ack.get_segment("MSH")
    assert adt_msh and ack_msh

    assert ack_msh.get_field(3) == adt_msh.get_field(5), "ACK sender should be ADT receiver"
    assert ack_msh.get_field(5) == adt_msh.get_field(3), "ACK receiver should be ADT sender"

    # Verify MSA references original control ID
    msa = parsed_ack.get_segment("MSA")
    assert msa is not None, "ACK missing MSA segment"
    assert msa.get_field(1) == "AA", f"Expected AA, got {msa.get_field(1)}"
    assert msa.get_field(2) == parsed_adt.message_control_id, (
        f"MSA-2 should reference original control ID: "
        f"{msa.get_field(2)} != {parsed_adt.message_control_id}"
    )

    print("\nACK round-trip: PASS")
    print(f"  ADT sender:    {adt_msh.get_field(3)}")
    print(f"  ACK sender:    {ack_msh.get_field(3)} (swapped)")
    print(f"  MSA-1:         {msa.get_field(1)} (Application Accept)")
    print(f"  MSA-2:         {msa.get_field(2)} (matches ADT control ID)")


def test_error_ack() -> None:
    """Build an error ACK (AE) and verify error text survives."""
    patient = Patient(
        patient_id="ROUND003",
        gestational_age_weeks=38,
        birth_weight_grams=3200,
        days_since_birth=2,
        spo2_baseline=98.0,
    )

    adt_message = build_adt_a01(patient)
    error_ack = build_ack(
        adt_message,
        ack_code="AE",
        error_text="PID-3 identifier type not recognized",
    )

    parsed = parse_message(error_ack)
    msa = parsed.get_segment("MSA")
    assert msa is not None
    assert msa.get_field(1) == "AE"
    assert "PID-3" in msa.get_field(3)

    print("\nError ACK: PASS")
    print(f"  MSA-1: {msa.get_field(1)} (Application Error)")
    print(f"  MSA-3: {msa.get_field(3)}")


def main() -> None:
    """Run all round-trip tests."""
    print("=" * 70)
    print("HL7v2 Round-Trip Validation")
    print("=" * 70)

    test_adt_round_trip()
    test_ack_round_trip()
    test_error_ack()

    print()
    print("=" * 70)
    print("All round-trip tests passed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
