"""
Command-line tool for anonymizing text files.

Usage:
    python anonymize_txt.py input.txt output.txt --debug=true

Options:
    --source_file: Input text file
    --target_file: Output text file (anonymized)
    --debug: Enable debug logging (true/false, default: false)
    --languages: Comma-separated language codes (default: fi,en)
    --encoding: Source and target file encoding (default: UTF-8)
    --separator: String separator for document boundaries (default: none)
    --profile: Profile name for configuration (default: default)
    --threshold: GLiNER confidence threshold 0.0-1.0 (default: 0.6)
"""

import argparse

from text_anonymizer import TextAnonymizer

def main():

    parser = argparse.ArgumentParser(
        description='Anonymize txt file',
        epilog="Example: python anonymize_txt.py file_in.txt file_out.txt --debug=true"
    )
    parser.add_argument('source_file', type=str, help='Text file to be anonymized')
    parser.add_argument('target_file', type=str, help='Name or path of (anonymized) destination file.')
    parser.add_argument('--debug', type=str, help='Toggle debug logging. Shows scores within labels. (true/false, default: false)')
    parser.add_argument('--encoding', type=str, help='Source encoding. Default: UTF-8')
    parser.add_argument('--separator', type=str, help='String separator for newlines. Default: None')
    parser.add_argument('--profile', type=str, help='Profile name for configuration. Default: default')
    parser.add_argument('--threshold', type=float, help='GLiNER confidence threshold (0.0-1.0). Default: 0.6')
    parser.add_argument('--labels', type=str, help='Entity labels to detect (comma-separated). Default: use profile defaults')

    debug = False

    args = parser.parse_args()
    source_encoding = 'UTF-8'
    source_file = None
    target_file = None
    separator = None
    profile = 'default'
    threshold = 0.6
    labels = None

    if args.source_file:
        source_file = args.source_file
    if args.target_file:
        target_file = args.target_file
    if args.debug and "true" == args.debug.lower():
        debug = True
    if args.encoding:
        source_encoding = args.encoding
    if args.separator:
        separator = args.separator
    if args.profile:
        profile = args.profile
    if args.threshold:
        threshold = args.threshold
    if args.labels:
        labels = args.labels.split(',') if args.labels else None

    print("Anonymizing file: {i}. ".format(i=source_file))

    print("")
    print("Parameters:")
    print("- Source file: {s}".format(s=source_file))
    print("- Target file: {s}".format(s=target_file))
    print("- Debug mode: {s}".format(s=debug))
    print("- Profile: {s}".format(s=profile))
    print("- Threshold: {s}".format(s=threshold))
    if labels:
        print("- Labels: {s}".format(s=labels))
    print("")

    text_anonymizer = TextAnonymizer(debug_mode=debug)
    statistics = []
    details = []

    def anonymize(doc: [str]) -> (str, object, object):
        """
        Anonymize a document (list of lines) and return results.

        Args:
            doc: List of text lines

        Returns:
            Tuple of (anonymized_text, summary_stats, entity_details)
        """
        a = ' '.join(doc)
        if a:
            result = text_anonymizer.anonymize(
                a,
                labels=labels,
                profile=profile,
                gliner_threshold=threshold
            )
            return result.anonymized_text, result.summary, result.details
        return None, None, None

    def prepare_raw_text(line):
        """Remove excessive whitespace from text line."""
        import re
        line = re.sub(r'\s+', ' ', line)
        return line

    if source_file:
        try:
            # use same encoding for source and target file
            with open(target_file, mode='w+', newline='', encoding=source_encoding) as outfile:
                with open(source_file, mode='r', newline='', encoding=source_encoding) as in_file:
                    lines = in_file.readlines()
                    doc = []
                    newline_counter = 0
                    line_counter = 0

                    for line in lines:
                        line_counter += 1
                        if line != '\n':
                            # remove double spaces etc
                            prepared = prepare_raw_text(line)
                            doc.append(prepared)
                        else:
                            newline_counter += 1

                        if newline_counter >= 2 or line_counter >= len(lines):
                            newline_counter = 0
                            anonymized, stats, detail = anonymize(doc)
                            if anonymized:
                                anonymized = ' '.join(anonymized.split())
                                if stats:
                                    statistics.append(stats)
                                if detail:
                                    details.append(detail)
                                if debug:
                                    if doc:
                                        print('>>> Original: ')
                                        print(''.join(doc))
                                        print('>>> Anonymized: ')
                                        print(anonymized)
                                        print('---')
                            doc = []
                            if anonymized:
                                outfile.write(anonymized)
                                if separator:
                                    outfile.write("\n{separator}\n")
        except Exception as e:
            print("Error: ", e)
            if 'codec' in str(e):
                print("Hint: Possibly invalid encoding. Please check the encoding of the source file. Use --encoding=... option to set the correct encoding.")
            exit(-1)

    combined_stats = text_anonymizer.combine_statistics(statistics)
    combined_details = text_anonymizer.combine_details(details)
    print("Statistics: ", combined_stats)
    if debug:
        print("Details: ", combined_details)
    print("\nFinished. Wrote anonymized version to: "+target_file)

if __name__ == "__main__":
    main()