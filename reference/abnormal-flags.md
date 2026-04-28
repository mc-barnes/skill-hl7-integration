# OBX-8 Abnormal Flags — EHR Alerting Behavior

Abnormal flags in OBX-8 drive clinical alerting in the receiving EHR. This is how a vitals observation triggers (or doesn't trigger) a nurse station alert, a physician notification, or a clinical decision support rule.

> **This is the field that matters most for clinical workflow.** Get the LOINC code wrong and the observation lands in the wrong category. Get OBX-8 wrong and the wrong people get paged at 3am — or nobody gets paged when they should.

---

## Flag Values (HL7 Table 0078)

| Flag | Name | Meaning | Typical EHR Behavior |
|------|------|---------|---------------------|
| `N` | Normal | Within normal reference range | No alert. Observation filed in chart. |
| `L` | Low | Below normal range | Flagged in results list. May trigger passive alert depending on EHR configuration. |
| `H` | High | Above normal range | Flagged in results list. May trigger passive alert. |
| `LL` | Critical Low | Below critical low threshold | **Active alert.** EHR may trigger audible alarm, page provider, or require acknowledgment. |
| `HH` | Critical High | Above critical high threshold | **Active alert.** Same as LL — immediate attention required. |
| `A` | Abnormal | Abnormal (direction unspecified) | Flagged as abnormal. Behavior varies by EHR configuration. Common in qualitative results. |
| `AA` | Critical Abnormal | Critically abnormal | **Highest priority alert.** Nurse station immediate notification. May auto-escalate if not acknowledged within configured timeout. |

---

## Less Common Flags

| Flag | Name | Meaning | When to Use |
|------|------|---------|-------------|
| `<` | Below absolute low-off instrument scale | Value below detectable range | Instrument limitation, not necessarily clinical |
| `>` | Above absolute high-off instrument scale | Value above detectable range | Instrument limitation |
| `B` | Better | Improved compared to previous | Trending context |
| `W` | Worse | Deteriorated compared to previous | Trending context |
| `U` | Significant change up | Significantly increased | Delta check triggered |
| `D` | Significant change down | Significantly decreased | Delta check triggered |
| `I` | Intermediate (microbiology) | Intermediate susceptibility | Antimicrobial susceptibility testing |
| `R` | Resistant (microbiology) | Resistant to antimicrobial | Antimicrobial susceptibility testing |
| `S` | Susceptible (microbiology) | Susceptible to antimicrobial | Antimicrobial susceptibility testing |

---

## Clinical Urgency → OBX-8 Mapping

When translating clinical urgency levels to OBX-8 flags for EHR integration:

| Clinical Urgency | OBX-8 Flag | Rationale |
|-----------------|------------|-----------|
| EMERGENCY | `AA` | Critical abnormal — immediate bedside response required |
| URGENT | `A` | Abnormal — prompt clinical review within minutes |
| MONITOR | `H` | Above high normal — increased observation frequency |
| ROUTINE | `N` | Normal — standard monitoring continues |

**Why not use `HH`/`LL` instead of `AA`?** `HH`/`LL` imply a numeric value outside a specific range. `AA` is a general critical abnormal that works for both numeric observations (SpO2 = 72%) and qualitative assessments (triage = EMERGENCY). Use `AA` when the urgency is derived from a clinical assessment, not just a threshold comparison.

---

## How EHRs Process OBX-8

### Alert Routing (typical Rhapsody/Mirth configuration)

```
OBX-8 = AA or HH or LL
  → Route to: nurse station alert queue + physician pager
  → Acknowledge timeout: 5 minutes
  → Escalation: charge nurse if unacknowledged

OBX-8 = A or H or L
  → Route to: results inbox with visual flag
  → No active alert unless matching a CDS rule

OBX-8 = N
  → Route to: results inbox, no flag
  → Standard chart filing
```

### Conformance Notes

1. **Multiple flags**: OBX-8 supports repetition (`~` separator). Example: `H~A` means both high and abnormal. Most EHRs use the highest-priority flag for alerting.
2. **Empty OBX-8**: If omitted, most EHRs treat the result as normal. Some systems flag missing OBX-8 as a conformance warning.
3. **Reference range interaction**: OBX-7 (reference range) and OBX-8 (abnormal flag) should be consistent. If OBX-7 = `>94` and OBX-5 = `91`, OBX-8 should be `L` or `A`, not `N`.
4. **CDS override**: Clinical Decision Support rules in the EHR can override OBX-8 alerting. A `H` flag might trigger an active alert if combined with other patient context (e.g., patient age, comorbidities).
