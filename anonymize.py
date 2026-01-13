from text_anonymizer import TextAnonymizer
import sys

#TODO: TESTS, DOCUMENT, PACKAGE, COMMENTS

text_anonymizer = TextAnonymizer()
for line in sys.stdin:
    text = line
    anonymized = text_anonymizer.anonymize_text(text)
    print(anonymized)