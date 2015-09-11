import textwrap
import sys
import re

PARAM_REGEX = "^[ ]*- parameter[ ]+"
RETURN_REGEX = "^[ ]*- returns:[ ]+"

line_length = int(sys.argv[1])
files = sys.argv[2:]


def get_ranges(content):
    ranges = []
    start = None
    end = None
    for i, line in enumerate(content):
        if re.match("^\s*/\*\*", line):
            start = i
        elif re.match("^\s*\*/", line):
            end = i + 1
        elif start is None:
            continue

        if start is not None and end is not None:
            ranges.append((start, end))
            start = None
            end = None

    return ranges


def longest_param(lines, regex):
    longest = None
    for line in lines:
        if re.match(regex, line):
            index = line.index(":")
            if index > longest:
                longest = index

    return longest


def spaced_lines(lines, regex):
    first_char_index = longest_param(lines, regex)
    if first_char_index is None:
        return lines

    new_lines = []
    for line in lines:
        if re.match(regex, line):
            index = line.index(":")
            diff = first_char_index - index
            assert(diff >= 0)

            identifier_regex = "^([^:]*:)[ ]+"
            assert(re.match(identifier_regex, line))

            new_line = re.sub(identifier_regex, "\\1%s" %
                              (" " * (diff + 1)), line)
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    return new_lines


def join_params(lines, regex):
    new_lines = []
    in_identifier = False
    accum = None

    for line in lines:
        if in_identifier:
            if line.strip() == "" or line.strip() == "*/":
                if accum is not None:
                    new_lines.append(accum)
                    accum = None
                in_identifier = False
                new_lines.append(line)
            elif re.match(PARAM_REGEX, line) or re.match(RETURN_REGEX, line):
                if accum is not None:
                    new_lines.append(accum)
                accum = line
            else:
                accum = "%s %s" % (accum, line.strip())
        elif re.match(regex, line):
            if accum is not None:
                new_lines.append(accum)
            in_identifier = True
            accum = line
        else:
            accum = None
            new_lines.append(line)

    if accum is not None:
        new_lines.append(accum)

    return new_lines


def first_real_index(lines, regex):
    for line in lines:
        if re.match(regex, line):
            parts = line.split(":")
            before = len(parts[1])
            after = len(parts[1].strip())
            return len(parts[0]) + 1 + (before - after)

    return None


def newlined(lines, regex):
    index = first_real_index(lines, regex)
    if index is None:
        return lines

    new_lines = []
    for line in lines:
        if len(line) < line_length:
            new_lines.append(line)
            continue

        if re.match(regex, line):
            wrapped = textwrap.wrap(line, line_length,
                                    subsequent_indent=(" " * index))
            new_lines += wrapped
        else:
            new_lines.append(line)

    return new_lines


def fix_comments(content, ranges, regex):
    new_content = list(content)
    for start, end in ranges[::-1]:
        lines = content[start:end]
        comment = " ".join(lines)

        if "parameter" not in comment and "returns" not in comment:
            continue

        joined = join_params(lines, regex)
        spaced = spaced_lines(joined, regex)
        broken = newlined(spaced, regex)
        new_content[start:end] = broken

    return new_content

for file in files:
    content = open(file).read().split("\n")
    param_ranges = get_ranges(content)
    param_content = fix_comments(content, param_ranges, PARAM_REGEX)
    return_ranges = get_ranges(param_content)
    return_content = fix_comments(param_content, return_ranges, RETURN_REGEX)

    with open(file, "w") as outfile:
        outfile.write("\n".join(return_content))
