#!/usr/bin/env python

#-----------------------------------------------------------------------
# regserverprelim.py
# Author: Ryan Donoghue and Hagop Alajajian
#-----------------------------------------------------------------------

import os
import sys
import time
import socket
import json
import contextlib
import sqlite3
import argparse

#-----------------------------------------------------------------------

DATABASE_URL = 'file:reg.sqlite'
GENERIC_ERROR = 'A server error occurred. Please contact the ' \
    'system administrator.'

#-----------------------------------------------------------------------

def get_delay(name):
    # A value that cannot be converted to an int is silently 0
    try:
        return int(os.environ.get(name, '0'))
    except ValueError:
        return 0

#-----------------------------------------------------------------------

def consume_cpu_time(delay):
    initial_time = time.process_time()
    while (time.process_time() - initial_time) < delay:
        pass

#-----------------------------------------------------------------------

def delay_server():
    # Called once per request, immediately before database access
    iodelay = get_delay('IODELAY')
    if iodelay > 0:
        time.sleep(iodelay)
    cdelay = get_delay('CDELAY')
    if cdelay > 0:
        consume_cpu_time(cdelay)

#-----------------------------------------------------------------------

def get_overviews(cursor, filters):
    # Normalize arguments: case insensitivity, and treat % and _ as
    # ordinary characters
    par = []
    for key in ('dept', 'coursenum', 'area', 'title'):
        arg = filters[key]
        if arg is None:
            arg = ''
        arg = arg.lower()
        arg = arg.replace('\\', '\\\\')
        arg = arg.replace('%', '\\%')
        arg = arg.replace('_', '\\_')
        par.append('%' + arg + '%')

    query_str = '''
        SELECT classes.classid, crosslistings.dept,
            crosslistings.coursenum, courses.area,
            courses.title
        FROM classes, courses, crosslistings
        WHERE classes.courseid = courses.courseid
            AND courses.courseid = crosslistings.courseid
            AND lower(crosslistings.dept)
                LIKE ? ESCAPE '\\'
            AND lower(crosslistings.coursenum)
                LIKE ? ESCAPE '\\'
            AND lower(courses.area) LIKE ? ESCAPE '\\'
            AND lower(courses.title) LIKE ? ESCAPE '\\'
        ORDER BY crosslistings.dept ASC,
            crosslistings.coursenum ASC,
            classes.classid ASC
    '''
    cursor.execute(query_str, par)

    overviews = []
    row = cursor.fetchone()
    while row is not None:
        overview = {'classid': row[0], 'dept': row[1],
                    'coursenum': row[2], 'area': row[3],
                    'title': row[4]}
        overviews.append(overview)
        row = cursor.fetchone()
    return overviews

#-----------------------------------------------------------------------

def get_details(cursor, classid):
    # Class information; also makes sure classid is in the database
    cursor.execute('''
        SELECT classid, days, starttime, endtime, bldg, roomnum,
            courseid
        FROM classes
        WHERE classes.classid = ?
    ''', [classid])
    row = cursor.fetchone()
    if row is None:
        return None

    details = {'classid': row[0], 'days': row[1], 'starttime': row[2],
               'endtime': row[3], 'bldg': row[4], 'roomnum': row[5],
               'courseid': row[6]}
    courseid = row[6]

    # Cross listings (departments and numbers)
    cursor.execute('''
        SELECT dept, coursenum FROM crosslistings
        WHERE crosslistings.courseid = ?
        ORDER BY dept ASC, coursenum ASC
    ''', [courseid])
    deptcoursenums = []
    row = cursor.fetchone()
    while row is not None:
        deptcoursenums.append(str(row[0]) + ' ' + str(row[1]))
        row = cursor.fetchone()
    details['deptcoursenums'] = deptcoursenums

    # Area, title, description, prerequisites
    cursor.execute('''
        SELECT area, title, descrip, prereqs FROM courses
        WHERE courses.courseid = ?
    ''', [courseid])
    row = cursor.fetchone()
    details['area'] = row[0]
    details['title'] = row[1]
    details['descrip'] = row[2]
    details['prereqs'] = row[3]

    # Professors
    cursor.execute('''
        SELECT profname FROM profs, coursesprofs
        WHERE coursesprofs.courseid = ? AND
        coursesprofs.profid = profs.profid
        ORDER BY profname ASC
    ''', [courseid])
    profnames = []
    row = cursor.fetchone()
    while row is not None:
        profnames.append(row[0])
        row = cursor.fetchone()
    details['profnames'] = profnames

    return details

#-----------------------------------------------------------------------

def handle_request(req):
    # Returns the response: [status, data]
    delay_server()
    try:
        # open db ro, so missing file is error instead of creating
        # new empty one
        with contextlib.closing(
            sqlite3.connect(DATABASE_URL + '?mode=ro',
                isolation_level=None, uri=True)) as connection:

            with contextlib.closing(connection.cursor()) as cursor:
                if req[0] == 'get_overviews':
                    return [True, get_overviews(cursor, req[1])]

                if req[0] == 'get_details':
                    classid = req[1]
                    details = get_details(cursor, classid)
                    if details is None:
                        return [False, f'no class with classid '
                                f'{classid} exists']
                    return [True, details]

                return [False, 'invalid request']

    # Server-side error: report to the system administrator, and send
    # a generic message to the client
    except Exception as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
        return [False, GENERIC_ERROR]

#-----------------------------------------------------------------------

def handle_client(sock):
    with sock.makefile(mode='r', encoding='utf-8') as flo:
        json_str = flo.readline()
    print('Received request')

    try:
        req = json.loads(json_str.rstrip())
        response = handle_request(req)
    except Exception as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
        response = [False, GENERIC_ERROR]

    with sock.makefile(mode='w', encoding='utf-8') as flo:
        flo.write(json.dumps(response) + '\n')
    print('Wrote to client')

#-----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(prog='regserver.py',
        description='Server for the registrar application')
    parser.add_argument('port', type=int,
        help='the port at which the server should listen')
    args = parser.parse_args()

    try:
        server_sock = socket.socket()
        print('Opened server socket')
        if os.name != 'nt':
            server_sock.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('', args.port))
        print('Bound server socket to port')
        server_sock.listen()
        print('Listening')
        while True:
            try:
                sock, _ = server_sock.accept()
                with sock:
                    print('Accepted connection')
                    handle_client(sock)
            except Exception as ex:
                print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
    except Exception as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
        sys.exit(1)

#-----------------------------------------------------------------------

if __name__ == '__main__':
    main()