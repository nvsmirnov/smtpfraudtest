#!/usr/bin/env python3
# coding=UTF-8

from __future__ import print_function

import os
import sys
import pexpect
import argparse

import logging
from logging import debug, info, warning, error, critical
logfile = None

args = None

def parse_args():
    parser = argparse.ArgumentParser(
            description="Test if SMTP server can pass mail with specific from/to's",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )
    parser.add_argument("-d", "--debug", action='store_true',
            help="Enable debug"
            )
    parser.add_argument("-c", "--connectto", type=str, required=True,
            help="SMTP server to connect to"
            )
    parser.add_argument("-H", "--helo", type=str, default="test",
            help="String to use in HELO"
            )
    parser.add_argument("-r", "--recipient", type=str, required=True,
            help="Mail recipient"
            )
    parser.add_argument("-s", "--sender", type=str, required=True,
            help="Sender address to use in SMTP session"
            )
    parser.add_argument("-f", "--headerfrom", type=str,
            help="Sender address to use in mail header (default is the same as -s)"
            )
    parser.add_argument("-F", "--omitfrom", type=str, action='store_true', default=False,
            help="Do not add 'From:' header to message"
            )
    parser.add_argument("-S", "--subject", type=str, default="smtptest",
            help="Mail subject"
            )
    parser.add_argument("-a", "--addheader", type=str, default=[], action="append",
            help="Add arbitrary text to header part of message (use this to add header)"
            )

    global args
    args = parser.parse_args()

    if args.debug:
        rootLogger.setLevel(logging.DEBUG)
        debug("Enabled debug")

    if not args.headerfrom:
        args.headerfrom = args.sender

    return True

if __name__ == '__main__':
    logFormatterFile = logging.Formatter("%(asctime)s [{0}] [%(levelname)-5.5s] %(message)s".format(os.getpid()))
    logFormatterConsole = logging.Formatter("%(message)s")

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatterConsole)
    rootLogger.addHandler(consoleHandler)

    if logfile:
        fileHandler = logging.FileHandler(logfile)
        fileHandler.setFormatter(logFormatterFile)
        rootLogger.addHandler(fileHandler)

    if not parse_args():
        sys.exit(1)

    try:
        smtp = pexpect.spawn('telnet', [args.connectto, "25"], timeout=3)
    except pexpect.ExceptionPexpect as e:
        debug("Got exception:", exc_info=True)
        error(e)
        sys.exit(1)

    try:
        smtp.expect('\n220')
        smtp.sendline("HELO %s" % (args.helo))
        smtp.expect('\n250')
        smtp.sendline("MAIL FROM: <%s>" % (args.sender))
        smtp.expect('\n250')
        smtp.sendline("RCPT TO: <%s>" % (args.recipient))
        smtp.expect('\n250')
        smtp.sendline("DATA")
        smtp.expect('\n354')
        smtp.sendline("Subject: %s" % (args.subject))
        if not args.omitfrom:
            smtp.sendline("From: %s" % (args.headerfrom))
        for header in args.addheader:
            smtp.sendline(header)
        smtp.sendline("")
        smtp.sendline("This is a test message with subject %s, sent with mail from='%s' and header from='%s', and additional headers=%s" % (args.subject, args.sender, args.recipient, args.addheader))
        smtp.sendline(".")
        smtp.expect('\n250')
        smtp.sendline("QUIT")
        smtp.expect('\n221')
    except pexpect.ExceptionPexpect as e:
        debug("Got exception:", exc_info=True)
        error(e)
        sys.exit(1)

    info("Done.")


# vim:expandtab tabstop=8 shiftwidth=4 softtabstop=4
