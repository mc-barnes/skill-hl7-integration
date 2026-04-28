#!/usr/bin/env python3
"""Build an HL7v2 ADT^A01 (Patient Admission) message.

Demonstrates:
- MSH-1 encoding quirk (field separator IS the first field)
- PID with medical record number identifier
- OBX with LOINC codes and UCUM units
- DG1 with ICD-10 diagnosis codes
- Correct segment terminator (\\r, not \\n)

Requires: Python 3.10+ (stdlib only)
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# HL7v2 Constants
# ---------------------------------------------------------------------------

FIELD_SEP = "|"
ENCODING_CHARS = "^~\\&"
HL7_VERSION = "2.5.1"

# LOINC code for SpO2 (pulse oximetry)
LOINC_SPO2 = "59408-5"
LOINC_SPO2_TEXT = "Oxygen saturation Pulse oximetry"

# ICD-10-CM codes for common neonatal conditions
ICD10_MAP: dict[str, tuple[str, str]] = {
    "apnea_of_prematurity": ("P28.4", "Primary apnea of newborn"),
    "bpd": ("P27.1", "Bronchopulmonary dysplasia"),
    "anemia": ("P61.2", "Anemia of prematurity"),
    "rop": ("H35.10", "Retinopathy of prematurity, unspecified"),
    "nec": ("P77.9", "Necrotizing enterocolitis, unspecified"),
}


# ---------------------------------------------------------------------------
# Patient Data (simple dataclass — no project-specific dependencies)
# ---------------------------------------------------------------------------

@dataclass
class Patient:
    """Minimal patient representation for HL7 message building."""

    patient_id: str
    gestational_age_weeks: int
    birth_weight_grams: int
    days_since_birth: int
    spo2_baseline: float
    known_conditions: list[str] = field(default_factory=list)
    sending_app: str = "NICU_SPO2_MONITOR"
    sending_facility: str = "DEMO_HOSPITAL"
    receiving_app: str = "RHAPSODY_ENGINE"
    receiving_facility: str = "DEMO_HOSPITAL"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _timestamp(dt: datetime | None = None) -> str:
    """Format datetime as HL7 timestamp: YYYYMMDDHHmmss."""
    return (dt or datetime.now()).strftime("%Y%m%d%H%M%S")


def _message_control_id(identifier: str, msg_type: str) -> str:
    """Generate a deterministic message control ID for audit traceability."""
    raw = f"{identifier}:{msg_type}"
    return hashlib.md5(raw.encode()).hexdigest()[:10].upper()


def _escape_hl7(text: str) -> str:
    r"""Escape HL7 special characters in free text.

    Escape sequences: \F\ for |, \S\ for ^, \R\ for ~, \E\ for \, \T\ for &.
    Order matters: escape backslash first to avoid double-escaping.
    """
    text = text.replace("\\", "\\E\\")
    text = text.replace("|", "\\F\\")
    text = text.replace("^", "\\S\\")
    text = text.replace("~", "\\R\\")
    text = text.replace("&", "\\T\\")
    return text


# ---------------------------------------------------------------------------
# ADT^A01 Builder
# ---------------------------------------------------------------------------

def build_adt_a01(patient: Patient) -> str:
    """Build an HL7v2 ADT^A01 (Patient Admission) message.

    Segments: MSH, EVN, PID, PV1, OBX (baseline vitals), DG1 (diagnoses).

    The MSH segment has a unique quirk: MSH-1 is the field separator character
    itself (|), so when you split on |, the field indexes are offset by one
    compared to every other segment. This trips up every first-time HL7
    implementer.
    """
    now = _timestamp()
    ctrl_id = _message_control_id(patient.patient_id, "ADT")
    dob = _timestamp(datetime.now() - timedelta(days=patient.days_since_birth))[:8]

    segments: list[str] = []

    # MSH — Message Header
    # MSH-1 is |, MSH-2 is ^~\&. After split("|"):
    #   [0]=MSH [1]=^~\& [2]=sending_app ... [8]=msg_type [9]=ctrl_id
    segments.append(
        f"MSH|{ENCODING_CHARS}|{patient.sending_app}|{patient.sending_facility}|"
        f"{patient.receiving_app}|{patient.receiving_facility}|{now}||"
        f"ADT^A01^ADT_A01|{ctrl_id}|P|{HL7_VERSION}"
    )

    # EVN — Event Type
    segments.append(f"EVN|A01|{now}")

    # PID — Patient Identification
    # PID-3: ID^^^Facility^MR (MR = Medical Record Number)
    # PID-7: Date of birth (YYYYMMDD)
    # PID-8: Sex (U = Unknown — common for neonatal)
    pid_name = f"BABY^DEMO_{patient.patient_id[:4]}"
    segments.append(
        f"PID|1||{patient.patient_id}^^^{patient.sending_facility}^MR||"
        f"{pid_name}||{dob}|U"
    )

    # PV1 — Patient Visit (Inpatient, NICU)
    segments.append(
        f"PV1|1|I|NICU^BED01^^{patient.sending_facility}||||"
        f"||||||||||||||||||||||||||||||||{now}"
    )

    # OBX — Baseline SpO2 (LOINC 59408-5)
    segments.append(
        f"OBX|1|NM|{LOINC_SPO2}^{LOINC_SPO2_TEXT}^LN||"
        f"{patient.spo2_baseline:.1f}|%^percent^UCUM||||||F"
    )

    # OBX — Gestational Age (local code, X-prefix)
    segments.append(
        f"OBX|2|NM|X-GA-WEEKS^Gestational Age^L||"
        f"{patient.gestational_age_weeks}|wk^weeks^UCUM||||||F"
    )

    # OBX — Birth Weight (local code, X-prefix)
    segments.append(
        f"OBX|3|NM|X-BIRTH-WT^Birth Weight^L||"
        f"{patient.birth_weight_grams}|g^grams^UCUM||||||F"
    )

    # DG1 — Diagnosis codes (ICD-10) for known conditions
    dg_set = 1
    for condition in patient.known_conditions:
        if condition in ICD10_MAP:
            code, desc = ICD10_MAP[condition]
            segments.append(
                f"DG1|{dg_set}||{code}^{_escape_hl7(desc)}^I10||{now}|A"
            )
            dg_set += 1

    # HL7 messages use \r (carriage return) as segment terminator — NOT \n
    return "\r".join(segments)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main() -> None:
    """Build and display a sample ADT^A01 message."""
    patient = Patient(
        patient_id="PAT00123",
        gestational_age_weeks=30,
        birth_weight_grams=1450,
        days_since_birth=14,
        spo2_baseline=93.5,
        known_conditions=["apnea_of_prematurity", "anemia"],
    )

    message = build_adt_a01(patient)

    print("=" * 70)
    print("HL7v2 ADT^A01 — Patient Admission")
    print("=" * 70)
    # Display with \n for readability, but the actual message uses \r
    for segment in message.split("\r"):
        print(segment)
    print("=" * 70)
    print(f"Segments: {len(message.split(chr(13)))}")
    print(f"Message Control ID: {_message_control_id(patient.patient_id, 'ADT')}")

    # Verify structure
    segments = message.split("\r")
    seg_ids = [s.split("|")[0] for s in segments]
    assert "MSH" in seg_ids, "Missing MSH segment"
    assert "EVN" in seg_ids, "Missing EVN segment"
    assert "PID" in seg_ids, "Missing PID segment"
    assert "PV1" in seg_ids, "Missing PV1 segment"
    assert "OBX" in seg_ids, "Missing OBX segment"
    assert "DG1" in seg_ids, "Missing DG1 segment"
    assert segments[0].startswith("MSH|^~\\&|"), "MSH encoding incorrect"
    print("All structural checks passed.")


if __name__ == "__main__":
    main()
