"""
Command-line tool for anonymizing text from stdin.

Usage:
    echo "My name is John and my phone is 050-123-4567" | python anonymize.py

    Or pipe from a file:
    python anonymize.py < input.txt > output.txt

Options can be passed via environment variables:
    GLINER_PROFILE (default: 'default')
    GLINER_THRESHOLD (default: 0.3)
    GLINER_LABELS (comma-separated, default: use profile defaults)
"""

from text_anonymizer import TextAnonymizer
import sys
import os

def main():
    # Get configuration from environment variables
    profile = os.getenv('GLINER_PROFILE', 'default')
    try:
        threshold = float(os.getenv('GLINER_THRESHOLD', '0.3'))
    except ValueError:
        threshold = 0.3

    labels_str = os.getenv('GLINER_LABELS')
    labels = labels_str.split(',') if labels_str else None

    # Initialize anonymizer
    text_anonymizer = TextAnonymizer()

    # Process each line from stdin
    try:
        for line in sys.stdin:
            text = line.rstrip('\n\r')  # Remove newline but preserve content
            if text:
                anonymized = text_anonymizer.anonymize_text(
                    text,
                    profile=profile,
                    labels=labels,
                    gliner_threshold=threshold
                )
                print(anonymized)
            else:
                print()  # Preserve empty lines
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error processing input: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
