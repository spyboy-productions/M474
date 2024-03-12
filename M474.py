import platform
import subprocess
import random
import psutil
import requests
import datetime
import socket

# Define colors for output
class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_current_mac(interface):
    try:
        for nic, addrs in psutil.net_if_addrs().items():
            if nic == interface:
                for addr in addrs:
                    if addr.family == psutil.AF_LINK:
                        return addr.address
    except (AttributeError, psutil.Error) as e:
        print(f"{Color.FAIL}Error retrieving MAC address: {e}{Color.ENDC}")
    return None

def get_internal_ip():
    try:
        internal_ip = psutil.net_if_addrs().get('lo', [])[0].address
        return internal_ip
    except (AttributeError, IndexError, psutil.Error) as e:
        print(f"{Color.FAIL}Error retrieving internal IP address: {e}{Color.ENDC}")
    return None

def get_external_ip():
    try:
        response = requests.get('https://api64.ipify.org?format=json')
        return response.json().get('ip')
    except (requests.RequestException, ValueError) as e:
        print(f"{Color.FAIL}Error retrieving external IP address: {e}{Color.ENDC}")
    return None

def renew_ip():
    try:
        subprocess.run(['sudo', 'dhclient', '-r'], check=True)
        subprocess.run(['sudo', 'dhclient'], check=True)
        print(f"{Color.GREEN}IP addresses successfully renewed.{Color.ENDC}")
    except subprocess.CalledProcessError as e:
        print(f"{Color.FAIL}Error renewing IP addresses: {e}{Color.ENDC}")

def generate_random_mac():
    return ':'.join([format(random.randint(0, 255), '02x') for _ in range(6)])

def change_mac(interface, new_mac):
    try:
        subprocess.run(['sudo', 'ifconfig', interface, 'down'], check=True)
        subprocess.run(['sudo', 'ifconfig', interface, 'hw', 'ether', new_mac], check=True)
        subprocess.run(['sudo', 'ifconfig', interface, 'up'], check=True)
        print(f"{Color.GREEN}MAC Address successfully changed.{Color.ENDC}")
    except subprocess.CalledProcessError as e:
        print(f"{Color.FAIL}Error changing MAC address: {e}{Color.ENDC}")

def check_network_connectivity():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False

def print_with_timestamp(message):
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")

def main():
    os_name = platform.system()

    if os_name == 'Windows':
        print(f"{Color.WARNING}This script is primarily designed for Unix-like systems and may not work correctly on Windows.{Color.ENDC}")
    
    try:
        interface = input("Enter the network interface (e.g., 'eth0'): ")
        print_with_timestamp(f"{Color.BLUE}=== Network Information ==={Color.ENDC}")

        current_mac = get_current_mac(interface)
        internal_ip = get_internal_ip()
        external_ip = get_external_ip()

        if current_mac:
            print_with_timestamp(f"Current MAC Address: {Color.GREEN}{current_mac}{Color.ENDC}")

        if internal_ip:
            print_with_timestamp(f"Internal IP Address: {Color.GREEN}{internal_ip}{Color.ENDC}")

        if external_ip:
            print_with_timestamp(f"External IP Address: {Color.GREEN}{external_ip}{Color.ENDC}")

        network_status = check_network_connectivity()
        print_with_timestamp(f"Network Connectivity: {Color.GREEN}{'Connected' if network_status else 'Disconnected'}{Color.ENDC}")

        renew_ip_option = input("Do you want to renew IP addresses? (yes/no): ").lower()

        if renew_ip_option == 'yes' and network_status:
            renew_ip()

        randomize_internal_ip_option = input("Do you want to randomize the internal IP address? (yes/no): ").lower()

        if randomize_internal_ip_option == 'yes':
            new_internal_ip = generate_random_mac()
            print_with_timestamp(f"New Internal IP Address: {Color.GREEN}{new_internal_ip}{Color.ENDC}")

        change_mac_option = input("Do you want to change the MAC address? (yes/no): ").lower()

        if change_mac_option == 'yes':
            new_mac = generate_random_mac()
            change_mac(interface, new_mac)
            print_with_timestamp(f"New MAC Address: {Color.GREEN}{new_mac}{Color.ENDC}")

        # Print all information at the end
        print(f"\n{Color.BLUE}=== Summary ==={Color.ENDC}")
        print(f"Current MAC Address: {Color.GREEN}{current_mac}{Color.ENDC}")
        print(f"Internal IP Address: {Color.GREEN}{internal_ip}{Color.ENDC}")
        print(f"External IP Address: {Color.GREEN}{external_ip}{Color.ENDC}")
        print(f"Network Connectivity: {Color.GREEN}{'Connected' if network_status else 'Disconnected'}{Color.ENDC}")

    except KeyboardInterrupt:
        print("\nOperation aborted by user.")
    except Exception as e:
        print_with_timestamp(f"{Color.FAIL}An unexpected error occurred: {e}{Color.ENDC}")

if __name__ == "__main__":
    main()
