# Debug Scripts

Standalone scripts for verifying anonymizer functionality without pytest. Run from project root.

## Usage

```bash
python debug_scripts/debug_ner_core.py           # NER: person, address, location, email
python debug_scripts/debug_regex_finnish.py      # Finnish: HETU, phone, IBAN, plates
python debug_scripts/debug_regex_general.py      # General: email, filename patterns
python debug_scripts/debug_gliner_controls.py    # Controls: labels, thresholds, profiles
python debug_scripts/debug_label_mappings.py     # Label mapping verification
python debug_scripts/debug_edge_cases.py         # Edge cases and error handling
python debug_scripts/debug_api_verification.py   # API endpoints (requires server)
```

## Scripts

| Script | Purpose | Mirrors |
|--------|---------|---------|
| `debug_ner_core.py` | Person, address, location, email NER | `test_ner_person_recognizer.py`, `test_ner_location_recognizer.py` |
| `debug_regex_finnish.py` | HETU, phone, IBAN, property ID, plates | `test_regex_finnish_identifiers.py` |
| `debug_regex_general.py` | Email, filename patterns | `test_regex_general_patterns.py` |
| `debug_gliner_controls.py` | Labels, thresholds, profiles, blocklist | `test_ner_gliner_controls.py` |
| `debug_label_mappings.py` | Config label mappings | `test_ner_gliner_controls.py` |
| `debug_edge_cases.py` | Unicode, long text, malformed input | `test_util_text_anonymizer.py` |
| `debug_api_verification.py` | API endpoints | `test_api_app.py` |
| `debug_utils.py` | Shared utilities (imported by others) | - |

## Troubleshooting

- **Module not found**: Run from project root directory
- **API connection refused**: Start server first with `python anonymizer_flask_app.py`
- **Slow first run**: GLiNER model loads on first use (~2-3s)

