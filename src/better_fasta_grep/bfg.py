#!/usr/bin/env python

# Author: Felix Thalen
# Date: September 9, 2019

'''
Search for one or more patterns within a FASTA file and print matching sequence
headers and or sequences. Default behaviour: look for the provided patterns
only within headers and output both headers and sequences.
'''

import argparse
import io
import select
import sys
import re
import os

VERSION_NUMBER = 0.1
NORMAL = '\033[0m'
BOLD_RED = '\033[1;31m'
GREEN = '\033[32m'
CYAN = '\033[36m'
OFFSET = len(BOLD_RED) + len(NORMAL)


def supports_color():
    '''
    Returns True if the running system's terminal supports color and that the
    output is not being redirected.
    '''
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or
                                                  'ANSICON' in os.environ)
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

    if not supported_platform or not is_a_tty:
        return False
    return True


def lines_in_fasta(file):
    '''
    Takes the path to a FASTA file as an input. Yields each line within the
    provided file, without newline characters removed, as strings.
    '''
    if isinstance(file, io.TextIOWrapper):
        # input comes from stdin, not file
        for line in file:
            yield line.rstrip()
    else:
        with open(file) as fasta_file:
            for line in fasta_file:
                yield line.rstrip()


def is_header(line):
    'Returns True if the provided string starts with a greater than sign.'
    return line.startswith('>')


def is_hit(result, invert_match=False):
    '''
    Takes a regular expression match object and a Boolean as an input. Returns
    True if the the result is a hit and the search is not inverted or if the
    result is a miss but the search is inverted, else False.
    '''
    return (invert_match and not result) or (not invert_match and result)


def highlight_str(string, span):
    '''
    Takes a string and a 2-tuple as an input. Returns the string surrounded
    with escape sequences for coloring the string in bold red.
    '''
    start, end = span
    color_str = ''
    color_str += string[0: start]
    color_str += BOLD_RED
    color_str += string[start: end]
    color_str += NORMAL
    color_str += string[end:]
    return color_str


def add_pattern(string, ignore_case=False, fixed_strings=False):
    '''
    Takes a string and a Boolean as an input. Returns the string as a regular
    expression Pattern object with re.IGNORECASE set if ignore_case is True.
    '''
    if fixed_strings:
        string = re.escape(string)

    if ignore_case:
        return re.compile(string, re.IGNORECASE)
    return re.compile(string)


def get_patterns(pattern=False, patterns_file=False, ignore_case=False,
                 fixed_strings=False):
    '''
    Takes a string, the path to a file containing multiple patterns, separated
    by newline, and 2 Boolean as an input. The string and the file path is
    optional. Returns a set of all the patterns that were found in the pattern
    string and or the patterns file.
    '''
    patterns = set()

    if pattern:
        patterns.add(add_pattern(pattern, ignore_case, fixed_strings))

    if patterns_file:
        with open(patterns_file) as file:
            for line in file:
                line = line.rstrip()
                patterns.add(add_pattern(line, ignore_case, fixed_strings))

    return patterns


def spans_overlap(span_pair):
    'Takes a set of 2-tuple spans and returns True if the spans overlap'
    span_a, span_b = span_pair
    return range(max(span_a[0], span_b[0]), min(span_a[-1], span_b[-1]) + 1)


def merge_overlapping_spans(spans):
    '''
    Takes a set of 2-tuple (start, end) spans as an input and returns a set of
    2-tuple spans where non of the tuples' start and end overlaps.
    '''
    current_span = ()
    last_span = ()
    merged_span = ()
    merged_spans = set()

    for current_span in sorted(spans):
        if not last_span:
            last_span = current_span
            continue

        if spans_overlap((current_span, last_span)) and merged_span:
            merged_span = merged_span[0], max(current_span)
        elif spans_overlap((current_span, last_span)):
            merged_span = min(last_span), max(current_span)
        elif bool(merged_span):
            merged_spans.add(merged_span)
            merged_span = ()
        else:
            merged_spans.add(last_span)
        last_span = current_span

    if merged_span:
        merged_spans.add(merged_span)
    elif current_span:
        merged_spans.add(current_span)

    return sorted(merged_spans)


def searchiter(patterns, string, invert_match=False, color=False):
    '''
    Takes a set of regular expression pattern objects, a string and 2 Booleans
    as an input. If color is not set or the matching is inverted: search for
    the first match and a Boolean and the input string. If color is set,
    highlight each matching group in the string and return a Boolean and the
    highlighted string.
    '''
    pattern_found = False
    pattern_found_in_record = False
    spans = set()

    for pattern in patterns:
        pattern_found = is_hit(pattern.search(string), invert_match)

        if not pattern_found:
            continue

        if not pattern_found_in_record:
            pattern_found_in_record = True

        if color and not invert_match:
            for result in pattern.finditer(string):
                spans.add(result.span())
        elif not color or invert_match:
            break

    if color and spans:
        for span in merge_overlapping_spans(spans):
            string = highlight_str(string, span)

    return pattern_found_in_record, string


def count_header_matches(patterns, file, invert_match=False, max_count=None):
    '''
    Takes a set of a patterns, the path to a FASTA file, a Boolean and the
    maximum number of allowed matches (an integer) as an input. Returns the
    number of matches found within the headers of the FASTA file given the
    settings (invert match or not and the maximum allowed number of matches).
    '''
    hit_count = 0

    for line in lines_in_fasta(file):
        if not is_header(line):
            continue

        pattern_found, _ = searchiter(patterns, line, invert_match)

        if pattern_found:
            hit_count += 1
            if max_count and hit_count >= max_count:
                return hit_count

    return hit_count


def count_seq_matches(patterns, file, invert_match=False, max_count=None):
    '''
    Takes a set of a patterns, the path to a FASTA file, a Boolean and the
    maximum number of allowed matches (an integer) as an input. Returns the
    number of matches found within the sequences of the FASTA file given the
    settings (invert match or not and the maximum allowed number of matches).
    '''
    hit_count = 0
    sequence_data = ''

    for line in lines_in_fasta(file):
        if is_header(line) and sequence_data:
            pattern_found, _ = searchiter(
                patterns, sequence_data, invert_match)
            if pattern_found:
                hit_count += 1
                if max_count and hit_count >= max_count:
                    return hit_count
            sequence_data = ''
        elif is_header(line):
            sequence_data = ''
            continue
        else:
            sequence_data += line

    if sequence_data:
        pattern_found, _ = searchiter(
            patterns, sequence_data, invert_match)
        if pattern_found:
            hit_count += 1
            if max_count and hit_count >= max_count:
                return hit_count
    return hit_count


def count_record_matches(patterns, file, invert_match=False, max_count=None):
    '''
    Takes a set of a patterns, the path to a FASTA file, a Boolean and the
    maximum number of allowed matches (an integer) as an input. Returns the
    number of matches found within the sequences of the FASTA file given the
    settings (invert match or not and the maximum allowed number of matches).
    '''
    last_header = ''
    sequence_data = ''
    hit_count = 0

    for line in lines_in_fasta(file):
        if is_header(line) and sequence_data:
            header_match, _ = searchiter(
                patterns, last_header, invert_match)

            seq_match, _ = searchiter(
                patterns, sequence_data, invert_match)

            if header_match or seq_match:
                hit_count += 1

                if max_count and hit_count >= max_count:
                    return hit_count

            last_header = line
            sequence_data = ''
        elif is_header(line):
            last_header = line
            sequence_data = ''
            continue
        else:
            sequence_data += line

    if sequence_data:
        header_match, _ = searchiter(
            patterns, last_header, invert_match)

        seq_match, _ = searchiter(
            patterns, sequence_data, invert_match)

        if header_match or seq_match:
            hit_count += 1

            if max_count and hit_count >= max_count:
                return hit_count
    return hit_count


def search_headers(patterns, file, invert_match=False, color=False,
                   max_count=None):
    '''
    Takes a list of patterns and a FASTA file path as an input. For each header
    with a matching pattern, yield the whole record in the form of tuples; each
    tuple represents one line where the first item is the line itself and the
    second item is a Boolean which is True if the preceeding item is a header.
    '''
    pattern_found = False
    hit_count = 0

    for line_number, line in enumerate(lines_in_fasta(file), 1):
        if is_header(line):
            pattern_found, line = searchiter(patterns, line, invert_match,
                                             color)

        if pattern_found and is_header(line):
            hit_count += 1
            if max_count and hit_count > max_count:
                return
        if pattern_found:
            yield line_number, line


def split_lines(string, linebreaks, spans):
    '''
    Takes a string, a set of 2-tuple linebreaks and a set of 2-tuple spans as
    an input. Highlight the string according to the spans and also split the
    string into smaller lines, given by the 2-tuple linebreaks.
    '''
    offset = 0

    for linenumber, linebreak in sorted(linebreaks):
        begin = offset
        end = begin + linebreak
        substr = string[begin:end]
        line_offset = 0

        for span_begin, span_end in sorted(spans):
            if span_end <= offset:
                continue
            elif span_end > end > span_begin:
                span_end = end
            elif span_end > end:
                break
            elif span_begin < begin < span_end:
                span_begin, span_end = (offset, span_end)

            substr = highlight_str(
                substr, (span_begin - offset + line_offset,
                         span_end - offset + line_offset))

            line_offset += OFFSET

        yield linenumber, substr
        offset += linebreak


def searchiter_w_linebreaks(patterns, string, invert_match=False, color=False,
                            linebreaks=False):
    '''
    Takes a set of regular expression pattern objects, a string, 2 Booleans,
    and a set of 2-tuples as an input. If color is set, highlight each matching
    group in the string. If a set of linebreaks is provided, also break the
    provided string into lines, as specified by the 2-tuples.
    '''
    pattern_found = False
    spans = set()

    for pattern in patterns:
        pattern_found = is_hit(pattern.search(string), invert_match)

        if not pattern_found:
            continue

        if pattern_found and (color and not invert_match):
            for result in pattern.finditer(string):
                spans.add(result.span())
        else:
            break

    spans = merge_overlapping_spans(spans)

    if pattern_found:
        for line_number, line in split_lines(string, linebreaks, spans):
            yield line_number, line


def search_sequences(patterns, file, invert_match=False, color=False,
                     max_count=None):
    '''
    Takes a pattern string and a FASTA file path as an input. For each sequence
    with a matching pattern, yield the whole record in the form of a tuple;
    each tuple represents one line where the first item is the line itself and
    the second item is a Boolean which is True if the preceeding item is a
    header.
    '''
    linebreaks = set()
    sequence_data = ''
    current_header = ()
    hit_count = 0

    for line_number, line in enumerate(lines_in_fasta(file), 1):
        if max_count and hit_count >= max_count:
            return

        if is_header(line):
            if sequence_data:
                hits = searchiter_w_linebreaks(
                    patterns, sequence_data, invert_match, color, linebreaks)

                first_iteration = True

                for seq_line_no, seq_line in hits:
                    if first_iteration:
                        hit_count += 1
                        yield current_header

                    yield seq_line_no, seq_line
                    first_iteration = False

            current_header = (line_number, line)
            sequence_data = ''
            linebreaks = set()
        else:
            linebreaks.add((line_number, len(line)))
            sequence_data += line

    if sequence_data:
        hits = searchiter_w_linebreaks(
            patterns, sequence_data, invert_match, color, linebreaks)

        first_iteration = True

        for seq_line_no, seq_line in hits:
            if first_iteration:
                hit_count += 1
                yield current_header

            yield seq_line_no, seq_line
            first_iteration = False


def search_records(patterns, file, invert_match=False, color=False,
                   max_count=None):
    '''
    Takes a pattern string and a FASTA file path as an input. Search whole
    sequence records (both headers and sequence data) for a matching pattern.
    For each match, yield the entire record in the form of a tuple; each tuple
    represents one line where the first item is the line itself and the second
    item is a Boolean which is True if the preceeding item is a header.
    '''
    linebreaks = set()
    last_header = ''
    sequence_data = ''
    hit_count = 0

    for line_number, line in enumerate(lines_in_fasta(file), 1):
        if is_header(line) and sequence_data:
            header_match, header_line = searchiter(
                patterns, last_header[1], invert_match, color)
            seq_match, _ = searchiter(
                patterns, sequence_data, invert_match)
            header_line_number = last_header[0]

            if seq_match:
                if max_count and hit_count >= max_count:
                    return

                hits = searchiter_w_linebreaks(
                    patterns, sequence_data, invert_match, color, linebreaks)
                first_iteration = True

                for seq_line_no, seq_line in hits:
                    if first_iteration:
                        yield header_line_number, header_line

                    yield seq_line_no, seq_line
                    first_iteration = False

                hit_count += 1
            elif header_match:
                if max_count and hit_count >= max_count:
                    return

                yield header_line_number, header_line
                offset = 0

                for subseq_line_no, linebreak in sorted(linebreaks):
                    start = offset
                    end = offset + linebreak
                    subseq = sequence_data[start:end]
                    yield subseq_line_no, subseq
                    offset += linebreak

                hit_count += 1

            last_header = line_number, line
            sequence_data = ''
            linebreaks = set()
        elif is_header(line):
            last_header = line_number, line
            sequence_data = ''
            linebreaks = set()
            continue
        else:
            sequence_data += line
            linebreaks.add((line_number, len(line)))

    if sequence_data:
        header_match, header_line = searchiter(
            patterns, last_header[1], invert_match, color)
        seq_match, _ = searchiter(
            patterns, sequence_data, invert_match)
        header_line_number = last_header[0]

        if seq_match:
            if max_count and hit_count >= max_count:
                return

            hits = searchiter_w_linebreaks(
                patterns, sequence_data, invert_match, color, linebreaks)
            first_iteration = True

            for seq_line_no, seq_line in hits:
                if first_iteration:
                    yield header_line_number, header_line

                yield seq_line_no, seq_line
                first_iteration = False

            hit_count += 1
        elif header_match:
            if max_count and hit_count >= max_count:
                return

            yield header_line_number, header_line
            offset = 0

            for subseq_line_no, linebreak in sorted(linebreaks):
                start = offset
                end = offset + linebreak
                subseq = sequence_data[start:end]
                yield subseq_line_no, subseq
                offset += linebreak

            hit_count += 1


def stdin_has_data():
    'Returns True if stdin contains any data.'
    return select.select([sys.stdin, ], [], [], 0.0)[0]


def output_headers(hits, line_number=False, color=False):
    '''
    Takes a set of line numbers, a set of lines, and a Boolean as an input.
    Output sequences, with or without line numbers whether the Boolean is True
    or False.
    '''
    if line_number:
        for number, line in hits:
            if not is_header(line):
                continue

            if color:
                line_no = GREEN + str(number) + CYAN + ':' + NORMAL
            else:
                line_no = str(number) + ':'
            print(line_no + line)
    else:
        for _, line in hits:
            if not is_header(line):
                continue

            print(line)


def output_seqs(hits, line_number=False, color=False):
    '''
    Takes a set of line numbers, a set of lines, and a Boolean as an input.
    Output sequences, with or without line numbers whether the Boolean is True
    or False.
    '''
    if line_number:
        for number, line in hits:
            if is_header(line):
                continue

            if color:
                line_no = GREEN + str(number) + CYAN + ':' + NORMAL
            else:
                line_no = str(number) + ':'
            print(line_no + line)
    else:
        for _, line in hits:
            if is_header(line):
                continue

            print(line)


def output_records(hits, line_number=False, color=False):
    '''
    Takes a set of line numbers, a set of lines, and a Boolean as an input.
    Output both headers and sequences with or without line numbers whether the
    Boolean is True or False.
    '''
    if line_number:
        for number, line in hits:
            if color:
                line_no = GREEN + str(number) + CYAN + ':' + NORMAL
            else:
                line_no = str(number) + ':'
            print(line_no + line)
    else:
        for _, line in hits:
            print(line)


def verify_args(arguments):
    '''
    Process the provided argument object and perform some basic sanity checks.
    '''
    fasta_file = arguments.fasta_file
    pattern = arguments.pattern

    if not arguments.fasta_file and stdin_has_data():
        # FILE was not provided and stdin contains data, read input from stdin
        fasta_file = sys.stdin
    elif os.path.isfile(arguments.pattern):
        # PATTERN is a file assign this file to fasta_file
        fasta_file = arguments.pattern
        pattern = ''

    return fasta_file, pattern


def parse_args():
    'Parse the user-provided arguments.'
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)

    group = parser.add_argument_group('pattern selection and interpretation')
    group.add_argument('-F', '--fixed-strings',
                       action='store_true',
                       default=False,
                       help='PATTERN is a string')
    group.add_argument('-f', '--file',
                       metavar='FILE',
                       help='take patterns, separated by newline characters, \
                             from FILE')
    group.add_argument('-i', '-y', '--ignore-case',
                       action='store_true',
                       default=False,
                       help='ignore case distinctions')
    group.add_argument('--search-sequences',
                       action='store_true',
                       default=False,
                       help='only look for PATTERN in sequences')
    group.add_argument('--search-records',
                       action='store_true',
                       default=False,
                       help='look for PATTERN in headers and sequences')

    group = parser.add_argument_group('miscellaneous')
    group.add_argument('-V', '--version',
                       action='version',
                       version=str(VERSION_NUMBER),
                       help='display version information and exit')
    group.add_argument('-v', '--invert-match',
                       action='store_true',
                       default=False,
                       help='select non-matching lines')
    group.add_argument('--help',
                       action='help',
                       help='display this help text and exit')

    group = parser.add_argument_group('output control')
    group.add_argument('-m', '--max-count',
                       metavar='NUM',
                       default=None,
                       type=int,
                       help='stop after NUM selected lines')
    group.add_argument('-n', '--line-number',
                       action='store_true',
                       default=False,
                       help='print line number with output lines')
    group.add_argument('-c', '--count',
                       action='store_true',
                       default=False,
                       help='print only a count of select lines')
    group.add_argument('--no-color',
                       action='store_true',
                       default=False,
                       help='do not colorize text when printed to stdout')
    group.add_argument('--output-headers',
                       action='store_true',
                       default=False,
                       help='only output the headers of matching records')
    group.add_argument('--output-sequences',
                       action='store_true',
                       default=False,
                       help='only output the sequences of matching records')

    parser.add_argument('pattern',
                        metavar='PATTERN',
                        nargs='?',
                        type=str,
                        help='the pattern you wish to match in the FASTA file')
    parser.add_argument('fasta_file',
                        metavar='FILE',
                        nargs='?',
                        default=None,
                        type=str,
                        help='the FASTA file to search within')

    return parser.parse_args(args=None if sys.argv[1:] else ['--help'])


def main():
    'Run the program from start to finish.'
    args = parse_args()
    color = True

    if not supports_color() or args.no_color:
        # the output is being redirected or the terminal is lacking color support
        color = False

    fasta_file, pattern = verify_args(args)
    patterns = get_patterns(pattern, args.file, args.ignore_case,
                            args.fixed_strings)

    if args.count and args.search_sequences:
        hit_count = count_seq_matches(patterns, fasta_file, args.invert_match, args.max_count)
    elif args.count and args.search_records:
        hit_count = count_record_matches(patterns, fasta_file, args.invert_match,
                                         args.max_count)
    elif args.count:
        hit_count = count_header_matches(patterns, fasta_file, args.invert_match,
                                         args.max_count)

    if args.count:
        # count requested, only print the number of matches
        print(hit_count)
        sys.exit()

    if args.search_sequences:
        hits = search_sequences(patterns, fasta_file, args.invert_match, color,
                                args.max_count)
    elif args.search_records:
        hits = search_records(patterns, fasta_file, args.invert_match, color,
                              args.max_count)
    else:
        hits = search_headers(patterns, fasta_file, args.invert_match, color,
                              args.max_count)

    if args.output_sequences and not args.output_headers:
        output_seqs(hits, args.line_number, color)
    elif args.output_headers and not args.output_sequences:
        output_headers(hits, args.line_number, color)
    else:
        output_records(hits, args.line_number, color)


def entry():
    main()
    return 0

if __name__ == '__main__':
    main()
