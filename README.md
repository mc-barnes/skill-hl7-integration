# HL7v2 Integration Skill for Claude Code

A Claude Code skill that helps healthcare engineers and PMs build correct HL7v2 integrations — message construction, parsing, validation, and clinical coding.

**Not a spec dump.** This skill encodes implementation patterns from production healthcare integrations: the MSH-1 encoding quirk, NTE chunking for Rhapsody, abnormal flag semantics that drive nurse station alerts, and the escape sequence ordering that trips up every first-time implementer.

## Who This Is For

- Healthcare engineers building EHR integrations (Rhapsody, Mirth Connect, Cloverleaf)
- PMs writing requirements for clinical data exchange
- Anyone building clinical alerting pipelines that consume HL7v2 observations
- Developers new to HL7v2 who want to get it right on the first attempt

## Install

### Option 1: Clone and copy (recommended)

```bash
git clone https://github.com/mc-barnes/skill-hl7-integration.git
cp skill-hl7-integration/SKILL.md ~/.claude/skills/hl7-integration/SKILL.md
```

### Option 2: Skill Seekers

```bash
pip install skill-seekers
skill-seekers install mc-barnes/skill-hl7-integration --target claude
```

### Option 3: Direct download

Download [`SKILL.md`](SKILL.md) and place it at `~/.claude/skills/hl7-integration/SKILL.md`.

## What's Included

| File | Description |
|------|-------------|
| [`SKILL.md`](SKILL.md) | The skill itself — message building, parsing, clinical coding, integration patterns, gotchas |
| [`examples/`](examples/) | 5 runnable Python scripts (stdlib only, Python 3.10+) |
| [`reference/`](reference/) | Quick-lookup tables for segments, LOINC, ICD-10, abnormal flags |

### Examples

```bash
python examples/adt_a01.py      # Build an ADT^A01 admission message
python examples/oru_r01.py      # Build an ORU^R01 observation result
python examples/ack.py          # Build ACK responses (AA, AE, AR)
python examples/parser.py       # Parse and validate HL7 messages
python examples/round_trip.py   # Build → parse → verify fields match
```

### Reference Docs

- [`reference/segment-map.md`](reference/segment-map.md) — MSH, EVN, PID, PV1, OBX, DG1, OBR, MSA, NTE field positions
- [`reference/loinc-common.md`](reference/loinc-common.md) — 15+ LOINC codes for vitals, labs, respiratory
- [`reference/icd10-neonatal.md`](reference/icd10-neonatal.md) — 30+ ICD-10 codes for neonatal conditions
- [`reference/icd10-cardiometabolic.md`](reference/icd10-cardiometabolic.md) — 70+ ICD-10 codes for cardiometabolic conditions
- [`reference/abnormal-flags.md`](reference/abnormal-flags.md) — OBX-8 values and how they drive EHR alerting

## Quick Example

```python
import hashlib
from datetime import datetime

# Every HL7v2 message: build segments, join with \r (NOT \n)
segments = [
    # MSH-1 is | itself — this offsets all field indexes
    f"MSH|^~\\&|MY_APP|HOSPITAL|EHR|HOSPITAL|{datetime.now():%Y%m%d%H%M%S}||"
    f"ADT^A01^ADT_A01|{hashlib.md5(b'demo').hexdigest()[:10].upper()}|P|2.5.1",
    f"EVN|A01|{datetime.now():%Y%m%d%H%M%S}",
    "PID|1||PAT001^^^HOSPITAL^MR||DOE^JANE||20260110|F",
    "PV1|1|I|NICU^BED01^^HOSPITAL",
    # OBX with LOINC code, UCUM units, abnormal flag
    "OBX|1|NM|59408-5^Oxygen saturation Pulse oximetry^LN||97.2|%^percent^UCUM|>94|N|||F",
]
message = "\r".join(segments)
```

## License

MIT — see [LICENSE](LICENSE).

## Author

**McCay Barnes** — Healthcare PM specializing in software medical devices (SaMD), EHR integration, and clinical AI pipelines. Built from patterns in production HL7v2 integrations across Rhapsody, Mirth Connect, and direct EHR feeds.
