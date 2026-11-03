#!/usr/bin/env python

#-----------------------------------------------------------------------
# regoverviews.py
# Author: Hagop Alajajian
#-----------------------------------------------------------------------
"""An application built based on registrar: show Princeton classes based
 on various matching filters."""
import sys
import argparse
import textwrap
import socket
import json

#-----------------------------------------------------------------------


DB = 'file:reg.sqlite'

# output table
# column has title
# titles underlined with hyphens
# row <= 72 chars not including \n
# each row each line must end after a word, not within a word,
# so no newline chars in words

def main():
    """Read command line arguments, query the database, print matches"""
    parser = argparse.ArgumentParser(prog='regoverviews.py',
                                     description=
                                     'Registrar application: ' \
                                     'show overviews of classes')
    parser.add_argument('-d', metavar='dept', default='',
                        help='show only those classes whose ' \
                        'department contains dept')
    parser.add_argument('-n', metavar='num', default='',
                        help='show only those classes whose ' \
                        'course number contains num')
    parser.add_argument('-a', metavar='area', default='',
                        help='show only those classes whose ' \
                        'distrib area contains area')
    parser.add_argument('-t', metavar='title', default='',
                        help='show only those classes whose ' \
                        'course title contains title')
    parser.add_argument('host',
                        help='the computer on which the ' \
                        'server is running')
    parser.add_argument('port',  type=int,
                        help='the port at which the server ' \
                        'is listening')

    args = parser.parse_args()


    req =  ['get_overviews',
             {'dept': args.d, 'coursenum': args.n,
              'area': args.a, 'title': args.t}]

    try:
        with socket.socket() as sock:
            sock.connect((args.host, args.port))

            with sock.makefile(mode='w', encoding = 'utf-8') as flo:
                flo.write(json.dumps(req)+'\n')

            with sock.makefile(mode='r', encoding = 'utf-8') as flo:
                json_str = flo.readline()

        json_str = json_str.strip()
        status, data = json.loads(json_str)

    except (OSError, ValueError) as excep:
        print(f'{sys.argv[0]}: {excep}', file=sys.stderr)
        sys.exit(1)
    if not status:
        print(f'{sys.argv[0]}: {data}', file=sys.stderr)
        sys.exit(1)

    #write_overviews(data)
    # hint provided in specs for format
    indent = ' ' * (23) # 5 + 1 + 4 + 1 + 6 + 1 + 4 + 1
    # print headers
    print(f'{"ClsId":>5} {"Dept":>4} {"CrsNum":>6} ' \
        f'{"Area":>4} {"Title"}')
    print(f'{"-----":>5} {"----":>4} {"------":>6} ' \
            f'{"----":>4} {"-----"}')

    for overview in data:
        row = (f'{overview["classid"]:>5} {overview["dept"]:>4} '
                f'{overview["coursenum"]:>6} {overview["area"]:>4} '
                f'{overview["title"]}')
        print(textwrap.fill(row, width=72,
                            subsequent_indent=indent,
                            break_long_words=False))


if __name__ == '__main__':
    main()
