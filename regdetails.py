#-----------------------------------------------------------------------
# regdetails.py
# Author: Hagop Alajajian
#-----------------------------------------------------------------------
"""Registrar app client: query to find and show class details."""
import sys
import socket
import json
import argparse
import textwrap

#-----------------------------------------------------------------------
LINE_WIDTH = 72
#-----------------------------------------------------------------------

def print_class_details(class_info):
    """Print class info, including id, days, start/end times, building, and room."""
    print("-------------")
    print("Class Details")
    print("-------------")


    print(textwrap.fill("Class Id: " + str(class_info['classid']), LINE_WIDTH))
    print(textwrap.fill("Days: " + class_info['days'], LINE_WIDTH))
    print(textwrap.fill("Start Time: " + class_info['starttime'], LINE_WIDTH))
    print(textwrap.fill("End Time: " + class_info['endtime'], LINE_WIDTH))
    print(textwrap.fill("Building: " + class_info['bldg'], LINE_WIDTH))
    print(textwrap.fill("Room: " + class_info['roomnum'], LINE_WIDTH))



def print_course_details(course_info):
    """Print the course details from the details dict."""
    print("--------------")
    print("Course Details")
    print("--------------")

    print(textwrap.fill("Course Id: " + str(course_info['courseid']),
                        LINE_WIDTH))


    combined_listings_str = ", ".join(course_info['deptcoursenums'])
    print(textwrap.fill("Departments and Numbers: "
                        + combined_listings_str, LINE_WIDTH))
    print(textwrap.fill("Area: " + course_info['area'], LINE_WIDTH))
    print(textwrap.fill("Title: " + course_info['title'], LINE_WIDTH,
                        subsequent_indent='   '))
    print(textwrap.fill("Description: " + course_info['descrip'],
                        LINE_WIDTH, subsequent_indent='   '))
    print(textwrap.fill("Prerequisites: " + course_info['prereqs'],
                        LINE_WIDTH, subsequent_indent='   '))

    combined_profs_str = ", ".join(course_info['profnames'])

    print(textwrap.fill("Professors: " +
                        combined_profs_str, LINE_WIDTH))

def main():
    """Request details from server and print the results."""
    parser = argparse.ArgumentParser(prog='regdetails.py', description=
                'Registrar application: show details about a class')
    parser.add_argument('host',
                        help='the computer on which the server is ' \
                        'running')
    parser.add_argument('port', type=int,
                        help='the port at which the server is ' \
                        'listening')
    parser.add_argument(
        'classid', help="the id of the class whose details " \
        "should be shown", type=int)
    args = parser.parse_args()

    req = ['get_details', args.classid]

    try:
        with socket.socket() as sock:
            sock.connect((args.host, args.port))

            with sock.makefile(mode='w', encoding='utf-8') as flo:
                flo.write(json.dumps(req) + '\n')

            with sock.makefile(mode='r', encoding='utf-8') as flo:
                json_str = flo.readline()

            json_str = json_str.rstrip()
            status, data = json.loads(json_str)
    except (OSError, ValueError) as excep:
        print(f'{sys.argv[0]}: {excep}', file=sys.stderr)
        sys.exit(1)
    if not status:
        print(f'{sys.argv[0]}: {data}', file=sys.stderr)
        sys.exit(1)

    print_class_details(data)
    print_course_details(data)

if __name__ == '__main__':
    main()
