---
name: hl7v2-integration
description: >
  Build correct HL7v2 clinical messages, parsers, and EHR integrations.
  Use when building ADT, ORU, ACK messages, parsing HL7 pipes, mapping
  LOINC/ICD-10/UCUM codes, designing Rhapsody/Mirth integration routes,
  or debugging HL7 message exchange failures.
---

# HL7v2 Integration

Build structurally valid HL7v2 messages with correct clinical coding on the first attempt. This skill encodes implementation patterns extracted from production healthcare integrations — not spec regurgitation.

## When to Use

- Building HL7v2 messages (ADT, ORU, ACK, ORM)
- Parsing or validating pipe-delimited HL7 messages
- Mapping clinical data to LOINC, ICD-10, UCUM codes
- Designing integration architecture with Rhapsody, Mirth Connect, or Cloverleaf
- Debugging HL7 message exchange failures (ACK/NAK, encoding, escaping)
- Building clinical alerting pipelines that consume OBX observations

## When NOT to Use

- FHIR R4 / JSON-based interoperability (different standard, different patterns)
- HL7 CDA (Clinical Document Architecture) — XML-based, not pipe-delimited
- Direct database integration (no message exchange involved)
- Non-clinical data exchange (HL7v2 is healthcare-specific)

## Top 5 Gotchas (ranked by frequency)

These are the things that break real HL7 integrations. Read these first.

### 1. Segment terminator: `\r` not `\n`

HL7v2 uses carriage return (`\r`, ASCII 13) as the segment terminator. Using `\n` (linefeed) is the single most common HL7 integration bug — the message looks right in your editor but the receiving system sees one giant segment.

```python
# WRONG — will fail silently in most integration engines
message = "MSH|^~\\&|...\nPID|1||...\nOBX|1|NM|..."

# CORRECT
message = "MSH|^~\\&|...\rPID|1||...\rOBX|1|NM|..."

# Build from segments list
segments = ["MSH|^~\\&|...", "PID|1||...", "OBX|1|NM|..."]
message = "\r".join(segments)
```

### 2. MSH-1 encoding quirk

MSH-1 (field separator) IS the `|` character itself. This means when you split MSH on `|`, the field indexes are offset by one compared to every other segment:

```python
msh = "MSH|^~\\&|SENDER|FACILITY|RECEIVER|FAC|20260115||ADT^A01^ADT_A01|CTRL01|P|2.5.1"
fields = msh.split("|")
# fields[0] = "MSH"        (segment ID)
# fields[1] = "^~\\&"      (MSH-2: encoding characters)
# fields[2] = "SENDER"     (MSH-3: sending application)
# fields[8] = "ADT^A01..."  (MSH-9: message type)
# fields[9] = "CTRL01"     (MSH-10: message control ID)

# For ANY OTHER segment, PID-3 is at fields[3]:
pid = "PID|1||PAT001^^^HOSP^MR||DOE^JOHN||19900101|M"
pid_fields = pid.split("|")
# pid_fields[3] = "PAT001^^^HOSP^MR"  (PID-3: patient ID)
```

### 3. Escape order matters

When escaping special characters in free-text fields, escape backslash FIRST. Otherwise you'll double-escape your own escape sequences:

```python
def escape_hl7(text: str) -> str:
    text = text.replace("\\", "\\E\\")   # Backslash first!
    text = text.replace("|", "\\F\\")
    text = text.replace("^", "\\S\\")
    text = text.replace("~", "\\R\\")
    text = text.replace("&", "\\T\\")
    return text
```

### 4. NTE segment length limit

Integration engines (Rhapsody, Mirth) truncate or reject NTE-3 content over ~200 characters. Split long clinical text at sentence boundaries:

```python
def split_nte(text: str, max_len: int = 200) -> list[str]:
    sentences = text.split(". ")
    chunks, current = [], ""
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
```

### 5. OBX-2 must match OBX-5 format

If OBX-2 = `NM` (numeric), OBX-5 must be a valid number. If OBX-2 = `ST` (string), OBX-5 is free text. Mismatches cause silent failures in many EHR parsers — the observation is accepted but never displayed.

## Message Construction Pattern

Every HL7v2 message follows the same build pattern:

```python
import hashlib
from datetime import datetime

ENCODING_CHARS = "^~\\&"
HL7_VERSION = "2.5.1"

def build_message(segments: list[str]) -> str:
    """Join segments with \\r (not \\n)."""
    return "\r".join(segments)

def timestamp(dt: datetime | None = None) -> str:
    """HL7 timestamp format: YYYYMMDDHHmmss."""
    return (dt or datetime.now()).strftime("%Y%m%d%H%M%S")

def control_id(identifier: str, msg_type: str) -> str:
    """Deterministic control ID for audit traceability."""
    return hashlib.md5(f"{identifier}:{msg_type}".encode()).hexdigest()[:10].upper()
```

## Message Types

### ADT^A01 — Patient Admission

Segments: MSH, EVN, PID, PV1, OBX (baseline vitals), DG1 (diagnoses).

Key patterns:
- PID-3: `PatientID^^^Facility^MR` — MR = Medical Record Number
- PID-8: `U` (unknown) is standard for neonatal sex
- OBX with LOINC 59408-5 for SpO2 baseline
- DG1 with ICD-10 codes for known conditions

See: [examples/adt_a01.py](examples/adt_a01.py)

### ACK — Acknowledgment

Segments: MSH, MSA. The HL7 handshake:

1. System A sends message → System B
2. System B processes, sends ACK → System A
3. System A marks message as delivered

Key patterns:
- **Swap sender/receiver** from original MSH
- MSA-1: `AA` (accept), `AE` (error), `AR` (reject)
- MSA-2: original message control ID (for correlation)

Without ACK handling, messages pile up in retry queues. Rhapsody won't mark a message delivered until it receives an ACK.

See: [examples/ack.py](examples/ack.py)

### ORU^R01 — Observation Result

Segments: MSH, PID, OBR, OBX (×N), NTE (×N).

Key patterns:
- OBR links all OBX segments to the order that requested them
- OBX-8 abnormal flags drive clinical alerting (see below)
- NTE segments carry clinical narrative, chunked at 200 chars

See: [examples/oru_r01.py](examples/oru_r01.py)

## Parsing

Three-level split: `\r` → segments, `|` → fields, `^` → components.

```python
def parse(raw: str) -> list[list[str]]:
    return [seg.split("|") for seg in raw.split("\r")]
```

Always validate after parsing:
- MSH is first segment
- Required segments present for message type
- OBX-2 matches OBX-5 format
- MSH-10 control ID is non-empty

See: [examples/parser.py](examples/parser.py), [examples/round_trip.py](examples/round_trip.py)

## Clinical Coding

### OBX-8 Abnormal Flags → EHR Alerting

| Urgency | OBX-8 | EHR Behavior |
|---------|-------|-------------|
| EMERGENCY | `AA` | Immediate nurse station alert, physician page |
| URGENT | `A` | Flagged abnormal, prompt clinical review |
| MONITOR | `H` | Above high normal, increased watch |
| ROUTINE | `N` | Filed in chart, no alert |

`AA` triggers the highest-priority alert in most EHR systems. Get this wrong and either nobody gets paged when they should, or the whole unit gets alarm fatigue.

Full reference: [reference/abnormal-flags.md](reference/abnormal-flags.md)

### LOINC Codes (OBX-3)

Format: `Code^Description^LN`

| Code | Observation | Unit |
|------|------------|------|
| `59408-5` | SpO2 (pulse oximetry) | `%` |
| `8867-4` | Heart rate | `/min` |
| `9279-1` | Respiratory rate | `/min` |
| `8310-5` | Body temperature | `Cel` |
| `8480-6` | Systolic BP | `mm[Hg]` |
| `29463-7` | Body weight | `kg` or `g` |

Full reference: [reference/loinc-common.md](reference/loinc-common.md)

### ICD-10 Codes (DG1-3)

Format: `Code^Description^I10`

| Code | Condition |
|------|-----------|
| `P28.4` | Apnea of prematurity |
| `P27.1` | Bronchopulmonary dysplasia |
| `P61.2` | Anemia of prematurity |
| `H35.10` | Retinopathy of prematurity |
| `P77.9` | Necrotizing enterocolitis |

Full reference: [reference/icd10-neonatal.md](reference/icd10-neonatal.md)

### Local Codes

When no standard code exists, use X-prefixed local codes with system `L`:

```
OBX|1|NM|X-GA-WEEKS^Gestational Age^L||30|wk^weeks^UCUM||||||F
```

Never invent fake LOINC or ICD-10 codes. Either use a real code or explicitly mark it as local.

## Integration Architecture

### Engine-Mediated Routing (Recommended)

```
Source System → Integration Engine → Destination System
               (Rhapsody/Mirth)
               ├─ Message validation
               ├─ Transformation rules
               ├─ ACK/NAK handling
               └─ Error queue (DLQ)
```

### ACK/NAK Pattern

```
Sender                  Engine                  Receiver
  │── message ──────────→│── route + transform ─→│
  │                       │←── ACK (AA) ─────────│
  │←── ACK (AA) ─────────│
  │                       │
  │  (if no ACK within    │
  │   timeout: retry,     │
  │   then DLQ)           │
```

### Production Checklist

1. **ACK/NAK handling** — retry policy with exponential backoff, dead letter queue after N failures
2. **IHE profiles** — PCD-01 (Patient Care Device) for device observations, PIX for patient ID cross-referencing
3. **PHI encryption** — TLS 1.2+ in transit, message-level encryption at rest
4. **Error queues** — DLQ → manual review → resubmit workflow
5. **Conformance validation** — validate against hospital-specific message profiles before go-live
6. **Batch vs real-time** — real-time for alerting (ORU), batch acceptable for administrative (ADT)

## Common Rationalizations

| What you'll hear | Why it's wrong |
|-----------------|---------------|
| "We'll add ACK handling later" | Messages will pile up in retry queues from day one |
| "Just use `\n`, it works in testing" | It works in YOUR parser. Rhapsody/Mirth expect `\r` |
| "FHIR replaces HL7v2" | v2 is still dominant in US hospital integrations. Most EHRs speak v2 natively |
| "We don't need escape sequences" | First patient with `&` in their name breaks the message |
| "One big NTE segment is fine" | Rhapsody truncates at ~200 chars. Your clinical summary gets cut off silently |

## Red Flags

Stop and investigate if you see:
- `\n` used as segment delimiter anywhere in message construction
- Hardcoded message control IDs (breaks audit trail and ACK correlation)
- LOINC or ICD-10 codes that don't appear in official registries
- Missing OBX-2 value type (causes silent parse failures in EHRs)
- No ACK handling in the integration design
- PHI in example code or test fixtures

## Verification Checklist

Before shipping any HL7 integration:

- [ ] All messages use `\r` segment terminator
- [ ] MSH-1 field indexing accounts for the separator quirk
- [ ] Every OBX-3 uses a real LOINC code or explicit local code (X-prefix, system `L`)
- [ ] Every DG1-3 uses a real ICD-10 code (system `I10`)
- [ ] OBX-2 data types match OBX-5 value formats
- [ ] Special characters in free text are escaped (order: `\` first)
- [ ] NTE segments stay under 200 characters
- [ ] ACK handler implemented with retry policy
- [ ] Message control IDs are unique and deterministic
- [ ] No real PHI in test data
- [ ] Round-trip test passes: build → parse → compare

## Reference Files

- [reference/segment-map.md](reference/segment-map.md) — Field positions for MSH, EVN, PID, PV1, OBX, DG1, OBR, MSA, NTE
- [reference/loinc-common.md](reference/loinc-common.md) — Common LOINC codes for vitals, labs, respiratory
- [reference/icd10-neonatal.md](reference/icd10-neonatal.md) — ICD-10 codes for neonatal conditions
- [reference/abnormal-flags.md](reference/abnormal-flags.md) — OBX-8 flag values and EHR alerting behavior
- [examples/](examples/) — Runnable Python scripts for ADT, ORU, ACK, parsing, round-trip
