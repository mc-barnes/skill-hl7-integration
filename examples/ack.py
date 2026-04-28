#!/usr/bin/env python3
"""Build HL7v2 ACK (Acknowledgment) messages.

Demonstrates:
- HL7 handshake pattern (sender/receiver swap)
- MSA-1 acknowledgment codes (AA, AE, AR)
- Referencing the original message control ID in MSA-2
- Building both positive (AA) and negative (AE) acknowledgments

Requires: Python 3.10+ (stdlib only)
"""
from __future__ import annotations

import hashlib
from datetime import datetime


# ---------------------------------------------------------------------------
# HL7v2 Constants
# ---------------------------------------------------------------------------

ENCODING_CHARS = "^~\\&"
HL7_VERSION = "2.5.1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _timestamp() -> str:
    """Current time as HL7 timestamp YYYYMMDDHHmmss."""
    return datetime.now().strftime("%Y%m%d%H%M%S")


def _message_control_id(identifier: str, msg_type: str) -> str:
    """Generate deterministic message control ID."""
    raw = f"{identifier}:{msg_type}"
    return hashlib.md5(raw.encode()).hexdigest()[:10].upper()


# ---------------------------------------------------------------------------
# ACK Builder
# ---------------------------------------------------------------------------

def build_ack(
    original_message: str,
    ack_code: str = "AA",
    error_text: str = "",
) -> str:
    """Build an HL7v2 ACK message for any inbound message.

    The HL7 handshake pattern:
    1. System A sends a message (ADT, ORU, etc.)
    2. System B receives it, processes it, sends back an ACK
    3. System A receives the ACK and marks the message as delivered

    Integration engines (Rhapsody, Mirth) won't mark a message as
    delivered until they receive an ACK. Without proper ACK handling,
    messages pile up in retry queues.

    Args:
        original_message: The full HL7 message being acknowledged.
        ack_code: MSA-1 value:
            AA = Application Accept (processed successfully)
            AE = Application Error (understood but rejected — bad data)
            AR = Application Reject (couldn't parse — structural error)
        error_text: Human-readable error description for AE/AR responses.
    """
    # Parse the original MSH to extract routing info
    msh_line = original_message.split("\r")[0]
    msh_fields = msh_line.split("|")

    # Extract original message control ID (MSH-10, index 9 after split)
    original_ctrl_id = msh_fields[9] if len(msh_fields) > 9 else "UNKNOWN"

    # Swap sender and receiver — ACK goes back to the original sender
    original_sender = msh_fields[2] if len(msh_fields) > 2 else ""
    original_send_fac = msh_fields[3] if len(msh_fields) > 3 else ""
    original_receiver = msh_fields[4] if len(msh_fields) > 4 else ""
    original_recv_fac = msh_fields[5] if len(msh_fields) > 5 else ""

    # Extract original message type for the ACK event code
    original_msg_type = msh_fields[8] if len(msh_fields) > 8 else "ACK"
    # ADT^A01^ADT_A01 → A01
    event_code = original_msg_type.split("^")[1] if "^" in original_msg_type else ""

    now = _timestamp()
    ack_ctrl_id = _message_control_id(original_ctrl_id, "ACK")

    segments: list[str] = []

    # MSH — Receiver becomes sender, sender becomes receiver
    segments.append(
        f"MSH|{ENCODING_CHARS}|{original_receiver}|{original_recv_fac}|"
        f"{original_sender}|{original_send_fac}|{now}||"
        f"ACK^{event_code}^ACK|{ack_ctrl_id}|P|{HL7_VERSION}"
    )

    # MSA — Message Acknowledgment
    # MSA-1: Acknowledgment code (AA/AE/AR)
    # MSA-2: Original message control ID (for correlation)
    # MSA-3: Error text (optional, for AE/AR)
    if error_text:
        segments.append(f"MSA|{ack_code}|{original_ctrl_id}|{error_text}")
    else:
        segments.append(f"MSA|{ack_code}|{original_ctrl_id}")

    return "\r".join(segments)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main() -> None:
    """Demonstrate ACK building for both success and error cases."""

    # Simulate an inbound ADT^A01 message
    sample_adt = (
        f"MSH|{ENCODING_CHARS}|NICU_MONITOR|HOSPITAL_A|"
        f"RHAPSODY|HOSPITAL_A|20260115210000||ADT^A01^ADT_A01|"
        f"CTRL123456|P|{HL7_VERSION}\r"
        f"EVN|A01|20260115210000\r"
        f"PID|1||PAT001^^^HOSPITAL_A^MR||DOE^JANE||20260110|F"
    )

    # --- Positive ACK (AA) ---
    ack_success = build_ack(sample_adt, ack_code="AA")

    print("=" * 70)
    print("ACK — Application Accept (AA)")
    print("=" * 70)
    for segment in ack_success.split("\r"):
        print(segment)

    # Verify sender/receiver swap
    ack_msh = ack_success.split("\r")[0].split("|")
    assert ack_msh[2] == "RHAPSODY", "Receiver should become sender"
    assert ack_msh[4] == "NICU_MONITOR", "Sender should become receiver"

    # Verify MSA references original control ID
    msa = ack_success.split("\r")[1].split("|")
    assert msa[1] == "AA", f"Expected AA, got {msa[1]}"
    assert msa[2] == "CTRL123456", f"Expected original ctrl ID, got {msa[2]}"
    print("Sender/receiver swap: correct")
    print(f"MSA-1: {msa[1]} (Application Accept)")
    print(f"MSA-2: {msa[2]} (references original message)")

    # --- Negative ACK (AE) ---
    ack_error = build_ack(
        sample_adt,
        ack_code="AE",
        error_text="PID-3 missing required patient identifier",
    )

    print()
    print("=" * 70)
    print("ACK — Application Error (AE)")
    print("=" * 70)
    for segment in ack_error.split("\r"):
        print(segment)

    msa_err = ack_error.split("\r")[1].split("|")
    assert msa_err[1] == "AE", f"Expected AE, got {msa_err[1]}"
    print(f"MSA-1: {msa_err[1]} (Application Error)")
    print(f"MSA-3: {msa_err[3]} (error description)")

    # --- Reject ACK (AR) ---
    ack_reject = build_ack(
        sample_adt,
        ack_code="AR",
        error_text="MSH-9 message type not recognized",
    )

    print()
    print("=" * 70)
    print("ACK — Application Reject (AR)")
    print("=" * 70)
    for segment in ack_reject.split("\r"):
        print(segment)

    msa_rej = ack_reject.split("\r")[1].split("|")
    assert msa_rej[1] == "AR", f"Expected AR, got {msa_rej[1]}"
    print(f"MSA-1: {msa_rej[1]} (Application Reject)")
    print()
    print("All structural checks passed.")


if __name__ == "__main__":
    main()
