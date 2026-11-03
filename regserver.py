#!/usr/bin/env python

#-----------------------------------------------------------------------
# regserver.py
# Author: Hagop Alajajian
#-----------------------------------------------------------------------
"""Server for registrar app. It listen on a port and replies
to various client requests with class overviews or class details."""

import os
import sys
import time
import socket
import threading
import json
import contextlib
import sqlite3
import argparse


DATABASE_URL = 'file:reg.sqlite'
GEN_ERROR = 'A server error occurred. Please contact the ' \
    'system administrator.'

def delay_fetch(name):
    """Return environment variable's val as an int, or default to a 0 if something fails."""

    # A value that cannot be converted to an int is 0
    try:
        return int(os.environ.get(name, '0'))
    except ValueError:
        return 0

def overviews_fetch(cursor, filters):
    """Try to find some class by using classid and return details, or None if no class exists."""

    # Normalize args for case insensitivity,
    # make sure % and _ aren't special chars
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

def details_fetch(cursor, classid):
    """Provide details dict for classid, or None if class can't be found."""
    # Class info and check to make sure classid is in db
    cursor.execute('''
        SELECT classid, days, starttime, endtime, bldg, roomnum,
            courseid
        FROM classes
        WHERE classes.classid = ?
    ''', [classid])
    row = cursor.fetchone()
    if row is None:
        return None

    det = {'classid': row[0], 'days': row[1], 'starttime': row[2],
               'endtime': row[3], 'bldg': row[4], 'roomnum': row[5],
               'courseid': row[6]}
    courseid = row[6]

    # Cross listings (dept + nums)
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
    det['deptcoursenums'] = deptcoursenums

    # Area, title, description, prerequisites into details
    cursor.execute('''
        SELECT area, title, descrip, prereqs FROM courses
        WHERE courses.courseid = ?
    ''', [courseid])
    row = cursor.fetchone()
    det['area'] = row[0]
    det['title'] = row[1]
    det['descrip'] = row[2]
    det['prereqs'] = row[3]

    # Profs
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
    det['profnames'] = profnames

    return det

def request_take(json_str):

    """Takes in a JSON request and returns the response: [status, data]"""
    # delay this 1/request, right before db access

    iodelay = delay_fetch('IODELAY')
    if iodelay > 0:
        time.sleep(iodelay)
    cdelay = delay_fetch('CDELAY')
    if cdelay > 0:
        start = time.thread_time()
        while cdelay > (time.thread_time() - start):
            pass

    try:

        req = json.loads(json_str.rstrip())

        # open db ro, so missing file is err instead of creating
        # new empty one
        with contextlib.closing(
            sqlite3.connect(DATABASE_URL + '?mode=ro',
                isolation_level=None, uri=True)) as connection:

            with contextlib.closing(connection.cursor()) as cursor:
                if req[0] == 'get_overviews':
                    return [True, overviews_fetch(cursor, req[1])]

                if req[0] == 'get_details':
                    classid = req[1]
                    details = details_fetch(cursor, classid)
                    if details is None:
                        return [False, f'no class with classid '
                                f'{classid} exists']
                    return [True, details]

                return [False, 'invalid request']

    # Err: send generic message to client
    # catch specific errors that would occur rather than the broad exception
    except Exception as excep:
        print(f'{sys.argv[0]}: {excep}', file=sys.stderr)
        return [False, GEN_ERROR]

def proc_client(sock):
    """Process client request on the sock and send back some response"""
    with sock.makefile(mode='r', encoding='utf-8') as flo:
        json_str = flo.readline()
    print('Received request')

    response = request_take(json_str)

    with sock.makefile(mode='w', encoding='utf-8') as flo:
        flo.write(json.dumps(response) + '\n')
    print('Wrote to client')

def proc_client_thread(sock):
    """Process client request on the sock and send back some response"""
    try:
        with sock:
            proc_client(sock)
    except (OSError, ValueError) as excep:
        print(f'{sys.argv[0]}: {excep}', file=sys.stderr)

def main():
    """This is the main func for server, where it reads port from CL and serves client ongoingly."""
    parser = argparse.ArgumentParser(prog='regserver.py',
        description='Server for the registrar app')
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
                print('Accepted connection')
                thread = threading.Thread(
                    target = proc_client_thread, args=(sock,))
                thread.start()
            except OSError as excep:
                print(f'{sys.argv[0]}: {excep}', file=sys.stderr)
    except OSError as excep:
        print(f'{sys.argv[0]}: {excep}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
