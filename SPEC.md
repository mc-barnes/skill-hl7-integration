# SPEC: HL7v2 Integration Skill for Claude Code

## 1. Objective

Build and publish a Claude Code skill that helps healthcare engineers and PMs build correct HL7v2 integrations — message construction, parsing, validation, integration architecture, and clinical coding. Published as a standalone GitHub repo (`mccaybarnes/hl7-integration-skill`) and Skill Seekers package.

### Why this exists
- Demonstrates domain expertise as a **publishable artifact**, not a resume bullet
- Encodes hard-won knowledge (MSH-1 quirk, NTE chunking, Rhapsody constraints, abnormal flag semantics) that generic HL7 docs don't teach
- Serves as the flagship of a "Claude Skills I've Published" resume section

### Target users
Healthcare engineers and PMs building clinical integrations (EHR systems, Rhapsody, NICU/patient monitors, clinical alerting pipelines) who use Claude Code as their development assistant.

### Success criteria
- Skill enables a developer to build a structurally valid HL7v2 message (ADT, ORU, ACK) with correct clinical coding on their first attempt
- Covers the 4 most common HL7v2 gotchas that trip up first-time implementers
- Published to GitHub with README, installable via Skill Seekers
- Usable as a Claude Code skill (drop into `~/.claude/skills/`)

## 2. Skill Capabilities (4 sections)

### 2.1 Build HL7v2 Messages
Teach Claude how to construct correct pipe-delimited messages for common clinical workflows.

**Message types covered:**
- ADT^A01 (Patient Admission) — MSH, EVN, PID, PV1, OBX, DG1
- ADT^A08 (Patient Update) — demographics/location changes
- ACK (Acknowledgment) — MSH, MSA with AA/AE/AR codes
- ORU^R01 (Observation Result) — MSH, PID, OBR, OBX, NTE
- ORM^O01 (Order) — brief coverage for completeness

**What makes it opinionated (not a docs dump):**
- Hand-crafted approach: no external HL7 libraries, pipe-delimited from scratch
- MSH-1 encoding quirk documented with correct field indexing
- Segment construction patterns with Python/TypeScript code templates
- Deterministic message control IDs for audit trails
- `\r` (CR) segment terminator — the #1 beginner mistake

### 2.2 Parse & Validate Messages
Round-trip parsing patterns and structural validation.

**Patterns:**
- Segment-by-segment parser (split on `\r`, then `|`, then `^`)
- Field extraction by segment type + position (PID-3, OBX-5, etc.)
- Round-trip validation: build → parse → compare
- HL7 special character escaping/unescaping (`\F\`, `\S\`, `\R\`, `\E\`, `\T\`)
- Encoding character detection from MSH-2

**Validation checks:**
- Required segments present (MSH mandatory, message-type-specific segments)
- MSH field count and encoding character consistency
- OBX data type matches value format (NM=numeric, ST=string, TX=text)
- Timestamp format (YYYYMMDDHHmmss)

### 2.3 Design Integration Architecture
Guidance for production HL7 integration patterns, focused on Rhapsody-style engines.

**Topics:**
- Message routing: point-to-point vs. engine-mediated (Rhapsody, Mirth, Cloverleaf)
- ACK/NAK patterns: immediate vs. deferred, retry policies, dead letter queues
- IHE profiles: PCD-01 (Patient Care Device), PIX (Patient Identifier Cross-reference)
- PHI handling: TLS 1.2+ in transit, message-level encryption at rest
- Error queue design: DLQ → manual review → resubmit workflow
- Conformance validation: hospital-specific message profiles
- Batch vs. real-time ORU routing tradeoffs
- Testing strategy: message conformance tools, round-trip validation

### 2.4 Clinical Coding Guidance
Correct codes for common clinical scenarios — the part that trips up pure software engineers.

**Code systems:**
- **LOINC** — observation identifiers (59408-5 SpO2, vitals, lab results)
- **ICD-10** — diagnosis codes (neonatal: P28.4 apnea, P27.1 BPD, P61.2 anemia; cardiovascular, metabolic)
- **UCUM** — units of measure (%, mmHg, g, mL, bpm)
- **OBX-8 Abnormal Flags** — AA (critical), A (abnormal), H (high), L (low), N (normal) and how they drive EHR clinical alerting rules
- **Local codes** — when and how to define X-prefixed local observation codes
- **Identifier types** — MR (medical record), VN (visit number), PI (patient internal)

**Common mapping patterns:**
- Vitals → LOINC + UCUM with correct OBX structure
- Diagnoses → ICD-10 in DG1 segments
- Urgency/severity → OBX-8 abnormal flags for nurse station alerting

## 3. Project Structure

```
hl7-integration-skill/
├── README.md              # What it is, install instructions, example usage
├── SKILL.md               # The actual Claude Code skill file
├── LICENSE                 # MIT
├── examples/
│   ├── adt_a01.py         # Build an ADT admission message
│   ├── oru_r01.py         # Build an ORU observation result
│   ├── ack.py             # Build ACK/NAK responses
│   ├── parser.py          # Parse and validate HL7 messages
│   └── round_trip.py      # Full round-trip: build → parse → validate
├── reference/
│   ├── segment-map.md     # Quick-reference: segment → fields → description
│   ├── loinc-common.md    # Frequently used LOINC codes in clinical monitoring
│   ├── icd10-neonatal.md  # ICD-10 codes for neonatal conditions
│   └── abnormal-flags.md  # OBX-8 flag → EHR alerting behavior
└── .github/
    └── workflows/
        └── validate.yml   # CI: lint examples, validate SKILL.md structure
```

### Key files
- `SKILL.md` — The skill itself. Installed by copying to `~/.claude/skills/hl7-integration/SKILL.md`
- `examples/` — Standalone, runnable Python scripts (no external deps beyond stdlib)
- `reference/` — Quick-lookup tables for clinical coding during development

## 4. Build Approach (Hybrid)

### Phase 1: Skill Seekers scaffold
Scrape HL7.org v2.5.1 spec reference to get:
- Standard segment definitions and field numbering
- Data type catalog
- Encoding rules

### Phase 2: Hand-write opinionated sections
Layer in knowledge from the spo2-eval-pipeline implementation:
- MSH-1 encoding quirk (field separator IS the first field)
- NTE chunking at sentence boundaries (200-char Rhapsody constraint)
- HL7 escape sequences (order matters: backslash first)
- Abnormal flag → clinical alerting mapping
- Deterministic message control IDs for audit trails
- Hand-crafted vs. library tradeoffs
- GA-adjusted threshold lookups in OBX
- ICD-10 mapping patterns for neonatal conditions
- Round-trip validation as a correctness proof

### Phase 3: Examples from spo2-eval-pipeline
Extract and generalize the working code from `src/interop/hl7_messages.py` into standalone examples that work without the spo2 project dependencies.

### Phase 4: Package and publish
- `skill-seekers package` for Claude target
- Push to GitHub
- Update resume with "Claude Skills I've Published" section

## 5. Code Style

### SKILL.md
- Frontmatter: `name`, `description`, trigger conditions
- Sections: When to Use, Message Building, Parsing, Architecture, Clinical Coding, Gotchas
- Code examples inline (Python primary, TypeScript secondary)
- Tables for quick-reference lookups (segment maps, LOINC codes, abnormal flags)
- Opinionated guidance marked as such ("In practice..." / "Gotcha:" / "Why:")

### Example scripts
- Python 3.10+, stdlib only (no external deps)
- Type hints on all functions
- Docstrings explaining the HL7 context (not just the code)
- Each example is self-contained and runnable (`python examples/adt_a01.py`)
- Output includes the raw HL7 message so users can inspect it

### Reference docs
- Markdown tables, scannable
- Sourced from HL7.org with citations
- Annotated with practical notes ("This is the code that drives nurse station alerts")

## 6. Testing Strategy

### Example scripts
- Each script runs without errors: `python examples/*.py`
- Each script produces valid HL7 output (segments separated by `\r`, MSH-1 = `|`)
- Round-trip example: build → parse → assert fields match

### CI (GitHub Actions)
- Run all examples on Python 3.10/3.11/3.12
- Lint with ruff
- Validate SKILL.md frontmatter is valid YAML

## 7. Boundaries

### Always do
- Use correct LOINC/ICD-10/UCUM codes — never invent clinical codes
- Include the MSH-1 encoding quirk warning in every message-building context
- Use `\r` (CR) as segment terminator, not `\n`
- Escape special characters in free-text fields
- Include message control IDs for audit trail traceability
- Cite HL7.org spec version (2.5.1) for standard references

### Ask first
- Which HL7 version to target (default 2.5.1, but 2.3.1 and 2.4 are still common)
- Whether to use hand-crafted or library-based approach (recommend hand-crafted for learning, library for production)
- Which integration engine (Rhapsody, Mirth Connect, Cloverleaf) — patterns differ
- Whether PHI will be present (changes encryption/audit requirements)

### Never do
- Generate fake LOINC/ICD-10 codes — always use real codes or explicitly mark as local (X-prefix)
- Skip ACK handling in integration architecture guidance
- Recommend sending HL7 over unencrypted channels
- Use `\n` as segment delimiter (the single most common HL7 integration bug)
- Include real PHI in examples (always use DEMO/simulated patient data)
- Claim FHIR replaces HL7v2 — v2 is still dominant in hospital integrations

## 8. Differentiation — What Makes This "Killer"

Most HL7 resources are either:
1. **Spec dumps** — regurgitate the 1,500-page standard without practical guidance
2. **Library tutorials** — teach python-hl7 or hl7apy API without understanding the protocol
3. **Academic** — explain the standard without production gotchas

This skill is none of those. It's:
- **Implementation-first** — patterns extracted from working code, not spec reading
- **Gotcha-driven** — leads with the things that break real integrations (MSH-1 offset, NTE chunking, \r vs \n, escaping order)
- **Clinically grounded** — correct LOINC/ICD-10/UCUM codes, abnormal flag semantics that drive real EHR alerting
- **Integration-engine-aware** — Rhapsody/Mirth patterns, ACK/NAK, error queues, conformance profiles
- **Opinionated** — recommends hand-crafted messages for understanding, explains WHY each field matters for clinical workflows

## 9. Distribution

| Channel | Format | Install |
|---------|--------|---------|
| GitHub | Standalone repo | `git clone` → copy `SKILL.md` to `~/.claude/skills/hl7-integration/` |
| Skill Seekers | Published package | `skill-seekers install mccaybarnes/hl7-integration-skill --target claude` |
| Manual | Direct download | Download `SKILL.md`, drop in skills directory |

## 10. Resume Integration

**Before (generic):**
> Skills: Python, AWS, HL7, FHIR, SQL, Jira

**After (differentiated):**
> **Published Claude Skills**
> - [HL7v2 Integration](github.com/mccaybarnes/hl7-integration-skill) — Clinical message construction, parsing, and EHR integration patterns for Claude Code
> - *(future: FHIR R4, IEC 62304 Design Controls, FDA Submission Workflows)*
