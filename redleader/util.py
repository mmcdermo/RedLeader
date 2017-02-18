import re
import sys

def multireplace(string, replacements):
    substrs = sorted(replacements, key=len, reverse=True)
    regexp = re.compile('|'.join(map(re.escape, substrs)))
    return regexp.sub(lambda match: replacements[match.group(0)], string)

def print_progress(current, max_progress=20, progress_char="="):
    sys.stdout.write("[")
    for x in range(current % max_progress):
        sys.stdout.write("=")
    for x in range(max_progress - (current % max_progress)):
        sys.stdout.write(" ")
    sys.stdout.write("]")
    sys.stdout.write("\r")
    sys.stdout.flush()
