# HL7v2 Segment Quick Reference

Field positions for the most common segments in clinical integrations (HL7 v2.5.1).

> **MSH-1 Quirk**: The field separator `|` **is** MSH-1. When you split MSH on `|`, index 0 = "MSH", index 1 = encoding chars (`^~\&`), index 2 = sending application. This offsets all MSH field numbers by -1 compared to what you'd expect. Every other segment indexes normally.

---

## MSH — Message Header

Every HL7 message starts with MSH. Controls routing, versioning, and message identification.

| Field | Position | Data Type | Description | Example |
|-------|----------|-----------|-------------|---------|
| Field Separator | MSH-1 | ST | Always `\|` — this IS the separator | `\|` |
| Encoding Characters | MSH-2 | ST | Component, repetition, escape, subcomponent | `^~\&` |
| Sending Application | MSH-3 | HD | System that originated the message | `NICU_SPO2_MONITOR` |
| Sending Facility | MSH-4 | HD | Facility of sending system | `GENERAL_HOSPITAL` |
| Receiving Application | MSH-5 | HD | Destination system | `RHAPSODY_ENGINE` |
| Receiving Facility | MSH-6 | HD | Destination facility | `GENERAL_HOSPITAL` |
| Date/Time of Message | MSH-7 | TS | Format: YYYYMMDDHHmmss | `20260115210000` |
| Security | MSH-8 | ST | Usually empty | |
| Message Type | MSH-9 | MSG | Type^Event^Structure | `ADT^A01^ADT_A01` |
| Message Control ID | MSH-10 | ST | Unique per message — used in ACK reference | `A3F7B2C901` |
| Processing ID | MSH-11 | PT | P=Production, T=Training, D=Debugging | `P` |
| Version ID | MSH-12 | VID | HL7 version | `2.5.1` |

**Practical note**: MSH-10 must be unique per message. Use a hash (e.g., MD5 of patient ID + message type) for deterministic IDs that are traceable in audit logs.

---

## EVN — Event Type

Describes the triggering event. Required in ADT messages.

| Field | Position | Data Type | Description | Example |
|-------|----------|-----------|-------------|---------|
| Event Type Code | EVN-1 | ID | Matches MSH-9 event code | `A01` |
| Recorded Date/Time | EVN-2 | TS | When the event was recorded | `20260115210000` |
| Date/Time Planned | EVN-3 | TS | Planned event time (optional) | |
| Event Reason Code | EVN-4 | IS | Why the event occurred | `01` (patient request) |
| Operator ID | EVN-5 | XCN | User who triggered the event | |

---

## PID — Patient Identification

Core patient demographics. Present in nearly every clinical message.

| Field | Position | Data Type | Description | Example |
|-------|----------|-----------|-------------|---------|
| Set ID | PID-1 | SI | Sequence number (usually `1`) | `1` |
| Patient ID (external) | PID-2 | CX | External ID (deprecated in 2.5+) | |
| Patient ID (internal) | PID-3 | CX | MRN: `ID^^^Facility^MR` | `PAT001^^^HOSP^MR` |
| Alternate Patient ID | PID-4 | CX | Secondary IDs | |
| Patient Name | PID-5 | XPN | `Last^First^Middle^Suffix^Prefix` | `DOE^JOHN^M` |
| Mother's Maiden Name | PID-6 | XPN | | |
| Date/Time of Birth | PID-7 | TS | YYYYMMDD or YYYYMMDDHHmmss | `20260110` |
| Administrative Sex | PID-8 | IS | M, F, U (unknown), O (other) | `U` |

**Neonatal note**: Use `U` (unknown) for sex when not yet determined or not relevant to the clinical context. PID-3 identifier type `MR` = Medical Record Number — the most common patient identifier in US hospital systems.

---

## PV1 — Patient Visit

Describes the patient's location and encounter details.

| Field | Position | Data Type | Description | Example |
|-------|----------|-----------|-------------|---------|
| Set ID | PV1-1 | SI | Sequence number | `1` |
| Patient Class | PV1-2 | IS | I=Inpatient, O=Outpatient, E=Emergency | `I` |
| Assigned Patient Location | PV1-3 | PL | `Unit^Room^Bed^Facility` | `NICU^BED01^^HOSP` |
| Admission Type | PV1-4 | IS | | |
| Attending Doctor | PV1-7 | XCN | | |
| Admit Date/Time | PV1-44 | TS | When patient was admitted | `20260115210000` |

**Practical note**: PV1-3 location format varies wildly by hospital. Some use `Unit^Room^^Facility`, others use `Building^Floor^Room^Bed`. Always check the receiving system's conformance profile.

---

## OBX — Observation/Result

The workhorse segment for clinical data. Carries vitals, lab results, device readings.

| Field | Position | Data Type | Description | Example |
|-------|----------|-----------|-------------|---------|
| Set ID | OBX-1 | SI | Sequence number within message | `1` |
| Value Type | OBX-2 | ID | NM=Numeric, ST=String, TX=Text, CWE=Coded | `NM` |
| Observation Identifier | OBX-3 | CWE | `Code^Text^System` (LOINC, local) | `59408-5^SpO2^LN` |
| Observation Sub-ID | OBX-4 | ST | Distinguishes repeated observations | |
| Observation Value | OBX-5 | varies | The actual result value | `97.2` |
| Units | OBX-6 | CWE | `Code^Text^System` (UCUM) | `%^percent^UCUM` |
| Reference Range | OBX-7 | ST | Normal range for this observation | `>94` |
| Abnormal Flags | OBX-8 | IS | Drives EHR alerting — see [abnormal-flags.md](abnormal-flags.md) | `AA` |
| Probability | OBX-9 | NM | | |
| Nature of Abnormal Test | OBX-10 | ID | | |
| Observation Result Status | OBX-11 | ID | F=Final, P=Preliminary, C=Corrected | `F` |
| Observation Date/Time | OBX-14 | TS | When the observation was taken | `20260115210000` |

**Critical**: OBX-2 must match the value in OBX-5. If OBX-2 = `NM`, OBX-5 must be a valid number. Mismatches cause silent failures in many EHR parsers.

**Clinical coding**: OBX-3 system field: `LN` = LOINC, `L` = Local, `I10` = ICD-10. See [loinc-common.md](loinc-common.md) for common LOINC codes.

---

## DG1 — Diagnosis

Carries diagnosis codes (ICD-10, ICD-9). Used in ADT and billing messages.

| Field | Position | Data Type | Description | Example |
|-------|----------|-----------|-------------|---------|
| Set ID | DG1-1 | SI | Sequence number | `1` |
| Diagnosis Coding Method | DG1-2 | ID | Deprecated — leave empty | |
| Diagnosis Code | DG1-3 | CWE | `Code^Description^System` | `P28.4^Apnea of newborn^I10` |
| Diagnosis Description | DG1-4 | ST | Free-text description (deprecated) | |
| Diagnosis Date/Time | DG1-5 | TS | When diagnosed | `20260115210000` |
| Diagnosis Type | DG1-6 | IS | A=Admitting, W=Working, F=Final | `A` |

**Practical note**: DG1-3 coding system: `I10` = ICD-10-CM, `I9` = ICD-9-CM. Always use the code system identifier — don't rely on the receiving system to guess. See [icd10-neonatal.md](icd10-neonatal.md) for common neonatal codes.

---

## OBR — Observation Request

Links observations (OBX) to the order that requested them. Required in ORU messages.

| Field | Position | Data Type | Description | Example |
|-------|----------|-----------|-------------|---------|
| Set ID | OBR-1 | SI | Sequence number | `1` |
| Placer Order Number | OBR-2 | EI | Ordering system's ID | `ORD001` |
| Filler Order Number | OBR-3 | EI | Performing system's ID | |
| Universal Service ID | OBR-4 | CWE | What was ordered — LOINC code | `59408-5^SpO2 Monitoring^LN` |
| Observation Date/Time | OBR-7 | TS | When the observation started | `20260115210000` |
| Result Status | OBR-25 | ID | F=Final, P=Preliminary | `F` |

---

## MSA — Message Acknowledgment

Present in ACK messages. References the original message being acknowledged.

| Field | Position | Data Type | Description | Example |
|-------|----------|-----------|-------------|---------|
| Acknowledgment Code | MSA-1 | ID | AA=Accept, AE=Error, AR=Reject | `AA` |
| Message Control ID | MSA-2 | ST | MSH-10 from the original message | `A3F7B2C901` |
| Text Message | MSA-3 | ST | Human-readable error description | `Message processed` |

**Integration note**: Rhapsody and Mirth both use MSA-1 to determine message disposition. `AA` = delivered successfully. `AE` = application-level error (message understood but rejected). `AR` = message rejected (parse failure, invalid structure). Always include MSA-2 so the sender can correlate the ACK to the original message.

---

## NTE — Notes and Comments

Free-text annotations attached to the preceding segment. Used for clinical narrative.

| Field | Position | Data Type | Description | Example |
|-------|----------|-----------|-------------|---------|
| Set ID | NTE-1 | SI | Sequence number | `1` |
| Source of Comment | NTE-2 | ID | L=Ancillary, P=Plasmapheresis, O=Other | `L` |
| Comment | NTE-3 | FT | Free text (escaped) | `Patient showed improvement...` |
| Comment Type | NTE-4 | CWE | RE=Remark, AI=Instructions | `RE` |

**Rhapsody gotcha**: NTE-3 has a practical limit of ~200 characters per segment. Long text must be split across multiple NTE segments at sentence boundaries. Many integration engines truncate or reject NTE segments over 200 chars. Split your text before building the message, not after.
