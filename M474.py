import subprocess
import os
import random
import re
import requests
import platform
import sys

# Define colors for terminal output
class colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    NC = '\033[0m'

# Function to get internal IP address
def get_internal_ip():
    if platform.system() == "Windows":
        ipconfig_output = subprocess.check_output(["ipconfig"]).decode()
        match = re.search(r"IPv4 Address[^\n:]*: ([\d.]+)", ipconfig_output)
        if match:
            return match.group(1)
        else:
            return None
    else:
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
    if platform.system() == "Windows":
        subprocess.run(["ipconfig", "/release"])
        subprocess.run(["ipconfig", "/renew"])
    else:
        try:
            subprocess.run(["dhclient", "-r"])
            subprocess.run(["dhclient"])
        except subprocess.CalledProcessError as e:
            print(colors.RED + "Error renewing IP:", e)

# Function to change MAC address
def change_mac():
    subprocess.run(["macchanger" if platform.system() != "Windows" else "getmac", "-l"], stdout=open("vendor_list.txt", "w"))
    with open("vendor_list.txt", "r") as file:
        mac_list = file.readlines()
    mac1 = random.choice(mac_list).split()[2]
    mac2 = ':'.join(format(random.randint(0x00, 0xff), '02x') for _ in range(3))
    subprocess.run(["macchanger" if platform.system() != "Windows" else "getmac", "-m", f"{mac1}:{mac2}", "eth0"])
    return f"{mac1}:{mac2}"

# Function to revert MAC address to the permanent MAC address
def revert_mac():
    subprocess.run(["macchanger" if platform.system() != "Windows" else "getmac", "-p", "eth0"])

# Print ASCII art
print(colors.YELLOW + """
    ...     ..      ..                                                   
  x*8888x.:*8888: -"888:           xeee    dL ud8Nu  :8c         xeee    
 X   48888X `8888H  8888          d888R    8Fd888888L %8        d888R    
X8x.  8888X  8888X  !888>        d8888R    4N88888888cuR       d8888R    
X8888 X8888  88888   "*8%-      @ 8888R    4F   ^""%""d       @ 8888R    
'*888!X8888> X8888  xH8>      .P  8888R    d       .z8      .P  8888R    
  `?8 `8888  X888X X888>     :F   8888R    ^     z888      :F   8888R    
  -^  '888"  X888  8888>    x"    8888R        d8888'     x"    8888R    
   dx '88~x. !88~  8888>   d8eeeee88888eer    888888     d8eeeee88888eer 
 .8888Xf.888x:!    X888X.:        8888R      :888888            8888R    
:""888":~"888"     `888*"         8888R       888888            8888R    
    "~'    "~        ""        "*%%%%%%**~    '%**%          "*%%%%%%**~ 
""" + colors.NC)

# Print separator
print(colors.GREEN + "===================================================================" + colors.NC)

# Check if script is run as root (on Unix-like systems)
if platform.system() != "Windows" and os.geteuid() != 0:
    print(colors.RED + "This script must be run as root")
    exit(1)

# Get current MAC address (this part remains the same for both systems)
current_mac_info = subprocess.check_output(["ifconfig" if platform.system() != "Windows" else "getmac"]).decode()
current_mac = re.search(r"ether\s+([0-9a-fA-F:]+)", current_mac_info if platform.system() != "Windows" else current_mac_info.split("\n")[3]).group(1)

# Get internal IP address
internal_ip = get_internal_ip()

# Get external IP address
external_ip = get_external_ip()

# Print current MAC address and IP addresses
print("Current MAC address:", colors.GREEN + current_mac + colors.NC)
if internal_ip:
    print("Internal IP address:", colors.GREEN + internal_ip + colors.NC)
if external_ip:
    print("External IP address:", colors.GREEN + external_ip + colors.NC)

# Renew IP address
renew_ip()

# Print separator
print(colors.GREEN + "===================================================================" + colors.NC)

# Check if command-line argument is provided to revert MAC address
if len(sys.argv) > 1 and sys.argv[1] == "revert":
    print(colors.GREEN + "Reverting MAC address to permanent MAC address..." + colors.NC)
    revert_mac()
    print(colors.GREEN + "MAC address reverted successfully!" + colors.NC)
    exit(0)

# Change MAC address
new_mac = change_mac()

# Print new MAC address
print("New MAC address:", colors.GREEN + new_mac + colors.NC)

# Print separator
print(colors.GREEN + "===================================================================" + colors.NC)

# Print new internal IP address
new_internal_ip = get_internal_ip()
if new_internal_ip:
    print("New internal IP address:", colors.GREEN + new_internal_ip + colors.NC)

# Print new external IP address
new_external_ip = get_external_ip()
if new_external_ip:
    print("New external IP address:", colors.GREEN + new_external_ip + colors.NC)

print(colors.YELLOW + "To revert MAC address to the permanent MAC address, run the script with the argument 'revert'." + colors.NC)
