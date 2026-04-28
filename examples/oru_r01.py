#!/usr/bin/env python3
"""Build an HL7v2 ORU^R01 (Observation Result) message.

Demonstrates:
- OBX-8 abnormal flags that drive EHR clinical alerting
- NTE chunking for long clinical text (200-char Rhapsody limit)
- UCUM units in OBX-6
- OBR linking observations to the order that requested them
- Multiple OBX segments with sequential set IDs

Requires: Python 3.10+ (stdlib only)
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime


# ---------------------------------------------------------------------------
# HL7v2 Constants
# ---------------------------------------------------------------------------

ENCODING_CHARS = "^~\\&"
HL7_VERSION = "2.5.1"

LOINC_SPO2 = "59408-5"
LOINC_SPO2_TEXT = "Oxygen saturation Pulse oximetry"

# Urgency → OBX-8 abnormal flag mapping
# These flags drive clinical alerting in the receiving EHR
ABNORMAL_FLAGS: dict[str, str] = {
    "EMERGENCY": "AA",   # Critical abnormal — immediate bedside response
    "URGENT": "A",       # Abnormal — prompt clinical review
    "MONITOR": "H",      # Above high normal — increased observation frequency
    "ROUTINE": "N",      # Normal — standard monitoring
}


# ---------------------------------------------------------------------------
# Data Structures (stdlib only)
# ---------------------------------------------------------------------------

@dataclass
class VitalsObservation:
    """Observation result from a monitoring session."""

    patient_id: str
    session_id: str
    observation_time: str          # ISO format: 2026-01-15T21:00:00
    mean_spo2: float
    min_spo2: float
    desat_count: int
    sat_seconds_burden: float      # Cumulative seconds × percentage below threshold
    triage_label: str              # normal, borderline, urgent, emergency
    urgency_level: str             # ROUTINE, MONITOR, URGENT, EMERGENCY
    clinical_summary: str          # Free-text handoff summary
    sending_app: str = "CLINICAL_PIPELINE"
    sending_facility: str = "DEMO_HOSPITAL"
    receiving_app: str = "EHR_SYSTEM"
    receiving_facility: str = "DEMO_HOSPITAL"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _timestamp(iso_str: str | None = None) -> str:
    """Convert ISO datetime or now to HL7 timestamp YYYYMMDDHHmmss."""
    if iso_str:
        dt = datetime.fromisoformat(iso_str)
    else:
        dt = datetime.now()
    return dt.strftime("%Y%m%d%H%M%S")


def _message_control_id(identifier: str, msg_type: str) -> str:
    """Generate deterministic message control ID for audit traceability."""
    raw = f"{identifier}:{msg_type}"
    return hashlib.md5(raw.encode()).hexdigest()[:10].upper()


def _escape_hl7(text: str) -> str:
    r"""Escape HL7 special characters. Order matters: backslash first."""
    text = text.replace("\\", "\\E\\")
    text = text.replace("|", "\\F\\")
    text = text.replace("^", "\\S\\")
    text = text.replace("~", "\\R\\")
    text = text.replace("&", "\\T\\")
    return text


def _split_nte(text: str, max_len: int = 200) -> list[str]:
    """Split text into NTE-sized chunks at sentence boundaries.

    Rhapsody and many integration engines truncate or reject NTE-3 content
    over ~200 characters. Split at sentence boundaries to preserve readability.
    """
    sentences = text.replace("\n\n", "\n").split(". ")
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = f"{current}. {sentence}" if current else sentence
        if len(candidate) > max_len and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = candidate

    if current.strip():
        chunks.append(current.strip())

    return chunks


# ---------------------------------------------------------------------------
# ORU^R01 Builder
# ---------------------------------------------------------------------------

def build_oru_r01(obs: VitalsObservation) -> str:
    """Build an HL7v2 ORU^R01 (Observation Result) message.

    Segments: MSH, PID, OBR, OBX (×6), NTE (×N).

    OBX-8 abnormal flags are the mechanism that drives clinical alerting
    in the EHR. A flag of AA (critical abnormal) triggers immediate nurse
    station notification. A flag of N (normal) files the result silently.
    """
    now = _timestamp()
    obs_time = _timestamp(obs.observation_time)
    ctrl_id = _message_control_id(obs.session_id, "ORU")
    abnormal_flag = ABNORMAL_FLAGS.get(obs.urgency_level, "N")

    segments: list[str] = []

    # MSH — Message Header
    segments.append(
        f"MSH|{ENCODING_CHARS}|{obs.sending_app}|{obs.sending_facility}|"
        f"{obs.receiving_app}|{obs.receiving_facility}|{now}||"
        f"ORU^R01^ORU_R01|{ctrl_id}|P|{HL7_VERSION}"
    )

    # PID — Patient Identification
    pid_name = f"PATIENT^DEMO_{obs.patient_id[:4]}"
    segments.append(
        f"PID|1||{obs.patient_id}^^^{obs.sending_facility}^MR||{pid_name}||"
        f"|U"
    )

    # OBR — Observation Request (links OBX segments to the monitoring order)
    segments.append(
        f"OBR|1|{obs.session_id}||{LOINC_SPO2}^SpO2 Monitoring^LN|||"
        f"{obs_time}||||||||||||||||F"
    )

    # OBX 1 — Mean SpO2 (LOINC)
    segments.append(
        f"OBX|1|NM|{LOINC_SPO2}^{LOINC_SPO2_TEXT} Mean^LN||"
        f"{obs.mean_spo2:.1f}|%^percent^UCUM|>94|{abnormal_flag}|||F|||{obs_time}"
    )

    # OBX 2 — Min SpO2 (LOINC)
    segments.append(
        f"OBX|2|NM|{LOINC_SPO2}^{LOINC_SPO2_TEXT} Min^LN||"
        f"{obs.min_spo2:.1f}|%^percent^UCUM|>90|{abnormal_flag}|||F|||{obs_time}"
    )

    # OBX 3 — Triage Label (local code)
    segments.append(
        f"OBX|3|ST|X-TRIAGE-001^Triage Label^L||"
        f"{obs.triage_label}||||||F|||{obs_time}"
    )

    # OBX 4 — Urgency Level (local code — drives nurse station alerts)
    segments.append(
        f"OBX|4|ST|X-URGENCY-001^Urgency Level^L||"
        f"{obs.urgency_level}||||||F|||{obs_time}"
    )

    # OBX 5 — SatSeconds Burden (local code)
    segments.append(
        f"OBX|5|NM|X-SATSEC-001^SatSeconds Burden^L||"
        f"{obs.sat_seconds_burden:.0f}|s^seconds^UCUM|<100||||F|||{obs_time}"
    )

    # OBX 6 — Desaturation Event Count (local code)
    segments.append(
        f"OBX|6|NM|X-DESAT-001^Desat Event Count^L||"
        f"{obs.desat_count}|{{events}}^events^UCUM|0||||F|||{obs_time}"
    )

    # NTE — Clinical summary split into 200-char chunks
    chunks = _split_nte(_escape_hl7(obs.clinical_summary))
    for i, chunk in enumerate(chunks, start=1):
        segments.append(f"NTE|{i}|L|{chunk}|RE")

    return "\r".join(segments)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main() -> None:
    """Build and display a sample ORU^R01 message."""
    obs = VitalsObservation(
        patient_id="PAT00123",
        session_id="SESS20260115",
        observation_time="2026-01-15T21:00:00",
        mean_spo2=91.3,
        min_spo2=82.0,
        desat_count=3,
        sat_seconds_burden=245.0,
        triage_label="urgent",
        urgency_level="URGENT",
        clinical_summary=(
            "URGENT — Patient had 3 desaturation events below threshold during "
            "overnight monitoring. Minimum SpO2 reached 82%. Mean SpO2 of 91.3% "
            "is below expected baseline for gestational age. SatSeconds burden of "
            "245 seconds exceeds the 100-second threshold for clinical review. "
            "Recommend respiratory assessment and consideration of supplemental "
            "oxygen titration. Previous night showed similar pattern with 2 events."
        ),
    )

    message = build_oru_r01(obs)

    print("=" * 70)
    print("HL7v2 ORU^R01 — Observation Result")
    print("=" * 70)
    for segment in message.split("\r"):
        print(segment)
    print("=" * 70)

    # Verify structure
    segments = message.split("\r")
    seg_ids = [s.split("|")[0] for s in segments]
    assert "MSH" in seg_ids, "Missing MSH segment"
    assert "PID" in seg_ids, "Missing PID segment"
    assert "OBR" in seg_ids, "Missing OBR segment"
    assert "OBX" in seg_ids, "Missing OBX segment"
    assert "NTE" in seg_ids, "Missing NTE segment"
    assert segments[0].split("|")[8] == "ORU^R01^ORU_R01", "Wrong message type"

    # Verify abnormal flag
    obx_segments = [s for s in segments if s.startswith("OBX")]
    first_obx_fields = obx_segments[0].split("|")
    assert first_obx_fields[8] == "A", f"Expected flag A for URGENT, got {first_obx_fields[8]}"

    # Verify NTE chunking (no chunk should exceed 200 chars)
    nte_segments = [s for s in segments if s.startswith("NTE")]
    for nte in nte_segments:
        nte_text = nte.split("|")[3]
        assert len(nte_text) <= 200, f"NTE chunk exceeds 200 chars: {len(nte_text)}"

    print(f"OBX segments: {len(obx_segments)}")
    print(f"NTE segments: {len(nte_segments)}")
    print(f"Abnormal flag: {first_obx_fields[8]} (URGENT → A)")
    print("All structural checks passed.")


if __name__ == "__main__":
    main()
