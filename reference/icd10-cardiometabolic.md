# ICD-10-CM Codes for Cardiometabolic Conditions

Diagnosis codes for cardiometabolic conditions commonly encountered in digital therapeutics, remote patient monitoring, and chronic disease management integrations. Used in DG1-3 segments with system identifier `I10`.

> **Format in DG1-3**: `Code^Description^I10` — the `I10` system identifier tells the receiver this is ICD-10-CM.

---

## Type 2 Diabetes Mellitus

| ICD-10 Code | Description | Clinical Context |
|-------------|-------------|------------------|
| `E11.9` | Type 2 diabetes mellitus without complications | Most common primary diagnosis for diabetes management programs |
| `E11.65` | Type 2 diabetes mellitus with hyperglycemia | Elevated blood glucose requiring intervention |
| `E11.69` | Type 2 diabetes mellitus with other specified complication | |
| `E11.40` | Type 2 diabetes mellitus with diabetic neuropathy, unspecified | Nerve damage complication |
| `E11.21` | Type 2 diabetes mellitus with diabetic nephropathy | Kidney disease complication |
| `E11.319` | Type 2 diabetes mellitus with unspecified diabetic retinopathy without macular edema | Eye complication |
| `E11.51` | Type 2 diabetes mellitus with diabetic peripheral angiopathy without gangrene | Vascular complication |
| `E11.22` | Type 2 diabetes mellitus with diabetic chronic kidney disease | CKD secondary to diabetes |
| `E13.9` | Other specified diabetes mellitus without complications | For atypical or secondary diabetes |

**Coding note**: Type 2 diabetes codes (E11.x) require a 4th-6th character for complication specificity. `E11.9` (without complications) is the starting point for most digital therapeutic and RPM enrollments. Add complication codes as secondary diagnoses when applicable.

---

## Prediabetes / Glucose Metabolism

| ICD-10 Code | Description | Clinical Context |
|-------------|-------------|------------------|
| `R73.03` | Prediabetes | Impaired fasting glucose or impaired glucose tolerance — key enrollment criterion for prevention programs |
| `R73.01` | Impaired fasting glucose | Fasting glucose 100-125 mg/dL |
| `R73.02` | Impaired glucose tolerance (oral) | 2-hour OGTT glucose 140-199 mg/dL |
| `R73.09` | Other abnormal glucose | |
| `E88.81` | Metabolic syndrome | Cluster: central obesity + dyslipidemia + hypertension + insulin resistance |

---

## Obesity

| ICD-10 Code | Description | Clinical Context |
|-------------|-------------|------------------|
| `E66.01` | Morbid (severe) obesity due to excess calories | BMI ≥40, or ≥35 with comorbidity |
| `E66.09` | Other obesity due to excess calories | BMI 30-39.9 without qualifying as morbid |
| `E66.1` | Drug-induced obesity | Obesity secondary to medication (e.g., antipsychotics, corticosteroids) |
| `E66.3` | Overweight | BMI 25-29.9 |
| `E66.9` | Obesity, unspecified | |
| `Z68.30` | Body mass index [BMI] 30.0-30.9, adult | BMI codes used as secondary diagnosis |
| `Z68.35` | Body mass index [BMI] 35.0-35.9, adult | |
| `Z68.41` | Body mass index [BMI] 40.0-44.9, adult | |
| `Z68.45` | Body mass index [BMI] 45.0-49.9, adult | |

**Coding note**: BMI Z-codes (Z68.x) are always secondary — never the primary diagnosis. Pair with the appropriate E66.x obesity code as primary.

---

## Hypertension

| ICD-10 Code | Description | Clinical Context |
|-------------|-------------|------------------|
| `I10` | Essential (primary) hypertension | Most common hypertension diagnosis — systolic ≥130 or diastolic ≥80 (2017 ACC/AHA) |
| `I11.9` | Hypertensive heart disease without heart failure | Hypertension with cardiac involvement |
| `I11.0` | Hypertensive heart disease with heart failure | |
| `I12.9` | Hypertensive chronic kidney disease with stage 1-4 or unspecified CKD | |
| `I13.10` | Hypertensive heart and chronic kidney disease without heart failure | Combined cardiac + renal |
| `I15.0` | Renovascular hypertension | Secondary hypertension — renal artery stenosis |
| `I15.8` | Other secondary hypertension | |
| `R03.0` | Elevated blood-pressure reading, without diagnosis of hypertension | Pre-hypertension or white coat |

---

## Dyslipidemia

| ICD-10 Code | Description | Clinical Context |
|-------------|-------------|------------------|
| `E78.5` | Dyslipidemia, unspecified | Mixed or unspecified lipid disorder |
| `E78.00` | Pure hypercholesterolemia, unspecified | Elevated total cholesterol / LDL |
| `E78.01` | Familial hypercholesterolemia | Genetic — high cardiovascular risk |
| `E78.1` | Pure hypertriglyceridemia | Elevated triglycerides (≥150 mg/dL) |
| `E78.2` | Mixed hyperlipidemia | Both cholesterol and triglycerides elevated |
| `E78.41` | Elevated Lipoprotein(a) | Emerging cardiovascular risk marker |
| `E78.49` | Other hyperlipidemia | |
| `E78.6` | Lipoprotein deficiency | Low HDL |

---

## Heart Failure

| ICD-10 Code | Description | Clinical Context |
|-------------|-------------|------------------|
| `I50.9` | Heart failure, unspecified | |
| `I50.20` | Unspecified systolic (HFrEF) heart failure | Reduced ejection fraction — EF <40% |
| `I50.22` | Chronic systolic (HFrEF) heart failure | |
| `I50.30` | Unspecified diastolic (HFpEF) heart failure | Preserved ejection fraction — EF ≥50% |
| `I50.32` | Chronic diastolic (HFpEF) heart failure | |
| `I50.42` | Chronic combined systolic and diastolic heart failure | |
| `I50.810` | Right heart failure, unspecified | |
| `I50.84` | End stage heart failure | |

---

## Atherosclerotic Cardiovascular Disease

| ICD-10 Code | Description | Clinical Context |
|-------------|-------------|------------------|
| `I25.10` | Atherosclerotic heart disease of native coronary artery without angina pectoris | CAD without symptoms |
| `I25.110` | Atherosclerotic heart disease of native coronary artery with unstable angina pectoris | |
| `I25.5` | Ischemic cardiomyopathy | Heart muscle damage from chronic ischemia |
| `I25.2` | Old myocardial infarction | History of MI — important for risk stratification |
| `I63.9` | Cerebral infarction, unspecified | Stroke |
| `I73.9` | Peripheral vascular disease, unspecified | PAD |
| `Z86.73` | Personal history of transient ischemic attack (TIA) | |

---

## Chronic Kidney Disease (Cardiorenal)

| ICD-10 Code | Description | Clinical Context |
|-------------|-------------|------------------|
| `N18.1` | Chronic kidney disease, stage 1 | GFR ≥90 with kidney damage markers |
| `N18.2` | Chronic kidney disease, stage 2 (mild) | GFR 60-89 |
| `N18.3` | Chronic kidney disease, stage 3 (moderate) | GFR 30-59 — medication dose adjustments begin |
| `N18.4` | Chronic kidney disease, stage 4 (severe) | GFR 15-29 |
| `N18.5` | Chronic kidney disease, stage 5 | GFR <15 — dialysis or transplant candidate |
| `N18.6` | End stage renal disease | On dialysis or post-transplant |
| `N18.9` | Chronic kidney disease, unspecified | |

**Coding note**: CKD is frequently comorbid with diabetes and hypertension. When both are present, use combination codes (I12.x for hypertensive CKD, E11.22 for diabetic CKD) rather than coding each independently.

---

## Non-Alcoholic Fatty Liver Disease

| ICD-10 Code | Description | Clinical Context |
|-------------|-------------|------------------|
| `K76.0` | Fatty (change of) liver, not elsewhere classified | NAFLD — simple steatosis |
| `K75.81` | Nonalcoholic steatohepatitis (NASH) | Inflammatory progression of NAFLD |
| `K74.0` | Hepatic fibrosis | Scarring — may progress to cirrhosis |
| `K74.60` | Unspecified cirrhosis of liver | End-stage liver disease |

---

## Common Comorbidity Clusters

Cardiometabolic patients rarely present with a single condition. These clusters drive enrollment criteria and risk stratification:

| Cluster | Typical Code Combination | Clinical Program |
|---------|-------------------------|-----------------|
| Metabolic syndrome | E88.81 + E66.09 + E78.5 + I10 | Lifestyle intervention / digital therapeutic |
| Diabetic cardiorenal | E11.22 + I12.9 + N18.3 | Nephrology co-management |
| Post-MI secondary prevention | I25.2 + E78.00 + I10 + E11.9 | Cardiac rehab / RPM |
| Prediabetes prevention | R73.03 + E66.09 | DPP (Diabetes Prevention Program) |
| HFpEF with metabolic comorbidities | I50.32 + I10 + E66.01 + E11.9 | Heart failure management program |
