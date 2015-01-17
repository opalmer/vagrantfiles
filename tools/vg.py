#!/usr/bin/env python

import re
import argparse
import subprocess
from collections import namedtuple

Host = namedtuple("Status", ["id", "name", "provider", "state", "path"])


def global_status():
    regex = re.compile(
        # vagrant id
        "^([a-f0-9]{7})\s+"    # id

        # name of host (what the user will input)
        "(\w+)\s+"

        # the vagrant adapter
        "(\w+)\s+"

        # current host state
        "(running|not created|not running|"
        "poweroff|aborted|saved|stopped|frozen)\s+"

        # root path of the vagrant image
        "(.*)$"    # path
    )

    output = subprocess.check_output(["vagrant", "global-status"])
    for line in output.splitlines():
        line = line.strip()
        match = regex.match(line)
        if match is not None:
            yield Host(*match.groups())


def run(args):
    print " ".join(args)
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        print "Command failed: %s" % " ".join(args)



parser = argparse.ArgumentParser(
    description="Wrapper around the 'vagrant' command")
parser.add_argument(
    "operation", help="The operation to perform",
    choices=(
        "up", "down", "resume", "destroy", "ssh", "list", "ls", "status", "st")
)
parser.add_argument(
    "hostnames", help="The vagrant host(s) to perform the operation on.",
    nargs="*"
)
parser.add_argument(
    "-c", "--command", help="Used in conjunction with the 'ssh' command "
                            "to send commands to a host or hosts."
)
args = parser.parse_args()
all_status = list(global_status())

if args.operation in ("list", "ls"):
    for status in all_status:
        print status

elif args.operation in ("status", "st"):
    for status in all_status:
        print status.id, status.name, status.state

else:
    for hostname in args.hostnames:
        for status in all_status:
            if status.name == hostname:
                operation = args.operation
                if args.operation == "down":
                    operation = "halt"

                cmd = ["vagrant", operation, status.id]
                if args.operation == "ssh" and args.command:
                    cmd += ["--", args.command]

                run(cmd)
                break

        else:
            parser.error("Vagrant host %r does not exist" % hostname)
