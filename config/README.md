# Configuration Directory

This directory contains profile-based configuration for the text anonymization engine. Profiles allow you to customize which entities are detected and how they are handled.

## Overview

- **Profiles**: Located in subdirectories (e.g., `config/default/`, `config/example/`). Each profile contains configuration files that control anonymization behavior.
- **Entity Detection**: Uses GLiNER (NER) for named-entity recognition and configurable regex patterns for specialized identifiers (like Finnish HETU numbers).
- **Entity Mapping**: Output labels are mapped via `label_mappings.txt` to produce consistent anonymized text (e.g., `PHONE_NUMBER` → `PUHELINNUMERO`).

## Configuration Files

### Global Configuration

**`label_mappings.txt`** (root of `config/` directory)

Maps internal entity labels to output labels shown in anonymized text. Format: `INPUT_LABEL=OUTPUT_LABEL`

Example:
```
PHONE_NUMBER=PUHELINNUMERO
EMAIL=SÄHKÖPOSTI
FI_HETU=HETU
PERSON=NIMI
```

### Profile-Specific Files

Each profile directory (e.g., `config/default/`, `config/example/`) can contain:

### Word list for blocked words - blocklist.txt

Words that **must always be anonymized**. Matches are case-insensitive and word-boundary aware.

- One word or phrase per line
- Matched words are replaced with `<MUU_TUNNISTE>` (generic identifier)
- Example: if "Matti" is in blocklist, "Matti" will be anonymized even if GLiNER doesn't detect it as a person name

### Word list for always unprocessed words - grantlist.txt

Words that **should never be anonymized** (allowlist/protection list). Protects words even if GLiNER or regex patterns match them.

- One word or phrase per line
- Useful for protecting company names, brand names, or common words that may be falsely flagged
- Example: if "Microsoft" is in grantlist, it won't be anonymized even if detected as an organization

### Configuration file for regular expression patterns - regex_patterns.txt

Custom regex patterns for entity detection. Useful for domain-specific or language-specific identifiers.

**Format** (one per line):
```
ENTITY_NAME: regex_pattern
```

- `ENTITY_NAME`: Uppercase identifier (e.g., `FI_HETU`, `FI_PUHELIN`, `EMAIL`)
- `regex_pattern`: A Python-compatible regex pattern
- Multiple lines can use the same `ENTITY_NAME` (all matches are collected)
- Lines starting with `#` are treated as comments and ignored
- Regex matches have perfect confidence (score 1.0) and take priority over GLiNER matches

**Example `regex_patterns.txt`:**
```
# Finnish Social Security Number (HETU)
# Format: DDMMYY-XXXY (e.g., 311299-999A)
FI_HETU: \b([0-3][0-9][0-1][0-9][0-9]{2})([-+A])([0-9]{3})([A-Za-z0-9])\b

# Finnish phone numbers
# Formats: +358401234567, 040-1234567, 09 123 4567
FI_PUHELIN: \b\+?358\s?[0-9]{1,2}\s?[0-9]{3,4}\s?[0-9]{3,4}\b
FI_PUHELIN: \b0[0-9]{1,2}[\s-]?[0-9]{2,7}\b

# Email addresses
EMAIL: \b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b
```

### Configuration file for NER labels - gliner_labels.txt (optional)

Specifies which GLiNER labels to use for this profile. Format: one label per line.

- If this file exists, only the listed labels are used for GLiNER detection
- If absent, the default GLiNER labels are used
- Labels should be in the normalized form used by the model (e.g., `person`, `phone number`, `email`)
- Example content:
  ```
  person
  phone number
  email
  address
  ```

## GLiNER Supported Labels

The project uses GLiNER for named-entity recognition. Supported labels include:

**Common PII labels:** person, organization, phone number, email, address, email address

**Financial/ID labels:** credit card number, social security number, passport number, driver's license number, national id number, iban, bank account number, identity card number

**Healthcare labels:** health insurance id number, health insurance number, medical condition, medication, blood type

**Other labels:** date of birth, ip address, username, registration number, student id number, insurance number, flight number, license plate number, postal code, serial number, vehicle registration number, credit card brand, fax number, cvv, cvc, transaction number, and more

For a complete reference, see the root `README.md` section on GLiNER labels.

## Configuration Profiles

### Default Profile (`config/default/`)

The profile used when no profile is explicitly specified. Contains regex patterns for common Finnish identifiers:

- `FI_HETU` - Finnish social security numbers
- `FI_PUHELIN` - Finnish phone numbers
- `FI_REKISTERI` - Finnish vehicle registration plates
- `FI_KIINTEISTO` - Finnish property identifiers
- `TIEDOSTO` - File names and URLs
- `EMAIL` - Email addresses (via regex)

### Example Profile (`config/example/`)

Demonstrates profile configuration options. Use as a template for custom profiles.

### Creating a Custom Profile

1. Create a new directory: `config/myprofile/`
2. Add any combination of the configuration files (`blocklist.txt`, `grantlist.txt`, `regex_patterns.txt`, `gliner_labels.txt`)
3. Use the profile in code or API calls

## Usage Examples

### Python Library


# Default Profile Configuration

The default profile includes the following regex patterns:

**EMAIL**

1. `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b`

**FI_HETU**

1. `\b([0-3][0-9][0-1][0-9][0-9]{2})([-+A])([0-9]{3})([a-zA-Z0-9])\b`
2. `\b([0-3][0-9][0-1][0-9][0-9]{2})([-+A])\b`

**FI_KIINTEISTO**

1. `\b[0-9]{1,3}-[0-9]{1,3}-[0-9]{1,4}-[0-9]{1,4}\b`
2. `\b[0-9]{1,3}-[0-9]{1,3}-[0-9]{1,4}-[0-9]{1,4}-[0-9A-Za-z]{1,4}\b`

**FI_PUHELIN**

 `\+358\s?\(0\)\s?[0-9]{1,2}\s?[0-9]{3,4}\s?[0-9]{3,4}` - International with (0)
2. `\+358\s[0-9]{1,2}\s[0-9]{3,4}\s?[0-9]{3,4}` - International with space
3. `\+358\s?[0-9]{1,2}\s?[0-9]{6,8}` - International compact
4. `\b0[1-9][0-9]?[\s-][0-9]{4,9}\b` - Local with single separator
5. `\b0[1-9][0-9]{0,2}\s[0-9]{3,4}\s[0-9]{3,4}\b` - Local with multiple spaces
6. `\b0[1-9][0-9]{7,9}\b` - Local without separator
7. `\(0[1-9][0-9]?\)\s?[0-9]{5,8}` - Organization with parentheses

**FI_REKISTERI**

1. `\b[A-Z]{3}-[0-9]{3}\b`
2. `\b[A-Z]{2}-[0-9]{3}\b`
3. `\b[A-Z]{2}-[0-9]{4}\b`

**TIEDOSTO**

1. `\b\w+\.(txt|doc|docx|xls|xlsx|pdf|jpg|jpeg|png|gif|ppt|pptx|zip|rar|csv)\b`
2. `https?://[A-Za-z0-9%-_./]+\.(txt|doc|docx|xls|xlsx|pdf|jpg|jpeg|png|gif|ppt|pptx|zip|rar|csv)\b`


# Label Mappings

The following shows how internal labels are mapped to output labels:

| Internal Label | Output Label |
| --- | --- |
| ADDRESS | OSOITE |
| CREDIT_CARD_NUMBER | LUOTTOKORTTI |
| DATE_OF_BIRTH | SYNTYMÄAIKA |
| DRIVER'S_LICENSE_NUMBER | AJOKORTTI |
| EMAIL | SÄHKÖPOSTI |
| FI_HETU | HETU |
| FI_KIINTEISTO | KIINTEISTÖ |
| FI_PUHELIN | PUHELIN |
| FI_REKISTERI | REKISTERI |
| IBAN | TILINUMERO |
| IP_ADDRESS | IP_OSOITE |
| LICENSE_PLATE_NUMBER | REKISTERINUMERO |
| MUU_TUNNISTE | TUNNISTE |
| NATIONAL_ID_NUMBER | HENKILÖLLISYYSTODISTUS |
| ORGANIZATION | ORGANISAATIO |
| PASSPORT_NUMBER | PASSI |
| PERSON | NIMI |
| PHONE_NUMBER | PUHELINNUMERO |
| SOCIAL_SECURITY_NUMBER | HENKILÖTUNNUS |
| TIEDOSTO | TIEDOSTO |
| USERNAME | KÄYTTÄJÄTUNNUS |


# GLiNER Labels Usage

To use GLiNER labels, append the `_ner` suffix to the label name.

Example GLiNER labels that can be requested:

| Label | Description |
| --- | --- |
| person_ner | Detect person names |
| organization_ner | Detect organization names |
| phone_number_ner | Detect phone numbers |
| email_ner | Detect email addresses |
| address_ner | Detect addresses |
| social_security_number_ner | Detect social security numbers |
| credit_card_number_ner | Detect credit card numbers |
| date_of_birth_ner | Detect dates of birth |


# Regex Patterns Usage

To use regex patterns from the profile, append the `_regex` suffix.

Available regex patterns in default profile:

| Label | Entity Type |
| --- | --- |
| email_regex | EMAIL |
| fi_hetu_regex | FI_HETU |
| fi_iban_regex | FI_IBAN |
| fi_kiinteisto_regex | FI_KIINTEISTO |
| fi_puhelin_regex | FI_PUHELIN |
| fi_rekisteri_regex | FI_REKISTERI |
| tiedosto_regex | TIEDOSTO |


# Basic Usage Examples

## Example 1: Anonymize with default settings

Anonymizes text using all default detectors (GLiNER + regex patterns).

```python
from text_anonymizer import TextAnonymizer

anonymizer = TextAnonymizer()
text = "Matti Meikäläinen, HETU: 311299-999A, puhelin: 040-1234567"
result = anonymizer.anonymize(text)

print(f"Original: {text}")
print(f"Anonymized: {result.anonymized_text}")
print(f"Summary: {result.summary}")
```

**Output:**
```
Original: Matti Meikäläinen, HETU: 311299-999A, puhelin: 040-1234567
Anonymized: <NIMI>, HETU: <HETU>, puhelin: <PUHELIN>
Summary: {'NIMI': 1, 'HETU': 1, 'PUHELIN': 1}
```

## Example 2: Only detect specific regex patterns

Anonymizes only HETU numbers, ignoring other entities.

```python
from text_anonymizer import TextAnonymizer

anonymizer = TextAnonymizer()
text = "Matti Meikäläinen, HETU: 311299-999A, puhelin: 040-1234567"
result = anonymizer.anonymize(text, labels=['fi_hetu_regex'])

print(f"Original: {text}")
print(f"Anonymized: {result.anonymized_text}")
print(f"Summary: {result.summary}")
```

**Output:**
```
Original: Matti Meikäläinen, HETU: 311299-999A, puhelin: 040-1234567
Anonymized: Matti Meikäläinen, HETU: <HETU>, puhelin: 040-1234567
Summary: {'HETU': 1}
```

## Example 3: Mix GLiNER and regex labels

Combine GLiNER person detection with regex-based phone numbers.

```python
from text_anonymizer import TextAnonymizer

anonymizer = TextAnonymizer()
text = "Matti Meikäläinen, HETU: 311299-999A, puhelin: 040-1234567"
result = anonymizer.anonymize(text, labels=['person_ner', 'fi_puhelin_regex'])

print(f"Original: {text}")
print(f"Anonymized: {result.anonymized_text}")
print(f"Summary: {result.summary}")
```

**Output:**
```
Original: Matti Meikäläinen, HETU: 311299-999A, puhelin: 040-1234567
Anonymized: <NIMI>, HETU: 311299-999A, puhelin: <PUHELIN>
Summary: {'NIMI': 1, 'PUHELIN': 1}
```

## Example 4: Use a custom profile

Use a specific profile with custom blocklist/grantlist. Let's assume that word "MicroCorpSoft" is in the blocklist of the `example` profile.

```python
from text_anonymizer import TextAnonymizer

anonymizer = TextAnonymizer()
text = "Matti Meikäläinen from MicroCorpSoft"
result = anonymizer.anonymize(text, profile='example')

print(f"Original: {text}")
print(f"Anonymized: {result.anonymized_text}")
print(f"Summary: {result.summary}")
```

**Output:**
```
Original: Matti Meikäläinen, Microsoft
Anonymized: <NIMI>, <MUU_TUNNISTE>
Summary: {'NIMI': 1, 'MUU_TUNNISTE': 1}
```



```python
from text_anonymizer import TextAnonymizer

anonymizer = TextAnonymizer()
text = "Matti Meikäläinen, HETU: 311299-999A, puhelin: 040-1234567, email: matti@example.com"

# Use default profile (all configured patterns applied)
# Note: profile='default' is the default and can be omitted
result = anonymizer.anonymize(text)
# Output: NIMI anonymized, HETU, PUHELIN, SÄHKÖPOSTI anonymized

# Use default profile but only anonymize HETU via regex
# The default profile can be omitted
result = anonymizer.anonymize(text, labels=['fi_hetu_regex'])
# Output: Only HETU anonymized

# Use a specific profile
result = anonymizer.anonymize(text, profile='example')

# Request specific GLiNER labels (using default profile implicitly)
result = anonymizer.anonymize(text, labels=['person_ner', 'phone_number_ner'])
# Output: Only person names and phone numbers anonymized

# Mix GLiNER and regex labels (using default profile implicitly)
result = anonymizer.anonymize(text, labels=['person_ner', 'fi_hetu_regex'])
# Output: Person names (via GLiNER) and HETU (via regex) anonymized
```

**Label suffixes:**
- `_ner` suffix: Request GLiNER/NER label (e.g., `person_ner`, `phone_number_ner`)
- `_regex` suffix: Request regex pattern from profile (e.g., `fi_hetu_regex`, `fi_puhelin_regex`)
- Unsuffixed: Treated as GLiNER labels for backward compatibility

### REST API

```bash
# Anonymize text with default settings
curl -X POST 'http://localhost:8000/anonymize' \
  -H 'Content-Type: application/json' \
  -d '{"text": "Matti Meikäläinen"}'

# Explicitly specify default profile (equivalent to above)
curl -X POST 'http://localhost:8000/anonymize' \
  -H 'Content-Type: application/json' \
  -d '{"text": "Matti Meikäläinen", "profile": "default"}'

# Use specific labels with default profile (profile can be omitted)
curl -X POST 'http://localhost:8000/anonymize' \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Matti Meikäläinen, HETU: 311299-999A",
    "labels": ["person_ner", "fi_hetu_regex"]
  }'

# Use a custom profile
curl -X POST 'http://localhost:8000/anonymize' \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Matti Meikäläinen",
    "profile": "example"
  }'
  
# Use a nonexistent profile
curl -X POST 'http://localhost:8000/anonymize' \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Matti Meikäläinen",
    "profile": "this_profile_does_not_exist"
  }'
```

## Implementation Notes

- **Regex Priority:** Regex patterns (with score 1.0) take priority over GLiNER matches when entities overlap.
- **Label Mapping:** All detected entity labels are mapped through `config/label_mappings.txt` before output. If a label is not in the mapping, it is used as-is (uppercased).
- **Case Sensitivity:** Blocklist and grantlist matching is case-insensitive; regex patterns are case-sensitive unless specified otherwise in the pattern.
- **Profile Fallback:** When no profile is specified or a file doesn't exist in the profile, the anonymizer uses defaults gracefully.

## Troubleshooting

- **Regex patterns not matching:** Use an online Python regex tester to verify patterns. Remember backslashes need to be literal in `.txt` files.
- **Labels not recognized:** Ensure the label format is correct (`person_ner` for GLiNER, `fi_hetu_regex` for regex). Check `label_mappings.txt` for valid output labels.
- **Words not being anonymized:** Check `blocklist.txt` and ensure no contradicting `grantlist.txt` entries. Verify the profile is being loaded correctly (enable `debug_mode=True` for diagnostic output).
- **Profile not found:** Verify the profile directory exists under `config/` and contains at least one configuration file.

## Creating custom patterns


## Test a specific regex pattern

```python
import re

# Test HETU pattern
hetu_pattern = r"\b([0-3][0-9][0-1][0-9][0-9]{2})([-+A])([0-9]{3})([A-Za-z0-9])\b"
test_text = "My HETU is 311299-999A"

matches = re.finditer(hetu_pattern, test_text)
for match in matches:
    print(f"Found: {match.group()} at position {match.start()}-{match.end()}")
```


