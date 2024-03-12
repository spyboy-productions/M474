import subprocess
import random
import os

# Define colors for console output
class Color:
    GREEN = '\033[1;32m'
    RED = '\033[1;31m'
    NC = '\033[0m'  # No Color

# Function to execute shell commands
def execute_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode().strip(), error.decode().strip()

# Check if script is run as root
def check_root():
    if os.geteuid() != 0:
        print(f"{Color.RED}This script must be run as root{Color.NC}")
        exit(1)

# Function to change MAC address
def change_mac_address(interface):
    # Get list of vendor MAC addresses
    vendor_list, _ = execute_command("macchanger -l")
    vendor = random.choice(vendor_list.splitlines()).split()[2]  # Select a random vendor MAC address
    new_mac = ':'.join([f"{random.randint(0x00, 0xff):02x}" for _ in range(3)])  # Generate a random MAC address
    new_mac_address = f"{vendor}:{new_mac}"  # Combine vendor and random MAC address
    output, error = execute_command(f"macchanger -m {new_mac_address} {interface}")  # Change MAC address
    if "New MAC" in output:
        print(f"{Color.GREEN}MAC Address successfully changed.{Color.NC}")
        print(f"New MAC Address: {new_mac_address}")
    else:
        print(f"{Color.RED}Error changing MAC address: {error}{Color.NC}")

# Function to renew IP addresses
def renew_ip_addresses():
    output, error = execute_command("dhclient -r")  # Release current IP addresses
    if not error:
        output, error = execute_command("dhclient")  # Renew IP addresses
        if not error:
            print(f"{Color.GREEN}IP addresses successfully renewed.{Color.NC}")
        else:
            print(f"{Color.RED}Error renewing IP addresses: {error}{Color.NC}")
    else:
        print(f"{Color.RED}Error releasing IP addresses: {error}{Color.NC}")

# Function to randomize internal IP address
def randomize_internal_ip():
    new_ip = ".".join([str(random.randint(0, 255)) for _ in range(4)])  # Generate a random internal IP address
    output, error = execute_command(f"ifconfig eth0 {new_ip}")  # Change internal IP address
    if not error:
        print(f"{Color.GREEN}New Internal IP Address: {new_ip}{Color.NC}")
    else:
        print(f"{Color.RED}Error randomizing internal IP address: {error}{Color.NC}")

# Main function
def main():
    check_root()  # Check if script is run as root
    interface = input("Enter the network interface (e.g., 'eth0'): ")
    change_mac_address(interface)  # Change MAC address
    renew_ip_addresses()  # Renew IP addresses
    randomize_internal_ip()  # Randomize internal IP address

if __name__ == "__main__":
    main()
