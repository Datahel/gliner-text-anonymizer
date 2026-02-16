"""
Evaluation Suite for Text Anonymizer

This script evaluates the text anonymizer with three test categories:
1. Names - Should be anonymized (100 samples)
2. Addresses/Streets - Should be anonymized (100 samples)
3. Plain words - Should NOT be anonymized (100 samples)

Features:
- Single evaluation run with configurable sample sizes
- Threshold optimization mode to find optimal GLiNER threshold
- Detailed logging and results tables

Usage:
    # Single evaluation
    python evaluation_suite.py --iterations 100

    # Threshold optimization
    python evaluation_suite.py --optimize --thresholds 0.3,0.4,0.5,0.6,0.7

Output:
    - Summary table with accuracy metrics
    - Detailed lists of failed cases
    - Threshold optimization report (when --optimize is used)
"""

import argparse
import logging
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Optional

from text_anonymizer import TextAnonymizer
import test_util_text_anonymizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Container for evaluation results of a single test category."""
    test_name: str
    samples: int
    success_count: int
    partial_count: int
    failed_items: List[str]
    duration_seconds: float
    gliner_threshold: float = 0.6

    @property
    def accuracy(self) -> float:
        return round((self.success_count / self.samples) * 100, 2) if self.samples > 0 else 0.0

    @property
    def error_rate(self) -> float:
        return round(100.0 - self.accuracy - self.partial_rate, 2)

    @property
    def partial_rate(self) -> float:
        return round((self.partial_count / self.samples) * 100, 2) if self.samples > 0 else 0.0


@dataclass
class ThresholdResult:
    """Container for threshold optimization results."""
    threshold: float
    name_accuracy: float
    address_accuracy: float
    word_accuracy: float  # Higher is better (fewer false positives)
    total_duration: float

    @property
    def combined_score(self) -> float:
        """
        Combined score balancing anonymization accuracy and false positive rate.
        Names and addresses should be anonymized (higher accuracy = better).
        Words should NOT be anonymized (higher accuracy = fewer false positives = better).
        """
        # Weight: 40% names, 30% addresses, 30% false positives
        return round(0.4 * self.name_accuracy + 0.3 * self.address_accuracy + 0.3 * self.word_accuracy, 2)


def evaluate_names_with_threshold(
    iterations: int,
    gliner_threshold: float,
    anonymizer: Optional[TextAnonymizer] = None,
    verbose: int = 1
) -> EvaluationResult:
    """
    Evaluate anonymizer with generated names using specified threshold.
    Names SHOULD be anonymized - success means the name was properly anonymized.

    Args:
        verbose: 0 = silent, 1 = summary only, 2 = all details
    """
    if verbose >= 1:
        logger.info("Evaluating name anonymization: iterations=%d, threshold=%.2f", iterations, gliner_threshold)

    start_time = time.time()

    if anonymizer is None:
        anonymizer = TextAnonymizer(debug_mode=False)

    random_names = test_util_text_anonymizer.generate_full_names(iterations)

    success_count = 0
    partial_count = 0
    failed_items = []

    for name in random_names:
        anonymized = anonymizer.anonymize_text(name, gliner_threshold=gliner_threshold)
        success_start = anonymized.startswith('<')
        success_end = anonymized.endswith('>')

        if success_start and success_end:
            success_count += 1
            if verbose >= 2:
                print(f"  [SUCCESS] '{name}' -> '{anonymized}'")
        elif success_start or success_end:
            partial_count += 1
            if verbose >= 2:
                print(f"  [PARTIAL] '{name}' -> '{anonymized}'")
        else:
            failed_items.append(f"{name} -> {anonymized}")
            if verbose >= 2:
                print(f"  [FAILED ] '{name}' -> '{anonymized}'")

    duration = time.time() - start_time

    return EvaluationResult(
        test_name="Names",
        samples=iterations,
        success_count=success_count,
        partial_count=partial_count,
        failed_items=failed_items,
        duration_seconds=duration,
        gliner_threshold=gliner_threshold
    )


def evaluate_addresses_with_threshold(
    iterations: int,
    gliner_threshold: float,
    anonymizer: Optional[TextAnonymizer] = None,
    verbose: int = 1
) -> EvaluationResult:
    """
    Evaluate anonymizer with generated street addresses using specified threshold.
    Addresses SHOULD be anonymized - success means the address was properly anonymized.

    Success criteria:
    - Full success: No digits remain in output AND has anonymization label
    - Partial success: Has anonymization label but some digits remain
    - Failure: No anonymization label present

    Args:
        verbose: 0 = silent, 1 = summary only, 2 = all details
    """
    if verbose >= 1:
        logger.info("Evaluating address anonymization: iterations=%d, threshold=%.2f", iterations, gliner_threshold)

    start_time = time.time()

    if anonymizer is None:
        anonymizer = TextAnonymizer(debug_mode=False)

    random_streets = test_util_text_anonymizer.generate_streets(iterations)

    success_count = 0
    partial_count = 0
    failed_items = []

    for street in random_streets:
        anonymized = anonymizer.anonymize_text(street, gliner_threshold=gliner_threshold)

        has_label = '<' in anonymized and '>' in anonymized
        no_numbers = not any(char.isdigit() for char in anonymized)

        if has_label and no_numbers:
            # Full success: completely anonymized with no numbers remaining
            success_count += 1
            if verbose >= 2:
                print(f"  [SUCCESS] '{street}' -> '{anonymized}'")
        elif has_label:
            # Partial success: has label but some numbers remain
            partial_count += 1
            if verbose >= 2:
                print(f"  [PARTIAL] '{street}' -> '{anonymized}'")
        else:
            # Failure: no anonymization happened
            failed_items.append(f"{street} -> {anonymized}")
            if verbose >= 2:
                print(f"  [FAILED ] '{street}' -> '{anonymized}'")

    duration = time.time() - start_time

    return EvaluationResult(
        test_name="Addresses",
        samples=iterations,
        success_count=success_count,
        partial_count=partial_count,
        failed_items=failed_items,
        duration_seconds=duration,
        gliner_threshold=gliner_threshold
    )


def evaluate_words_with_threshold(
    iterations: int,
    gliner_threshold: float,
    anonymizer: Optional[TextAnonymizer] = None,
    verbose: int = 1
) -> EvaluationResult:
    """
    Evaluate anonymizer with plain words (false positive test) using specified threshold.
    Words should NOT be anonymized - success means the word was left intact.

    Args:
        verbose: 0 = silent, 1 = summary only, 2 = all details
    """
    if verbose >= 1:
        logger.info("Evaluating false positives (words): iterations=%d, threshold=%.2f", iterations, gliner_threshold)

    start_time = time.time()

    if anonymizer is None:
        anonymizer = TextAnonymizer(debug_mode=False)

    random_words = test_util_text_anonymizer.generate_words(iterations)

    success_count = 0
    failed_items = []

    for word in random_words:
        anonymized = anonymizer.anonymize_text(word, gliner_threshold=gliner_threshold)

        # Success = word was NOT anonymized (no angle brackets)
        if '<' not in anonymized:
            success_count += 1
            if verbose >= 2:
                print(f"  [SUCCESS] '{word}' -> '{anonymized}'")
        else:
            failed_items.append(f"{word} -> {anonymized}")
            if verbose >= 2:
                print(f"  [FAILED ] '{word}' -> '{anonymized}'")

    duration = time.time() - start_time

    return EvaluationResult(
        test_name="Words (no anonymize)",
        samples=iterations,
        success_count=success_count,
        partial_count=0,
        failed_items=failed_items,
        duration_seconds=duration,
        gliner_threshold=gliner_threshold
    )


def load_test_sentences(filepath: str = None) -> List[str]:
    """Load test sentences from file."""
    if filepath is None:
        # Default path relative to this file
        this_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(this_dir, "data", "testilauseet.txt")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    return lines


def find_placeholders(text: str) -> List[Tuple[int, int, str]]:
    """
    Find all placeholders in text and return their positions and types.

    Returns:
        List of (start, end, label_type) tuples, sorted by position
    """
    placeholders = []

    # Find all <LABEL> patterns
    pattern = r'<(NIMI|OSOITE)>'
    for match in re.finditer(pattern, text):
        placeholders.append((match.start(), match.end(), match.group(1)))

    return sorted(placeholders, key=lambda x: x[0])


def replace_placeholders_with_content(
    template: str,
    names: List[str],
    addresses: List[str]
) -> Tuple[str, List[Tuple[int, int, str, str]]]:
    """
    Replace placeholders with random content from appropriate sources.

    Works by replacing from end to start to avoid index shifting issues.

    Args:
        template: Text with <NIMI> and <OSOITE> placeholders
        names: List of names to use as replacements
        addresses: List of addresses to use as replacements

    Returns:
        Tuple of (filled_text, injected_entities)
        where injected_entities is list of (start, end, label_type, original_text)
    """
    placeholders = find_placeholders(template)

    if not placeholders:
        return template, []

    # Work backwards to avoid index shifting
    result = template
    injected_entities = []

    # Process in reverse order
    for start, end, label_type in reversed(placeholders):
        if label_type == 'NIMI':
            replacement = random.choice(names)
        elif label_type == 'OSOITE':
            replacement = random.choice(addresses)
        else:
            continue

        # Replace the placeholder
        result = result[:start] + replacement + result[end:]

    # Now find the positions in the final text by processing forward
    # Re-parse to get actual positions after all replacements
    result = template
    current_offset = 0

    for start, end, label_type in placeholders:
        if label_type == 'NIMI':
            replacement = random.choice(names)
        elif label_type == 'OSOITE':
            replacement = random.choice(addresses)
        else:
            continue

        # Calculate actual position accounting for previous replacements
        actual_start = start + current_offset

        # Replace in result
        result = result[:actual_start] + replacement + result[actual_start + (end - start):]

        # Record the entity position in the final text
        actual_end = actual_start + len(replacement)
        injected_entities.append((actual_start, actual_end, label_type, replacement))

        # Update offset for next replacement
        # Offset changes by the difference between replacement length and placeholder length
        current_offset += len(replacement) - (end - start)

    return result, injected_entities


def check_entity_anonymized(
    anonymized_text: str,
    original_text: str,
    entity_start: int,
    entity_end: int,
    entity_text: str,
    label_type: str
) -> str:
    """
    Check if an entity was properly anonymized.

    Returns:
        'success' - Entity was fully anonymized
        'partial' - Entity was partially anonymized
        'failed' - Entity was not anonymized
    """
    # The entity text should not appear in the anonymized output
    if entity_text not in anonymized_text:
        # Check if appropriate label exists
        expected_labels = ['<NIMI>', '<OSOITE>'] if label_type == 'NIMI' else ['<OSOITE>', '<SIJAINTI>']
        if any(label in anonymized_text for label in expected_labels):
            return 'success'
        # Text is gone but no label - might still be success if replaced with any label
        if '<' in anonymized_text and '>' in anonymized_text:
            return 'success'
        return 'partial'
    else:
        # Entity text still present
        # Check if at least part was anonymized (label present)
        if '<' in anonymized_text and '>' in anonymized_text:
            return 'partial'
        return 'failed'


def evaluate_longer_texts_with_threshold(
    iterations: int,
    gliner_threshold: float,
    anonymizer: Optional[TextAnonymizer] = None,
    verbose: int = 1
) -> EvaluationResult:
    """
    Evaluate anonymizer with longer texts containing multiple entities.

    Process:
    1. Load template sentences with <NIMI> and <OSOITE> placeholders
    2. Replace placeholders with random names/addresses
    3. Run anonymizer on the filled text
    4. Check if all injected entities were properly anonymized

    Args:
        iterations: Number of test iterations
        gliner_threshold: GLiNER confidence threshold
        anonymizer: Pre-initialized anonymizer (optional)
        verbose: 0 = silent, 1 = summary only, 2 = all details

    Returns:
        EvaluationResult with success/partial/failed counts
    """
    if verbose >= 1:
        logger.info("Evaluating longer texts: iterations=%d, threshold=%.2f", iterations, gliner_threshold)

    start_time = time.time()

    if anonymizer is None:
        anonymizer = TextAnonymizer(debug_mode=False)

    # Load templates and generate test data
    templates = load_test_sentences()
    names = test_util_text_anonymizer.generate_full_names(iterations * 5)  # Generate pool of names
    addresses = test_util_text_anonymizer.generate_streets(iterations * 5)  # Generate pool of addresses

    success_count = 0
    partial_count = 0
    failed_items = []

    total_entities = 0
    entities_success = 0
    entities_partial = 0
    entities_failed = 0

    for i in range(iterations):
        # Pick a random template
        template = random.choice(templates)

        # Reset random seed for reproducible name/address selection per iteration
        # (but still randomized based on iteration)
        random.seed(1234 + i)

        # Fill template with random content
        filled_text, injected_entities = replace_placeholders_with_content(
            template, names, addresses
        )

        if not injected_entities:
            continue

        # Anonymize the filled text
        anonymized = anonymizer.anonymize_text(filled_text, gliner_threshold=gliner_threshold)

        # Check each injected entity
        iteration_success = 0
        iteration_partial = 0
        iteration_failed = 0

        for entity_start, entity_end, label_type, entity_text in injected_entities:
            total_entities += 1

            result = check_entity_anonymized(
                anonymized, filled_text, entity_start, entity_end, entity_text, label_type
            )

            if result == 'success':
                entities_success += 1
                iteration_success += 1
            elif result == 'partial':
                entities_partial += 1
                iteration_partial += 1
            else:
                entities_failed += 1
                iteration_failed += 1

        # Determine overall result for this text
        if iteration_failed == 0 and iteration_partial == 0:
            success_count += 1
            if verbose >= 2:
                print(f"  [SUCCESS] All {len(injected_entities)} entities anonymized")
                print(f"    Input:  '{filled_text[:80]}...'")
                print(f"    Output: '{anonymized[:80]}...'")
        elif iteration_failed == 0:
            partial_count += 1
            if verbose >= 2:
                print(f"  [PARTIAL] {iteration_success}/{len(injected_entities)} entities fully anonymized")
                print(f"    Input:  '{filled_text[:80]}...'")
                print(f"    Output: '{anonymized[:80]}...'")
        else:
            failed_items.append(f"Text {i+1}: {iteration_failed}/{len(injected_entities)} entities not anonymized")
            if verbose >= 2:
                print(f"  [FAILED ] {iteration_failed}/{len(injected_entities)} entities not anonymized")
                print(f"    Input:  '{filled_text[:80]}...'")
                print(f"    Output: '{anonymized[:80]}...'")
                # Show which entities failed
                for entity_start, entity_end, label_type, entity_text in injected_entities:
                    if entity_text in anonymized:
                        print(f"    - NOT anonymized: '{entity_text}' ({label_type})")

    duration = time.time() - start_time

    if verbose >= 1:
        logger.info("Longer texts entity stats: %d success, %d partial, %d failed (total: %d)",
                   entities_success, entities_partial, entities_failed, total_entities)

    return EvaluationResult(
        test_name="Longer Texts",
        samples=iterations,
        success_count=success_count,
        partial_count=partial_count,
        failed_items=failed_items,
        duration_seconds=duration,
        gliner_threshold=gliner_threshold
    )


def print_separator(char: str = "-", length: int = 80):
    """Print a separator line."""
    print(char * length)


def print_results_table(results: List[EvaluationResult], title: str = "EVALUATION RESULTS SUMMARY"):
    """Print a formatted results table."""
    print_separator("=")
    print(title)
    print_separator("=")

    # Header
    header = f"{'Test Category':<22} {'Samples':>8} {'Success':>10} {'Partial':>10} {'Failed':>8} {'Accuracy':>10} {'Partial %':>10}"
    print(header)
    print_separator("-")

    # Data rows
    total_samples = 0
    total_success = 0
    total_partial = 0
    total_failed = 0

    for result in results:
        failed_count = len(result.failed_items)
        row = f"{result.test_name:<22} {result.samples:>8} {result.success_count:>10} {result.partial_count:>10} {failed_count:>8} {result.accuracy:>9.2f}% {result.partial_rate:>9.2f}%"
        print(row)
        total_samples += result.samples
        total_success += result.success_count
        total_partial += result.partial_count
        total_failed += failed_count

    print_separator("-")

    # Totals
    overall_accuracy = round((total_success / total_samples) * 100, 2) if total_samples > 0 else 0.0
    overall_partial = round((total_partial / total_samples) * 100, 2) if total_samples > 0 else 0.0
    totals_row = f"{'TOTAL':<22} {total_samples:>8} {total_success:>10} {total_partial:>10} {total_failed:>8} {overall_accuracy:>9.2f}% {overall_partial:>9.2f}%"
    print(totals_row)
    print_separator("=")


def print_failed_items(results: List[EvaluationResult], max_items: int = 20):
    """Print failed items for each test category."""
    print("\nFAILED ITEMS DETAILS")
    print_separator("=")

    for result in results:
        if result.failed_items:
            print(f"\n{result.test_name} - {len(result.failed_items)} failed:")
            print_separator("-", 40)

            items_to_show = result.failed_items[:max_items]
            for item in items_to_show:
                print(f"  - {item}")

            if len(result.failed_items) > max_items:
                print(f"  ... and {len(result.failed_items) - max_items} more")
        else:
            print(f"\n{result.test_name}: All samples passed")


def print_threshold_optimization_table(threshold_results: List[ThresholdResult]):
    """Print threshold optimization results table."""
    print_separator("=")
    print("THRESHOLD OPTIMIZATION RESULTS")
    print_separator("=")

    # Header
    header = f"{'Threshold':>10} {'Names':>12} {'Addresses':>12} {'Words':>12} {'Combined':>12} {'Duration':>10}"
    print(header)
    print_separator("-")

    # Sort by combined score descending
    sorted_results = sorted(threshold_results, key=lambda x: x.combined_score, reverse=True)

    for result in sorted_results:
        row = f"{result.threshold:>10.2f} {result.name_accuracy:>11.2f}% {result.address_accuracy:>11.2f}% {result.word_accuracy:>11.2f}% {result.combined_score:>11.2f}% {result.total_duration:>9.2f}s"
        print(row)

    print_separator("=")

    # Best threshold recommendation
    best = sorted_results[0]
    print(f"\nRECOMMENDED THRESHOLD: {best.threshold:.2f}")
    print(f"  - Combined Score: {best.combined_score:.2f}%")
    print(f"  - Name Accuracy: {best.name_accuracy:.2f}%")
    print(f"  - Address Accuracy: {best.address_accuracy:.2f}%")
    print(f"  - False Positive Rate: {100.0 - best.word_accuracy:.2f}%")
    print_separator("=")


def run_threshold_optimization(
    iterations: int = 100,
    thresholds: List[float] = None,
    seed: int = 1234,
    verbose: bool = True
) -> Tuple[float, List[ThresholdResult]]:
    """
    Run evaluation with multiple GLiNER thresholds to find optimal value.

    Args:
        iterations: Number of samples per test category
        thresholds: List of threshold values to test (default: [0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
        seed: Random seed for reproducibility
        verbose: Print detailed output

    Returns:
        Tuple of (best_threshold, all_results)
    """
    if thresholds is None:
        thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

    logger.info("Starting threshold optimization")
    logger.info("Configuration: iterations=%d, thresholds=%s, seed=%d", iterations, thresholds, seed)

    # Set random seed
    random.seed(seed)

    # Pre-generate test data once (same data for all thresholds)
    logger.info("Generating test data...")
    test_names = test_util_text_anonymizer.generate_full_names(iterations)
    test_streets = test_util_text_anonymizer.generate_streets(iterations)
    test_words = test_util_text_anonymizer.generate_words(iterations)

    print("\n")
    print_separator("=")
    print("TEXT ANONYMIZER THRESHOLD OPTIMIZATION")
    print_separator("=")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Random Seed: {seed}")
    print(f"Iterations per category: {iterations}")
    print(f"Thresholds to test: {thresholds}")
    print_separator("-")

    # Initialize anonymizer once (model loading is slow)
    logger.info("Loading anonymizer model...")
    anonymizer = TextAnonymizer(debug_mode=False)

    threshold_results = []

    for idx, threshold in enumerate(thresholds):
        print(f"\n[{idx + 1}/{len(thresholds)}] Testing threshold: {threshold:.2f}")
        print_separator("-", 50)

        start_time = time.time()

        # Evaluate names
        name_success = 0
        for name in test_names:
            anonymized = anonymizer.anonymize_text(name, gliner_threshold=threshold)
            if anonymized.startswith('<') and anonymized.endswith('>'):
                name_success += 1
        name_accuracy = round((name_success / iterations) * 100, 2)
        print(f"  Names:     {name_accuracy:>6.2f}% ({name_success}/{iterations})")

        # Evaluate addresses (success = has label AND no numbers remaining)
        address_success = 0
        for street in test_streets:
            anonymized = anonymizer.anonymize_text(street, gliner_threshold=threshold)
            has_label = '<' in anonymized and '>' in anonymized
            no_numbers = not any(char.isdigit() for char in anonymized)
            if has_label and no_numbers:
                address_success += 1
        address_accuracy = round((address_success / iterations) * 100, 2)
        print(f"  Addresses: {address_accuracy:>6.2f}% ({address_success}/{iterations})")

        # Evaluate words (false positives)
        word_success = 0
        for word in test_words:
            anonymized = anonymizer.anonymize_text(word, gliner_threshold=threshold)
            if '<' not in anonymized:
                word_success += 1
        word_accuracy = round((word_success / iterations) * 100, 2)
        print(f"  Words:     {word_accuracy:>6.2f}% ({word_success}/{iterations}) [higher = fewer false positives]")

        duration = time.time() - start_time

        result = ThresholdResult(
            threshold=threshold,
            name_accuracy=name_accuracy,
            address_accuracy=address_accuracy,
            word_accuracy=word_accuracy,
            total_duration=duration
        )
        threshold_results.append(result)

        print(f"  Combined:  {result.combined_score:>6.2f}%")
        print(f"  Duration:  {duration:.2f}s")

    # Print summary table
    print("\n")
    print_threshold_optimization_table(threshold_results)

    # Find best threshold
    best_result = max(threshold_results, key=lambda x: x.combined_score)

    return best_result.threshold, threshold_results


def run_evaluation(
    iterations: int = 100,
    seed: int = 1234,
    accuracy_threshold: float = 0.95,
    gliner_threshold: float = 0.6,
    verbose: int = 1
) -> Tuple[bool, List[EvaluationResult]]:
    """
    Run the full evaluation suite with a single GLiNER threshold.

    Args:
        iterations: Number of samples per test category
        seed: Random seed for reproducibility
        accuracy_threshold: Minimum accuracy threshold (0.0 to 1.0)
        gliner_threshold: GLiNER confidence threshold (0.0 to 1.0)
        verbose: 0 = final report only, 1 = summary (default), 2 = all details

    Returns:
        Tuple of (all_passed, results_list)
    """
    if verbose >= 1:
        logger.info("Starting evaluation suite")
        logger.info("Configuration: iterations=%d, seed=%d, accuracy_threshold=%.2f, gliner_threshold=%.2f, verbose=%d",
                    iterations, seed, accuracy_threshold, gliner_threshold, verbose)

    # Set random seed for reproducibility
    random.seed(seed)

    if verbose >= 1:
        print("\n")
        print_separator("=")
        print("TEXT ANONYMIZER EVALUATION SUITE")
        print_separator("=")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Random Seed: {seed}")
        print(f"Iterations per category: {iterations}")
        print(f"GLiNER Threshold: {gliner_threshold}")
        print(f"Accuracy Threshold: {accuracy_threshold * 100:.1f}%")
        print(f"Verbose Level: {verbose}")
        print_separator("-")

    # Initialize anonymizer once
    if verbose >= 1:
        logger.info("Loading anonymizer model...")
    anonymizer = TextAnonymizer(debug_mode=False)

    results = []

    # Run evaluations
    if verbose >= 1:
        print("\n[1/4] Evaluating name anonymization...")
        if verbose >= 2:
            print_separator("-", 60)
    results.append(evaluate_names_with_threshold(iterations, gliner_threshold, anonymizer, verbose=verbose))

    if verbose >= 1:
        print("\n[2/4] Evaluating address anonymization...")
        if verbose >= 2:
            print_separator("-", 60)
    results.append(evaluate_addresses_with_threshold(iterations, gliner_threshold, anonymizer, verbose=verbose))

    if verbose >= 1:
        print("\n[3/4] Evaluating false positives (plain words)...")
        if verbose >= 2:
            print_separator("-", 60)
    results.append(evaluate_words_with_threshold(iterations, gliner_threshold, anonymizer, verbose=verbose))

    if verbose >= 1:
        print("\n[4/4] Evaluating longer texts with multiple entities...")
        if verbose >= 2:
            print_separator("-", 60)
    results.append(evaluate_longer_texts_with_threshold(iterations, gliner_threshold, anonymizer, verbose=verbose))

    # Print failed items (details) - only at verbose >= 1
    if verbose >= 1:
        print_failed_items(results)

    # Check thresholds
    if verbose >= 1:
        print("\n")
        print_separator("=")
        print("THRESHOLD CHECK")
        print_separator("=")

    all_passed = True
    threshold_pct = accuracy_threshold * 100

    for result in results:
        passed = result.accuracy >= threshold_pct
        status = "PASS" if passed else "FAIL"
        if verbose >= 1:
            print(f"{result.test_name}: {result.accuracy:.2f}% (threshold: {threshold_pct:.1f}%) - {status}")
        if not passed:
            all_passed = False

    if verbose >= 1:
        print_separator("-")
    overall_status = "PASS" if all_passed else "FAIL"
    if verbose >= 1:
        print(f"Overall Result: {overall_status}")
        print_separator("=")

    # Print results table (always printed - this is the final report)
    print("\n")
    print_results_table(results)

    return all_passed, results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Text Anonymizer Evaluation Suite",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--iterations", type=int, default=100,
        help="Number of samples per test category"
    )
    parser.add_argument(
        "--seed", type=int, default=1234,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--accuracy-threshold", type=float, default=0.95,
        help="Minimum accuracy threshold (0.0 to 1.0)"
    )
    parser.add_argument(
        "--gliner-threshold", type=float, default=0.6,
        help="GLiNER confidence threshold (0.0 to 1.0)"
    )
    parser.add_argument(
        "--optimize", action="store_true",
        help="Run threshold optimization mode"
    )
    parser.add_argument(
        "--thresholds", type=str, default="0.3,0.4,0.5,0.6,0.7,0.8",
        help="Comma-separated list of thresholds to test (used with --optimize)"
    )
    parser.add_argument(
        "--verbose", "-v", type=int, default=1, choices=[0, 1, 2],
        help="Verbosity level: 0 = final report only, 1 = summary (default), 2 = all details"
    )

    args = parser.parse_args()

    if args.optimize:
        # Parse thresholds
        thresholds = [float(t.strip()) for t in args.thresholds.split(',')]

        best_threshold, _ = run_threshold_optimization(
            iterations=args.iterations,
            thresholds=thresholds,
            seed=args.seed
        )

        print(f"\nOptimal threshold found: {best_threshold}")
        sys.exit(0)
    else:
        all_passed, _ = run_evaluation(
            iterations=args.iterations,
            seed=args.seed,
            accuracy_threshold=args.accuracy_threshold,
            gliner_threshold=args.gliner_threshold,
            verbose=args.verbose
        )

        sys.exit(0 if all_passed else 1)


class TestEvaluationSuite:
    """
    Test class for running evaluations as part of a test suite.
    Can be run with pytest or unittest.
    """

    def test_evaluation_suite(self):
        """Run the full evaluation suite with default parameters."""
        all_passed, results = run_evaluation(
            iterations=100,
            seed=1234,
            accuracy_threshold=0.95,
            gliner_threshold=0.6
        )
        assert all_passed, "Evaluation suite did not meet accuracy threshold"


if __name__ == "__main__":
    main()

