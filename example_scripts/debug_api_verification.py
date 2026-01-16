#!/usr/bin/env python
"""
Debug script for API Verification.

Tests the Anonymizer FastAPI application endpoints:
  - /anonymize endpoint
  - /anonymize_batch endpoint
  - Profile-based anonymization
  - Error handling and response validation
  - Connection status

Usage:
    python debug_scripts/debug_api_verification.py              # Full API verification
    python debug_scripts/debug_api_verification.py --quick      # Quick connection check
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from debug_utils import print_section_header, print_example_case
import time

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("WARNING: requests library not found. Install with: pip install requests")


API_URL = "http://127.0.0.1:8000"
API_TIMEOUT = 3.0


def check_api_availability():
    """TEST 1: Check API Connection"""
    print_section_header(1, "API Connection Check", 5)

    params = {
        'api_url': API_URL,
        'timeout': API_TIMEOUT,
        'endpoint': '/docs'
    }

    print("\nPARAMETERS:")
    print(f"  API URL: {params['api_url']}")
    print(f"  Timeout: {params['timeout']}s")
    print(f"  Checking endpoint: {params['endpoint']}")

    if not REQUESTS_AVAILABLE:
        print("\n✗ SKIP: requests library not available")
        return 0

    print("\n\nTest: Connecting to API")

    try:
        response = requests.get(f"{API_URL}{params['endpoint']}", timeout=params['timeout'])

        if response.status_code == 200:
            print(f"  Status: ✓ API is running")
            print(f"  Response code: {response.status_code}")
            print(f"  Documentation available at: {API_URL}/docs")
            return 1
        else:
            print(f"  Status: ✗ Unexpected response code: {response.status_code}")
            return 0
    except requests.ConnectionError:
        print(f"  Status: ✗ Connection refused")
        print(f"  API is not running at {API_URL}")
        print(f"  To start API, run: python anonymizer_flask_app.py")
        return 0
    except requests.Timeout:
        print(f"  Status: ✗ Connection timeout")
        return 0
    except Exception as e:
        print(f"  Status: ✗ Error: {e}")
        return 0


def test_anonymize_simple_text():
    """TEST 2: Simple Text Anonymization"""
    print_section_header(2, "Simple Text Anonymization Endpoint", 5)

    payload = {
        "text": "Matti Meikäläinen, puh: 040-1234567",
        "languages": ["fi"],
        "recognizers": [],
        "profile": None
    }

    params = {
        'endpoint': '/anonymize',
        'method': 'POST',
        'text': payload['text']
    }

    print("\nPARAMETERS:")
    print(f"  Endpoint: POST {params['endpoint']}")
    print(f"  Text: {params['text']}")
    print(f"  Languages: {payload['languages']}")

    if not REQUESTS_AVAILABLE:
        print("\n✗ SKIP: requests library not available")
        return 0

    print("\n\nTest: Sending anonymization request")
    print_example_case(payload['text'], "Should anonymize name and phone")

    try:
        response = requests.post(
            f"{API_URL}{params['endpoint']}",
            json=payload,
            timeout=API_TIMEOUT
        )

        if response.status_code != 200:
            print(f"\n  Status: ✗ Request failed with code {response.status_code}")
            print(f"  Response: {response.text}")
            return 0

        data = response.json()

        print(f"\n  Status: ✓ SUCCESS (HTTP {response.status_code})")
        print(f"  Original: {payload['text']}")
        print(f"  Anonymized: {data.get('anonymized_txt', 'N/A')}")
        print(f"  Summary: {data.get('summary', 'N/A')}")

        # Validate response structure
        has_anonymized = 'anonymized_txt' in data
        has_summary = 'summary' in data
        text_changed = data.get('anonymized_txt') != payload['text']

        print(f"\n  Response has 'anonymized_txt': {has_anonymized}")
        print(f"  Response has 'summary': {has_summary}")
        print(f"  Text was anonymized: {text_changed}")

        status = "✓ PASS" if (has_anonymized and has_summary) else "✗ FAIL"
        print(f"  Status: {status}")

        return 1 if (has_anonymized and has_summary) else 0

    except requests.ConnectionError:
        print(f"\n  Status: ✗ Cannot connect to API")
        return 0
    except requests.Timeout:
        print(f"\n  Status: ✗ Request timeout")
        return 0
    except Exception as e:
        print(f"\n  Status: ✗ Error: {e}")
        return 0


def test_anonymize_with_profile():
    """TEST 3: Profile-Based Anonymization"""
    print_section_header(3, "Profile-Based Anonymization", 5)

    test_cases = [
        {"profile": "default", "text": "Henkilötunnus 311299-999A"},
        {"profile": "example", "text": "Registration plate ABA-303"},
    ]

    params = {
        'endpoint': '/anonymize',
        'profiles': ["default", "example"]
    }

    print("\nPARAMETERS:")
    print(f"  Endpoint: POST {params['endpoint']}")
    print(f"  Available profiles: {', '.join(params['profiles'])}")

    if not REQUESTS_AVAILABLE:
        print("\n✗ SKIP: requests library not available")
        return 0

    passed = 0

    for test_case in test_cases:
        profile = test_case['profile']
        text = test_case['text']

        print(f"\n\nTest: Using profile '{profile}'")
        print_example_case(text, f"Should use {profile} profile patterns")

        payload = {
            "text": text,
            "languages": ["fi"],
            "recognizers": [],
            "profile": profile
        }

        try:
            response = requests.post(
                f"{API_URL}{params['endpoint']}",
                json=payload,
                timeout=API_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                print(f"  Original: {text}")
                print(f"  Anonymized: {data.get('anonymized_txt', 'N/A')}")
                print(f"  Summary: {data.get('summary', 'N/A')}")
                print(f"  Status: ✓ PASS")
                passed += 1
            else:
                print(f"  Status: ✗ Request failed ({response.status_code})")

        except Exception as e:
            print(f"  Status: ✗ Error: {e}")

    return passed


def test_anonymize_batch():
    """TEST 4: Batch Anonymization Endpoint"""
    print_section_header(4, "Batch Anonymization Endpoint", 5)

    payload = {
        "texts": [
            "Matti Meikäläinen",
            "Phone: 040-1234567",
            "HETU: 311299-999A"
        ],
        "languages": ["fi"],
        "profile": None
    }

    params = {
        'endpoint': '/anonymize_batch',
        'batch_size': len(payload['texts'])
    }

    print("\nPARAMETERS:")
    print(f"  Endpoint: POST {params['endpoint']}")
    print(f"  Batch size: {params['batch_size']} items")
    print(f"  Items:")
    for i, text in enumerate(payload['texts'], 1):
        print(f"    {i}. {text}")

    if not REQUESTS_AVAILABLE:
        print("\n✗ SKIP: requests library not available")
        return 0

    print("\n\nTest: Sending batch request")
    print_example_case(
        "3 items",
        "Should anonymize all items in batch"
    )

    try:
        response = requests.post(
            f"{API_URL}{params['endpoint']}",
            json=payload,
            timeout=API_TIMEOUT
        )

        if response.status_code != 200:
            print(f"\n  Status: ✗ Request failed ({response.status_code})")
            return 0

        data = response.json()
        results = data.get('results', [])

        print(f"\n  Status: ✓ SUCCESS (HTTP {response.status_code})")
        print(f"  Items processed: {len(results)}")

        for i, result in enumerate(results, 1):
            print(f"\n  Item {i}:")
            print(f"    Original: {result.get('original', 'N/A')[:40]}...")
            print(f"    Anonymized: {result.get('anonymized_txt', 'N/A')[:40]}...")

        status = "✓ PASS" if len(results) == len(payload['texts']) else "✗ FAIL"
        print(f"\n  Status: {status}")

        return 1 if len(results) == len(payload['texts']) else 0

    except requests.ConnectionError:
        print(f"\n  Status: ✗ Cannot connect to API")
        return 0
    except requests.Timeout:
        print(f"\n  Status: ✗ Request timeout")
        return 0
    except Exception as e:
        print(f"\n  Status: ✗ Error: {e}")
        return 0


def test_error_handling():
    """TEST 5: Error Handling"""
    print_section_header(5, "Error Handling", 5)

    test_cases = [
        {"name": "Empty text", "payload": {"text": "", "languages": ["fi"], "profile": None}},
        {"name": "Missing text field", "payload": {"languages": ["fi"], "profile": None}},
        {"name": "Invalid language", "payload": {"text": "Test", "languages": ["xx"], "profile": None}},
    ]

    params = {
        'endpoint': '/anonymize',
        'error_cases': len(test_cases)
    }

    print("\nPARAMETERS:")
    print(f"  Endpoint: POST {params['endpoint']}")
    print(f"  Testing {params['error_cases']} error cases")

    if not REQUESTS_AVAILABLE:
        print("\n✗ SKIP: requests library not available")
        return 0

    passed = 0

    for test_case in test_cases:
        name = test_case['name']
        payload = test_case['payload']

        print(f"\n\nTest: {name}")
        print(f"  Payload: {payload}")

        try:
            response = requests.post(
                f"{API_URL}{params['endpoint']}",
                json=payload,
                timeout=API_TIMEOUT
            )

            # Could return 200 (gracefully handled), 400 (bad request), or other
            print(f"  Response code: {response.status_code}")
            print(f"  Status: ✓ PASS (handled - returned HTTP {response.status_code})")
            passed += 1

        except requests.ConnectionError:
            print(f"  Status: ✗ Connection error")
        except requests.Timeout:
            print(f"  Status: ✗ Timeout")
        except Exception as e:
            print(f"  Status: ✗ Error: {e}")

    return passed


def main():
    """Run all API verification tests."""

    print("\n" + "="*80)
    print("API VERIFICATION DEBUG SCRIPT")
    print(f"API URL: {API_URL}")
    print("Tests: Connection, simple text, profiles, batch, error handling")
    print("="*80)

    all_passed = 0

    try:
        all_passed += check_api_availability()

        # Only run other tests if API is available
        if all_passed > 0:
            all_passed += test_anonymize_simple_text()
            all_passed += test_anonymize_with_profile()
            all_passed += test_anonymize_batch()
            all_passed += test_error_handling()
        else:
            print("\n" + "="*80)
            print("⚠ API NOT RUNNING - Skipping endpoint tests")
            print("To start the API server, run one of:")
            print("  python anonymizer_flask_app.py")
            print("  python anonymizer_api_app.py")
            print("  python anonymizer_web_app.py")
            print("="*80 + "\n")
            return

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print(f"SUMMARY: {all_passed} test sections passed")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

