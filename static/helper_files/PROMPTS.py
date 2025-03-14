QUESTION_GENERATION_PROMPT = '''
# Clinical Assessment Question Generator

## Instructions

Based on the provided patient data, generate essential diagnostic questions that should be asked during clinical assessment. These questions should:

1. Target a deeper understanding of the patient's presenting symptoms
2. Explore potential etiologies for the clinical presentation
3. Be concise and clinically relevant (prioritize high-yield questions only)

## Output Requirements

Your response must strictly adhere to the following JSON format:

```json
{
  "content": [
    "Question 1?",
    "Question 2?",
    "Question 3?"
  ]
}
```

## Important Notes

- Focus on clinical efficiency - generate only the minimum number of questions necessary for comprehensive assessment
- Ensure questions follow standard clinical interviewing practices
- The questions should be directly relevant to the patient data provided
'''

DIFFERENTIAL_DIAGONOSIS_GENERATION_PROMPT = """# Clinical Differential Diagnosis Template

## Instructions

Generate a comprehensive differential diagnosis based on the provided patient information. Follow the exact structure below.

## Patient Information
- **Name:** 
- **Age:** 
- **Gender:** 
- **Main Symptoms:** 
- **Past Medical History:** 
- **Known Medical Conditions:** 
- **Current Medications:**
- **Country:**

## Differential Diagnosis

### 1. [DISEASE NAME] ([PROBABILITY PERCENTAGE]%)
**Reasoning:**
- **Present Symptoms:**
  - [Symptom 1]
  - [Symptom 2]
  - [Additional symptoms as relevant]

- **Symptoms Requiring Verification:** *(if applicable)*
  - [Symptom 1]
  - [Symptom 2]

**Relevant History or Examination Findings:** *(Only if applicable)*
- [Detail 1]
- [Detail 2]

**Recommended Medications:**
- Name: [Name of the Drug]
    - Use: [Purpose of the Drug]
    - Dosage: [Dosage Instructions and Efficacy of the Drug]
    - Known Side Effects: [List of known side effects of the provided medications (only if there are any side effects)]
    - Efficacy of the drug.
(repeat this pattern for each prescribed medicine)

- Therapy/Procedures: [List of Recommended Therapies/Procedures]

**Diagnostic Tests:** *(Only if applicable)*
- [Test 1]
- [Test 2]

**Home Remedies:** *(Only if applicable)*
- [Strategy 1]
- [Strategy 2]

### 2. [DISEASE NAME] ([PROBABILITY PERCENTAGE]%)
*(Repeat the above structure)*

*(Continue with additional conditions up to 10 total, prioritizing those with highest probability based on clinical presentation)*

---

**DISCLAIMER: This information is provided for educational purposes only. Do not take any medication or implement treatment without consulting a qualified healthcare professional.**"""

