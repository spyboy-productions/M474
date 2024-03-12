import subprocess
import os
import random
import re
import requests

# Define colors for terminal output
class colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    NC = '\033[0m'

# Function to get internal IP address
def get_internal_ip():
    return subprocess.check_output(["hostname", "-I"]).decode().strip()

# Function to get external IP address
def get_external_ip():
    try:
        response = requests.get("https://api.ipify.org")
        return response.text.strip()
    except requests.RequestException as e:
        print(colors.RED + "Error fetching external IP:", e)
        return None

# Function to renew IP address
def renew_ip():
    try:
        subprocess.run(["dhclient", "-r"])
        subprocess.run(["dhclient"])
    except subprocess.CalledProcessError as e:
        print(colors.RED + "Error renewing IP:", e)

# Print separator
print(colors.GREEN + "=============================================================================================================[+]" + colors.NC)

# Check if script is run as root
if os.geteuid() != 0:
    print(colors.RED + "This script must be run as root")
    exit(1)

# Print current MAC address
current_mac = subprocess.check_output(["ifconfig", "eth0"]).decode()
print("Current MAC address:", re.search(r"ether\s+([0-9a-fA-F:]+)", current_mac).group(1))

# Get internal IP address
internal_ip = get_internal_ip()
if internal_ip:
    print("Internal IP address:", internal_ip)

# Get external IP address
external_ip = get_external_ip()
if external_ip:
    print("External IP address:", external_ip)

# Renew IP address
renew_ip()

# Print separator
print(colors.GREEN + "=============================================================================================================[+]" + colors.NC)

# Print new MAC address
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

# Print new MAC address
print("New MAC address:", f"{mac1}:{mac2}")

# Print separator
print(colors.GREEN + "=============================================================================================================[+]" + colors.NC)

# Print new internal IP address
new_internal_ip = get_internal_ip()
if new_internal_ip:
    print("New internal IP address:", new_internal_ip)

# Print new external IP address
new_external_ip = get_external_ip()
if new_external_ip:
    print("New external IP address:", new_external_ip)
