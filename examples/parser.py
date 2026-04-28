#!/usr/bin/env python3
"""Parse and validate HL7v2 messages.

Demonstrates:
- Generic segment parser (split on \\r, then |, then ^)
- Field extraction by segment type + position
- HL7 special character unescaping
- Structural validation checks
- Encoding character detection from MSH-2

Requires: Python 3.10+ (stdlib only)
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Parsed Message Structure
# ---------------------------------------------------------------------------

@dataclass
class ParsedSegment:
    """A single parsed HL7 segment."""

    segment_id: str
    fields: list[str]

    def get_field(self, index: int) -> str:
        """Get field by 1-based HL7 position. Returns empty string if missing."""
        if self.segment_id == "MSH":
            # MSH-1 is the field separator itself, so indexes are offset
            actual = index - 1
        else:
            actual = index
        if 0 <= actual < len(self.fields):
            return self.fields[actual]
        return ""

    def get_component(self, field_index: int, component_index: int = 1) -> str:
        """Get a component within a field (1-based). Components are ^-separated."""
        field_value = self.get_field(field_index)
        components = field_value.split("^")
        idx = component_index - 1
        if 0 <= idx < len(components):
            return components[idx]
        return ""


@dataclass
class ParsedMessage:
    """A fully parsed HL7v2 message."""

    segments: list[ParsedSegment] = field(default_factory=list)
    raw: str = ""

    def get_segments(self, segment_id: str) -> list[ParsedSegment]:
        """Get all segments of a given type (e.g., 'OBX')."""
        return [s for s in self.segments if s.segment_id == segment_id]

    def get_segment(self, segment_id: str) -> ParsedSegment | None:
        """Get the first segment of a given type, or None."""
        matches = self.get_segments(segment_id)
        return matches[0] if matches else None

    @property
    def message_type(self) -> str:
        """Extract message type from MSH-9 (e.g., 'ADT^A01^ADT_A01')."""
        msh = self.get_segment("MSH")
        return msh.get_field(9) if msh else ""

    @property
    def message_control_id(self) -> str:
        """Extract message control ID from MSH-10."""
        msh = self.get_segment("MSH")
        return msh.get_field(10) if msh else ""

    @property
    def version(self) -> str:
        """Extract HL7 version from MSH-12."""
        msh = self.get_segment("MSH")
        return msh.get_field(12) if msh else ""


# ---------------------------------------------------------------------------
# Escape / Unescape
# ---------------------------------------------------------------------------

def unescape_hl7(text: str) -> str:
    r"""Unescape HL7 special characters in field values.

    Reverses: \F\ → |, \S\ → ^, \R\ → ~, \T\ → &, \E\ → \
    Order matters: unescape \E\ last to avoid double-processing.
    """
    text = text.replace("\\F\\", "|")
    text = text.replace("\\S\\", "^")
    text = text.replace("\\R\\", "~")
    text = text.replace("\\T\\", "&")
    text = text.replace("\\E\\", "\\")
    return text


def escape_hl7(text: str) -> str:
    r"""Escape HL7 special characters for embedding in fields.

    Order matters: escape backslash FIRST to avoid double-escaping.
    """
    text = text.replace("\\", "\\E\\")
    text = text.replace("|", "\\F\\")
    text = text.replace("^", "\\S\\")
    text = text.replace("~", "\\R\\")
    text = text.replace("&", "\\T\\")
    return text


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_message(raw: str) -> ParsedMessage:
    """Parse a raw HL7v2 message into structured segments.

    HL7 messages are:
    - Segments separated by \\r (carriage return)
    - Fields within segments separated by | (pipe)
    - Components within fields separated by ^ (caret)

    The MSH segment is special: MSH-1 IS the field separator character,
    so after splitting on |, index 0 = "MSH" and index 1 = encoding chars.
    """
    # Normalize line endings — accept both \r and \n for parsing flexibility
    # (but always BUILD with \r)
    if "\r" in raw:
        lines = raw.split("\r")
    else:
        lines = raw.split("\n")

    # Filter empty lines
    lines = [line.strip() for line in lines if line.strip()]

    msg = ParsedMessage(raw=raw)

    for line in lines:
        fields = line.split("|")
        segment_id = fields[0]
        msg.segments.append(ParsedSegment(segment_id=segment_id, fields=fields))

    return msg


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Result of validating an HL7 message."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_message(msg: ParsedMessage) -> ValidationResult:
    """Run structural validation checks on a parsed HL7 message.

    Checks:
    1. MSH segment present and first
    2. MSH-2 encoding characters present
    3. MSH-9 message type present
    4. MSH-10 message control ID present
    5. MSH-12 version present
    6. OBX-2 data type matches OBX-5 format (NM must be numeric)
    7. Message-type-specific required segments
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Check MSH is present and first
    if not msg.segments:
        return ValidationResult(valid=False, errors=["Empty message"])

    if msg.segments[0].segment_id != "MSH":
        errors.append("First segment must be MSH")

    msh = msg.get_segment("MSH")
    if not msh:
        return ValidationResult(valid=False, errors=["Missing MSH segment"])

    # Check required MSH fields
    encoding = msh.get_field(2)
    if not encoding:
        errors.append("MSH-2 (encoding characters) is empty")
    elif encoding != "^~\\&":
        warnings.append(f"Non-standard encoding characters: {encoding}")

    if not msh.get_field(9):
        errors.append("MSH-9 (message type) is empty")

    if not msh.get_field(10):
        warnings.append("MSH-10 (message control ID) is empty — required for ACK correlation")

    if not msh.get_field(12):
        warnings.append("MSH-12 (version) is empty")

    # Message-type-specific segment requirements
    msg_type = msh.get_component(9, 1)  # e.g., "ADT" from "ADT^A01^ADT_A01"
    required_segments: dict[str, list[str]] = {
        "ADT": ["PID", "PV1"],
        "ORU": ["PID", "OBR", "OBX"],
        "ACK": ["MSA"],
    }

    if msg_type in required_segments:
        present = {s.segment_id for s in msg.segments}
        for req in required_segments[msg_type]:
            if req not in present:
                errors.append(f"{msg_type} message missing required segment: {req}")

    # Validate OBX segments
    for obx in msg.get_segments("OBX"):
        value_type = obx.get_field(2)  # OBX-2: NM, ST, TX, CWE, etc.
        value = obx.get_field(5)       # OBX-5: the actual value

        if value_type == "NM" and value:
            try:
                float(value)
            except ValueError:
                errors.append(
                    f"OBX-2=NM but OBX-5 is not numeric: '{value}' "
                    f"(OBX-3: {obx.get_field(3)})"
                )

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Convenience Extractors
# ---------------------------------------------------------------------------

def extract_patient_id(msg: ParsedMessage) -> str:
    """Extract primary patient ID from PID-3, component 1."""
    pid = msg.get_segment("PID")
    if pid:
        return pid.get_component(3, 1)
    return ""


def extract_observations(msg: ParsedMessage) -> list[dict[str, str]]:
    """Extract all OBX observations as dicts with code, value, units, flag."""
    results = []
    for obx in msg.get_segments("OBX"):
        results.append({
            "set_id": obx.get_field(1),
            "value_type": obx.get_field(2),
            "code": obx.get_component(3, 1),
            "code_text": obx.get_component(3, 2),
            "code_system": obx.get_component(3, 3),
            "value": obx.get_field(5),
            "units": obx.get_component(6, 1),
            "reference_range": obx.get_field(7),
            "abnormal_flag": obx.get_field(8),
            "status": obx.get_field(11),
        })
    return results


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse and validate a sample HL7 message."""
    # Sample ADT^A01 message
    sample = (
        "MSH|^~\\&|NICU_MONITOR|HOSPITAL|RHAPSODY|HOSPITAL|20260115210000||"
        "ADT^A01^ADT_A01|CTRL001|P|2.5.1\r"
        "EVN|A01|20260115210000\r"
        "PID|1||PAT001^^^HOSPITAL^MR||DOE^BABY^J||20260110|U\r"
        "PV1|1|I|NICU^BED01^^HOSPITAL\r"
        "OBX|1|NM|59408-5^Oxygen saturation Pulse oximetry^LN||93.5|"
        "%^percent^UCUM||||||F\r"
        "OBX|2|NM|X-GA-WEEKS^Gestational Age^L||30|wk^weeks^UCUM||||||F\r"
        "DG1|1||P28.4^Primary apnea of newborn^I10||20260115210000|A"
    )

    print("=" * 70)
    print("HL7v2 Parser Demo")
    print("=" * 70)

    # Parse
    msg = parse_message(sample)
    print(f"Message type: {msg.message_type}")
    print(f"Control ID:   {msg.message_control_id}")
    print(f"Version:      {msg.version}")
    print(f"Patient ID:   {extract_patient_id(msg)}")
    print(f"Segments:     {[s.segment_id for s in msg.segments]}")

    # Validate
    result = validate_message(msg)
    print(f"\nValidation: {'PASS' if result.valid else 'FAIL'}")
    for err in result.errors:
        print(f"  ERROR: {err}")
    for warn in result.warnings:
        print(f"  WARN:  {warn}")

    # Extract observations
    obs = extract_observations(msg)
    print(f"\nObservations ({len(obs)}):")
    for o in obs:
        print(f"  [{o['set_id']}] {o['code']} ({o['code_text']}): "
              f"{o['value']} {o['units']} flag={o['abnormal_flag'] or 'N/A'}")

    # Test escape/unescape round-trip
    original = "SpO2 | test ^ value ~ repeat & join"
    escaped = escape_hl7(original)
    unescaped = unescape_hl7(escaped)
    assert unescaped == original, f"Round-trip failed: {unescaped!r} != {original!r}"
    print(f"\nEscape round-trip: '{original}'")
    print(f"  Escaped:   '{escaped}'")
    print(f"  Unescaped: '{unescaped}'")

    assert result.valid, "Validation should pass"
    assert extract_patient_id(msg) == "PAT001"
    assert len(obs) == 2
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
