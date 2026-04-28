# Common LOINC Codes for Clinical Monitoring

LOINC (Logical Observation Identifiers Names and Codes) codes for vitals, labs, and respiratory monitoring. These are the codes you'll use most often in OBX-3 when building HL7v2 messages.

> **Format in OBX-3**: `Code^Long Common Name^LN` — the `LN` system identifier tells the receiver this is a LOINC code.

---

## Vital Signs

| LOINC Code | Long Common Name | UCUM Unit | OBX-2 Type | Notes |
|------------|-----------------|-----------|------------|-------|
| `59408-5` | Oxygen saturation in Arterial blood by Pulse oximetry | `%` | NM | SpO2 — the primary pulse oximetry code |
| `2708-6` | Oxygen saturation in Arterial blood | `%` | NM | SaO2 (arterial blood gas, not pulse ox) |
| `8867-4` | Heart rate | `/min` | NM | Beats per minute |
| `9279-1` | Respiratory rate | `/min` | NM | Breaths per minute |
| `8310-5` | Body temperature | `Cel` | NM | Celsius; use `[degF]` for Fahrenheit |
| `85354-9` | Blood pressure panel with all children optional | — | — | Panel code; use children for systolic/diastolic |
| `8480-6` | Systolic blood pressure | `mm[Hg]` | NM | |
| `8462-4` | Diastolic blood pressure | `mm[Hg]` | NM | |
| `8478-0` | Mean blood pressure | `mm[Hg]` | NM | MAP — common in ICU/NICU monitoring |
| `29463-7` | Body weight | `kg` | NM | Use `g` for neonatal (grams) |
| `8302-2` | Body height | `cm` | NM | |
| `8287-5` | Head Occipital-frontal circumference by Tape measure | `cm` | NM | Head circumference — key neonatal metric |

---

## Respiratory / Oxygenation

| LOINC Code | Long Common Name | UCUM Unit | OBX-2 Type | Notes |
|------------|-----------------|-----------|------------|-------|
| `59408-5` | Oxygen saturation by Pulse oximetry | `%` | NM | Most common SpO2 code |
| `3150-0` | Inhaled oxygen concentration | `%` | NM | FiO2 |
| `19994-3` | Oxygen/Inspired gas setting [Volume Fraction] Ventilator | `%` | NM | Ventilator FiO2 setting |
| `33438-3` | Breath rate mechanical --on ventilator | `/min` | NM | Ventilator rate |
| `76222-9` | Apnea events in 24 hours | `{events}` | NM | Apnea event count |
| `20564-1` | Oxygen saturation in Blood | `%` | NM | Generic — prefer 59408-5 for pulse ox |

---

## Laboratory (Common in NICU)

| LOINC Code | Long Common Name | UCUM Unit | OBX-2 Type | Notes |
|------------|-----------------|-----------|------------|-------|
| `718-7` | Hemoglobin [Mass/volume] in Blood | `g/dL` | NM | |
| `4544-3` | Hematocrit [Volume Fraction] of Blood by Automated count | `%` | NM | |
| `789-8` | Erythrocytes [#/volume] in Blood by Automated count | `10*6/uL` | NM | RBC count |
| `6690-2` | Leukocytes [#/volume] in Blood by Automated count | `10*3/uL` | NM | WBC count |
| `1975-2` | Bilirubin.total [Mass/volume] in Serum or Plasma | `mg/dL` | NM | Critical for neonatal jaundice |
| `2339-0` | Glucose [Mass/volume] in Blood | `mg/dL` | NM | |
| `2019-8` | Carbon dioxide [Partial pressure] in Arterial blood | `mm[Hg]` | NM | pCO2 from ABG |
| `2703-7` | Oxygen [Partial pressure] in Arterial blood | `mm[Hg]` | NM | pO2 from ABG |
| `2744-1` | pH of Arterial blood | `[pH]` | NM | |

---

## UCUM Units Quick Reference

Units in OBX-6 should use UCUM (Unified Code for Units of Measure) format: `Code^Text^UCUM`.

| Clinical Unit | UCUM Code | OBX-6 Example |
|---------------|-----------|---------------|
| Percent | `%` | `%^percent^UCUM` |
| Beats/breaths per minute | `/min` | `/min^per minute^UCUM` |
| Millimeters of mercury | `mm[Hg]` | `mm[Hg]^mmHg^UCUM` |
| Celsius | `Cel` | `Cel^degrees Celsius^UCUM` |
| Kilograms | `kg` | `kg^kilograms^UCUM` |
| Grams | `g` | `g^grams^UCUM` |
| Centimeters | `cm` | `cm^centimeters^UCUM` |
| Milligrams per deciliter | `mg/dL` | `mg/dL^mg/dL^UCUM` |
| Grams per deciliter | `g/dL` | `g/dL^g/dL^UCUM` |
| Seconds | `s` | `s^seconds^UCUM` |
| Events (countable) | `{events}` | `{events}^events^UCUM` |
| Weeks | `wk` | `wk^weeks^UCUM` |

**Gotcha**: UCUM codes are case-sensitive. `Cel` (Celsius) is correct; `cel` is not. `L` (liter) ≠ `l` (not valid). Always verify against the [UCUM specification](https://ucum.org/ucum).
