import re
import sys
import textwrap

# Regular expressions matching parameter and return comments
PARAM_REGEX = "^[ ]*- parameter[ ]+"
RETURN_REGEX = "^[ ]*- returns:[ ]+"


def get_comment_ranges(content):
    """Get ranges of comments in content

    :param content: Array of strings to find comments in

    :returns: list of tuples with start and end integers corresponding to the
              start and end of documentation comments in the given content
    """
    ranges = []
    start = None
    end = None
    for i, line in enumerate(content):
        if re.match("^[ ]*/\*\*", line):
            start = i
        elif re.match("^[ ]*\*/", line):
            end = i + 1
        elif start is None:
            continue

        if start is not None and end is not None:
            ranges.append((start, end))
            start = None
            end = None

    return ranges


def longest_matching(lines, regex):
    """Returns the index of the first : in the longest matching line

    :param lines: list of strings to find the longest parameter in
    :param regex: regex to identify the lines to compare

    :returns: The highest index of the first : in the matching lines,
              or None if no line matches the given regex
    """
    longest = None
    for line in lines:
        if re.match(regex, line):
            index = line.index(":")
            if index > longest:
                longest = index

    return longest


def spaced_lines(lines, regex):
    """Align properties matching the given regex

    This takes the given regex and aligns the strings in lines to make the
    first character of the description line up after the longest :

    :param lines: list of strings to re-space
    :param regex: regex to identify the start of a new group

    :returns: list of strings with the newly spaced lines
    """
    first_char_index = longest_matching(lines, regex)
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


def is_end_of_group(string):
    """Determine if the given string should be interpreted as the end of a
    docstring identifier

    :param string: The string to use to determine if it's the end

    :returns: True if the string is the end of a group, otherwise false
    """
    return string.strip() == "" or string.strip() == "*/"


def join_multiline_identifiers(lines, regex):
    """Join the multi-line parameters/returns so they can be re-flowed

    This function takes the list of strings and joins subsequent lines that "go
    together." For example a multi-line parameter argument in a docstring would
    be concatenated with a space. After this the lines can be re-aligned based
    on the maximum line length

    :param lines: list of strings to join
    :param regex: regex to identify the start of a new identifier

    :returns: list of strings with multi-line comments joined
              (NOTE: this list is not particularly the same length as the
              original)
    """
    new_lines = []
    in_identifier = False
    accum = None

    for line in lines:
        if in_identifier:
            if is_end_of_group(line):
                new_lines.append(accum)
                accum = None
                in_identifier = False
                new_lines.append(line)
            elif re.match(PARAM_REGEX, line) or re.match(RETURN_REGEX, line):
                new_lines.append(accum)
                accum = line
            else:
                accum = "%s %s" % (accum, line.strip())
        elif re.match(regex, line):
            new_lines.append(accum)
            in_identifier = True
            accum = line
        else:
            accum = None
            new_lines.append(line)

    new_lines.append(accum)
    return [x for x in new_lines if x is not None]


def first_char_index(lines, regex):
    """Get the index of the first position for a description character

    Use this to find where the first character after the : should be placed so
    that each comment can line up.

    :param lines: list of strings to find the index for
    :param regex: Regex to identify the line to compare with

    :returns: The index of the first position for description characters,
              or None if no lines matched the given regex
    """
    for line in lines:
        if re.match(regex, line):
            parts = line.split(":")
            before = len(parts[1])
            after = len(parts[1].strip())
            return len(parts[0]) + 1 + (before - after)

    return None


def reflowed_lines(lines, regex, line_length):
    """Get the realigned lines

    This method takes a list of strings and lays them out respecting the given
    line length while also lining up the hanging lines

    :param lines: list of strings to realign
    :param regex: regex to identify the lines to reflow
    :param line_length: the maximum length for each line

    :returns: list of strings to use in place of the given lines
    """
    index = first_char_index(lines, regex)
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


def fix_comments(content, ranges, regex, line_length):
    """Get replacement content with the comments realigned correctly

    :param content: The content to realign
    :param ranges: The ranges of doc comments in the given content
    :param regex: The regex to identify the lines to fix
    :param line_length: The maximum line length for each line

    :returns: list of strings that replace the given content with fixed
              comments
    """
    new_content = list(content)
    for start, end in ranges[::-1]:
        lines = content[start:end]
        comment = " ".join(lines)

        if "parameter" not in comment and "returns" not in comment:
            continue

        joined = join_multiline_identifiers(lines, regex)
        spaced = spaced_lines(joined, regex)
        aligned = reflowed_lines(spaced, regex, line_length)
        new_content[start:end] = aligned

    return new_content


def main(args):
    line_length = int(args[0])
    files = args[1:]

    for infile in files:
        content = open(infile).read().split("\n")
        param_ranges = get_comment_ranges(content)
        param_content = fix_comments(content, param_ranges, PARAM_REGEX,
                                     line_length)
        return_ranges = get_comment_ranges(param_content)
        return_content = fix_comments(param_content, return_ranges,
                                      RETURN_REGEX, line_length)

        with open(infile, "w") as outfile:
            outfile.write("\n".join(return_content))


if __name__ == "__main__":
    main(sys.argv[1:])
