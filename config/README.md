# Configuration Directory

This directory contains profile-based configuration for text anonymization.

## Profile Structure

Each profile is a subdirectory with the following optional files:

- `blocklist.txt` - Words to always anonymize (one per line)
- `grantlist.txt` - Words to protect from anonymization (one per line)
- `regex_patterns.txt` - Custom regex patterns (format: `ENTITY_NAME: pattern`)

## Example Profile

The `example` profile demonstrates all configuration options:

### blocklist.txt
Words listed here will be detected and anonymized as `<MUU_TUNNISTE>`.

### grantlist.txt
Words listed here will be protected and never anonymized, even if detected by GLiNER or other recognizers.

### regex_patterns.txt
Custom regex patterns to detect specific entity types. Format:
```
ENTITY_NAME: regex_pattern
```

Multiple patterns can use the same ENTITY_NAME.

## Creating a New Profile

1. Create a new directory: `config/myprofile/`
2. Add any combination of the three config files
3. Use the profile in API calls with `"profile": "myprofile"`

## Usage

```python
# Without profile
result = anonymizer.anonymize("Some text")

# With profile
result = anonymizer.anonymize("Some text", profile="example")
```

In API requests:
```json
{
  "text": "Some text to anonymize",
  "languages": ["fi"],
  "profile": "example"
}
```

