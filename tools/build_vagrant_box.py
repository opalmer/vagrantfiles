#!/usr/bin/env python

from __future__ import print_function

import argparse
import json
import subprocess
import re
import sys
import tarfile
from os import listdir, chdir
from os.path import isfile, dirname, abspath, join
from pprint import pprint

if not sys.platform.startswith("darwin"):
    print("WARNING")
    print("WARNING: This tool was built and tested on OS X using vmware")
    print("WARNING: fusion. It may not operate properly on other platforms")
    print("WARNING")

parser = argparse.ArgumentParser(
    description="Builds a vagrant box from a VMWare host"
)
parser.add_argument("vmdk", help="The main virtual disk image (vmdk)")
parser.add_argument("name", help="The name of the vagrant box")
parser.add_argument("output", help="Write the .box file to this path")
parser.add_argument("--provider", default="vmware_fusion")
parser.add_argument("--description", default="No description provided")
args = parser.parse_args()

if not isfile(args.vmdk):
    parser.error("%s is not a file" % args.vmdk)

if not args.output.endswith(".box"):
    parser.error("Expected `output` to end in .box")

# Defragment and shrink the vmdk
subprocess.check_call(["vmware-vdiskmanager", "-d", args.vmdk])
subprocess.check_call(["vmware-vdiskmanager", "-k", args.vmdk])

# Cleanup any files we don't need.
root = dirname(abspath(args.vmdk))
keep_extensions = re.compile("^.*[.](:?nvram|vmsd|vmx|vmxf|vmdk)$")
remove_paths = []

for path in listdir(root):
    if keep_extensions.match(path) is None and path != "metadata.json":
        remove_paths.append(join(root, path))

if remove_paths:
    pprint(remove_paths)

    answer = ""
    while answer not in ("y", "n"):
        try:
            answer = raw_input("Remove these non-essential files? [y/n] ")
        except NameError:
            answer = input("Remove these non-essential files? [y/n] ")

    if answer == "y":
        subprocess.check_call(["rm", "-rfv"] + remove_paths)
else:
    print("No files to cleanup")

# Write out the metadata file
metadata = {
    "name": args.name,
    "provider": args.provider,
    "description": args.description
}
with open(join(root, "metadata.json"), "w") as metadata_file:
    json.dump(metadata, metadata_file, indent=4)
print("wrote %s" % metadata_file.name)

# Create the .box file
chdir(root)
with tarfile.open(args.output, mode="w:gz") as tar:
    for path in listdir(root):
        if path.endswith(".box"):
            continue

        path = join(root, path)
        print("adding file: %s" % path)
        tar.add(path)

print("DONE.    Wrote %s." % abspath(args.output))
