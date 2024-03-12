import subprocess
import os
import random
import re

# Define colors for terminal output
class colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    NC = '\033[0m'

# Check if script is run as root
if os.geteuid() != 0:
    print(colors.RED + "This script must be run as root")
    exit(1)

# Run macchanger -l command and redirect output to vendor_list.txt
subprocess.run(["macchanger", "-l"], stdout=open("vendor_list.txt", "w"))

# Get a list of MAC addresses and select a random one
with open("vendor_list.txt", "r") as file:
    mac_list = file.readlines()
mac1 = random.choice(mac_list).split()[2]

# Generate a random MAC address
mac2 = ':'.join(format(random.randint(0x00, 0xff), '02x') for _ in range(3))

# Change MAC address of interface eth0
subprocess.run(["macchanger", "-m", f"{mac1}:{mac2}", "eth0"])

# Find the path of the script
path = subprocess.check_output(["find", "/", "-name", "n0Mac.sh"]).decode().splitlines()[0]

# Check if the script is already set up in the crontab
if re.search("n0Mac.sh", open("/etc/crontab").read()):
    exit(1)
else:
    with open("/etc/crontab", "a") as file:
        file.write("@reboot root /bin/sh " + path + "\n")
