import subprocess
import platform
import socket
import requests
import re
from datetime import datetime

class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_with_timestamp(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")

def validate_mac(mac):
    # MAC address regex pattern
    mac_pattern = re.compile("^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
    return bool(mac_pattern.match(mac))

def change_mac(interface, new_mac):
    if not validate_mac(new_mac):
        print_with_timestamp(f"{Color.FAIL}Invalid MAC address format.{Color.ENDC}")
        return

    try:
        subprocess.run(['sudo', 'ifconfig', interface, 'down'], check=True)
        subprocess.run(['sudo', 'ifconfig', interface, 'hw', 'ether', new_mac], check=True)
        subprocess.run(['sudo', 'ifconfig', interface, 'up'], check=True)
        print_with_timestamp(f"{Color.GREEN}MAC Address successfully changed.{Color.ENDC}")
    except subprocess.CalledProcessError as e:
        print_with_timestamp(f"{Color.FAIL}Error changing MAC address: {e}{Color.ENDC}")

def get_external_ip():
    try:
        external_ip = requests.get("https://api64.ipify.org?format=json", timeout=5).json()["ip"]
        return external_ip
    except requests.RequestException:
        print_with_timestamp(f"{Color.FAIL}Error retrieving external IP address: Failed to connect.{Color.ENDC}")
        return None

def renew_ip():
    try:
        subprocess.run(['sudo', 'dhclient', '-r'], check=True)
        subprocess.run(['sudo', 'dhclient'], check=True)
        print_with_timestamp(f"{Color.GREEN}IP addresses successfully renewed.{Color.ENDC}")
    except subprocess.CalledProcessError as e:
        print_with_timestamp(f"{Color.FAIL}Error renewing IP addresses: {e}{Color.ENDC}")

def check_network_connectivity():
    try:
        # Using Google DNS as a reliable host to check connectivity
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

def main():
    os_name = platform.system()

    if os_name == 'Windows':
        print(f"{Color.WARNING}This script is primarily designed for Unix-like systems and may not work correctly on Windows.{Color.ENDC}")
    
    try:
        interface = input("Enter the network interface (e.g., 'eth0'): ")
        print_with_timestamp(f"{Color.BLUE}=== Network Information ==={Color.ENDC}")

        current_mac = subprocess.check_output(['ifconfig', interface]).decode().split('\n')[0].split()[-1]
        internal_ip = subprocess.check_output(['hostname', '-I']).decode().split()[0]

        print_with_timestamp(f"Current MAC Address: {Color.GREEN}{current_mac}{Color.ENDC}")
        print_with_timestamp(f"Internal IP Address: {Color.GREEN}{internal_ip}{Color.ENDC}")

        external_ip = get_external_ip()
        if external_ip:
            print_with_timestamp(f"External IP Address: {Color.GREEN}{external_ip}{Color.ENDC}")

        network_status = check_network_connectivity()
        print_with_timestamp(f"Network Connectivity: {Color.GREEN}{'Connected' if network_status else 'Disconnected'}{Color.ENDC}")

        renew_ip_option = input("Do you want to renew IP addresses? (yes/no): ").lower()

        if renew_ip_option == 'yes':
            renew_ip()

        randomize_internal_ip_option = input("Do you want to randomize the internal IP address? (yes/no): ").lower()

        if randomize_internal_ip_option == 'yes':
            new_internal_ip = subprocess.check_output(['openssl', 'rand', '-hex', '6']).decode().strip()
            print_with_timestamp(f"New Internal IP Address: {Color.GREEN}{new_internal_ip}{Color.ENDC}")

        change_mac_option = input("Do you want to change the MAC address? (yes/no): ").lower()

        if change_mac_option == 'yes':
            new_mac = input("Enter the new MAC address: ")
            change_mac(interface, new_mac)

        # Print all information at the end
        print(f"\n{Color.BLUE}=== Summary ==={Color.ENDC}")
        print_with_timestamp(f"Current MAC Address: {Color.GREEN}{current_mac}{Color.ENDC}")
        print_with_timestamp(f"Internal IP Address: {Color.GREEN}{internal_ip}{Color.ENDC}")
        print_with_timestamp(f"External IP Address: {Color.GREEN}{external_ip}{Color.ENDC}")
        print_with_timestamp(f"Network Connectivity: {Color.GREEN}{'Connected' if network_status else 'Disconnected'}{Color.ENDC}")

    except KeyboardInterrupt:
        print("\nOperation aborted by user.")
    except Exception as e:
        print_with_timestamp(f"{Color.FAIL}An unexpected error occurred: {e}{Color.ENDC}")

if __name__ == "__main__":
    main()
