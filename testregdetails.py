#!/usr/bin/env python

#-----------------------------------------------------------------------
# testregdetails.py
# Author: Bob Dondero
#-----------------------------------------------------------------------
"""Run tests for regdetails.py."""
import os
import sys
import argparse

#-----------------------------------------------------------------------

MAX_LINE_LENGTH = 72
UNDERLINE = '-' * MAX_LINE_LENGTH

#-----------------------------------------------------------------------

def parse_args():
    """Parse CL args: program name, host, and port"""

    parser = argparse.ArgumentParser(
        description=
        "Test the Registrar's application's handling of " +
        "class details requests")
    parser.add_argument('program', metavar='program', type=str,
        help='the client program to run')
    parser.add_argument('host', metavar='host', type=str,
        help='the host on which the server is running')
    parser.add_argument('port', metavar='port', type=int,
        help='the port at which the server is listening')
    args = parser.parse_args()

    return (args.program, args.host, args.port)

#-----------------------------------------------------------------------

def print_flush(message):
    """Print message and flush it to keep output ordered with subprocess output."""

    print(message)
    sys.stdout.flush()

#-----------------------------------------------------------------------

def exec_command(program, args):
    """Run test command, while printing CL and exit status"""
    print_flush(UNDERLINE)
    command = 'python ' + program + ' ' + args
    print_flush(command)
    print_flush(UNDERLINE)

    exit_status = os.system(command)
    if os.name == 'nt':  # Running on MS Windows?
        print_flush('Exit status = ' + str(exit_status))
    else:
        print_flush('Exit status = ' + str(os.WEXITSTATUS(exit_status)))

#-----------------------------------------------------------------------

def main():
    """Run all the tests here in main."""

    program, host, port = parse_args()

    exec_command(program, '-h')

    prefix = host + ' ' + str(port) + ' '

    exec_command(program, prefix + '8321')

    # Add more tests here.

     # Add more tests here.

    # existing classids
    exec_command(program, prefix + '8456')
    exec_command(program, prefix + '9240')
    exec_command(program, prefix + '8462')
    exec_command(program, prefix + '8463')
    exec_command(program, prefix + '9577')

    # boundary classids (lowest + highest)
    exec_command(program, prefix + '1') #unrealistic min
    exec_command(program, prefix + '99999') #unrealistic max

    exec_command(program, prefix + '7838') #real min
    exec_command(program, prefix + '10264') #real max


    # non-existing classids
    exec_command(program, prefix + '0')
    exec_command(program, prefix + '-1')
    exec_command(program, prefix + '99999999999999')

    # classid with leading zeros and + sign
    exec_command(program, prefix + '08321')
    exec_command(program, prefix + '+8321')

    #  command-line arguments that aren't correct
    exec_command(program, prefix + 'abc')
    exec_command(program, prefix + '8456x')
    exec_command(program, prefix + '84.56')
    exec_command(program, prefix + '"8456 8457"')
    exec_command(program, prefix + '""')
    exec_command(program, prefix + '"   "')
    exec_command(program, prefix + '%')
    exec_command(program, prefix + '_')
    exec_command(program, prefix + '"\\\\"')
    exec_command(program, prefix + '8456 8457')
    exec_command(program, prefix + '8456 more')
    exec_command(program, prefix + '-x 8456')
    exec_command(program, prefix + '-d 8456')

    # host/port args that are missing or not valid or extra
    exec_command(program, '')
    exec_command(program, host)
    exec_command(program, host + ' ' + str(port))
    exec_command(program, host + ' whatPort 8456')
    exec_command(program, '8456')

    # no server that is listening
    exec_command(program, host + ' ' + str(port + 1) + ' 8456')
    exec_command(program, 'nohost.invalid' + str(port) +
        ' 8456')

if __name__ == '__main__':
    main()
