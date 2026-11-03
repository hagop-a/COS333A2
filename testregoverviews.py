#!/usr/bin/env python

#-----------------------------------------------------------------------
# testregoverviews.py
# Author: Bob Dondero and Hagop Alajajian
#-----------------------------------------------------------------------
"""Run tests for regoverviews.py."""
import os
import sys
import argparse
import string

#-----------------------------------------------------------------------

MAX_LINE_LENGTH = 72
UNDERLINE = '-' * MAX_LINE_LENGTH

#-----------------------------------------------------------------------

def parse_args():
    """Parse CL args: program name, host, and port"""
    parser = argparse.ArgumentParser(
        description=
        "Test the Registrar's application's handling of " +
        "class overviews requests")
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

    exec_command(program, prefix + '-d COS')
    exec_command(program, prefix + '-d COS -a qr -n 2 -t intro')

    # Add more tests here.

    # first test: check if there are invariants + func failures
    # val tests

    exec_command(program, prefix + '-d DSNTEXIST') # dep doesn't exist
    exec_command(program, prefix + '-n 999999') # num doesn't exist
    exec_command(program, prefix + '-a SSS') # area doesn't exist
    exec_command(program, prefix + '-t NoTitle') # title doesn't exist

    exec_command(program, prefix + '-d COS -n 999') # valid dep, num doesn't exist
    exec_command(program, prefix + '-d cOs -t INTrodUcTion')
    exec_command(program, prefix + '-d cos -t introduction')

    #commented out some tests to fit pylint's limit to 50 tests

    #testing to see if we treet % and _ as ordinary chars instead of wildcards
    exec_command(program, prefix + '-d "%"')
    #exec_command(program, prefix + '-n "%"')
    #exec_command(program, prefix + '-a "%"')
    #exec_command(program, prefix + '-t "%"')

    exec_command(program, prefix + '-d "_"')
    #exec_command(program, prefix + '-n "_"')
    #exec_command(program, prefix + '-a "_"')
    #exec_command(program, prefix + '-t "_"')


    # see if we can handle backslashes correctly
    exec_command(program, prefix + '-d "\\\\"')
    exec_command(program, prefix + '-n "\\\\"')
    #exec_command(program, prefix + '-a "\\\\"')
    #exec_command(program, prefix + '-t "\\\\"')

    # wrong/unknown command line args
    exec_command(program, prefix + '-k flagNotExist')
    exec_command(program, prefix + '-D ECE')
    exec_command(program, prefix + '-dd ECE')

    # no option attached, just extra positional argument
    exec_command(program, prefix + 'noOption') #should reject extra pos argument

    exec_command(program, prefix + '-d') # exit stat 2 and error bc no vals here
    exec_command(program, prefix + '-n')
    exec_command(program, prefix + '-a')
    exec_command(program, prefix + '-t')

    # missing/extra/invalid host/port args
    exec_command(program, '') # no args at all, host/port missing
    exec_command(program, host) # missing port
    exec_command(program, host + ' whatPort') # port isn't int
    exec_command(program, host + ' ' + str(port) + ' extra') # extra pos arg after host/port
    exec_command(program, '-d COS ' + host) # another missing port

    #server isn't available and isn't listening at port
    exec_command(program, host + ' ' + str(port + 1) + ' -d COS') # exit stat 1 err bc wrong port
    exec_command(program, 'host.invalid ' + str(port) +
        ' -d COS') # exit stat 1 error bc host name not resolved

    #validate some parameters to make sure its correctly handled
    exec_command(program, prefix + '-d ""') # empty dep
    exec_command(program, prefix + '-d "   "') # dep with spaces only
    exec_command(program, prefix + '-d C') # 1 char dep
    exec_command(program, prefix + '-d COS -n 324 -a QR -t intro') # valid params for all 4 vals
    exec_command(program, prefix + '-t "introduction to"') # title with spaces
    exec_command(program, prefix + '-t "' + 'z' * 600 + '"') # long title

    # white box test
    exec_command(program, prefix + '-d COS -d MAT') # first -d should be dropped
    exec_command(program, prefix + '-n 104 -n 217')
    exec_command(program, prefix + '-t intro -a QR -n 324 -d COS') # diff order of args than usual
    exec_command(program, prefix + '-d COS -n 324 -a QR -d MAT -n 215 -a HA') # repeat each option

    exec_command(program, prefix + '-d COS -n 333') # yes match
    exec_command(program, prefix + '-d COS -a HA') # probably no match

    # put the option before the pos args host/port
    exec_command(program, '-d COS ' + prefix + '-n 217')

    # black box testing
    exec_command(program, prefix + '-a HA') # one area only
    exec_command(program, prefix + '-n 324') # one course num only
    exec_command(program, prefix + '-t analysis') # title only
    exec_command(program, prefix + '-d COS -t programming') # dept and title together

    # stress test

    for letter in string.ascii_lowercase: # every letter dept substring
        exec_command(program, prefix + '-d ' + letter)

#-----------------------------------------------------------------------

if __name__ == '__main__':
    main()
