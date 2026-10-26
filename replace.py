#-----------------------------------------------------------------------
# replace.py
# Author: Bob Dondero
#-----------------------------------------------------------------------

import sys

def main():
    if len(sys.argv) != 4:
        print('Usage: python ' + sys.argv[0] +
            ' filename fromstr tostr', file=sys.stderr)
        sys.exit(1)

    filename = sys.argv[1]
    fromstr = sys.argv[2]
    tostr = sys.argv[3]

    lines = []

    try:
        with open(filename, 'r', encoding='utf-8') as infile:
            for line in infile:
                line = line.replace(fromstr, tostr)
                lines.append(line)

        with open(filename, 'w', encoding='utf-8') as outfile:
            for line in lines:
                print(line, file=outfile, end='')

    except Exception as ex:
        print(ex, file=sys.stderr)

if __name__ == '__main__':
    main()
