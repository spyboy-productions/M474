import platform
import subprocess
import random
import psutil
import requests
import datetime
import socket

def get_current_mac(interface):
    try:
        for nic, addrs in psutil.net_if_addrs().items():
            if nic == interface:
                for addr in addrs:
                    if addr.family == psutil.AF_LINK:
                        return addr.address
    except (AttributeError, psutil.Error) as e:
        print(f"Error retrieving MAC address: {e}")
    return None

def get_internal_ip(randomize=False):
    try:
        internal_ip = psutil.net_if_addrs().get('lo', [])[0].address
        if randomize:
            internal_ip = ".".join(map(str, (random.randint(1, 255) for _ in range(4))))
        return internal_ip
    except (AttributeError, IndexError, psutil.Error) as e:
        print(f"Error retrieving internal IP address: {e}")
    return None

def get_external_ip():
    try:
        response = requests.get('https://api64.ipify.org?format=json')
        return response.json().get('ip')
    except (requests.RequestException, ValueError) as e:
        print(f"Error retrieving external IP address: {e}")
    return None

def renew_ip():
    try:
        subprocess.run(['sudo', 'dhclient', '-r'], check=True)
        subprocess.run(['sudo', 'dhclient'], check=True)
        print("IP addresses successfully renewed.")
    except subprocess.CalledProcessError as e:
        print(f"Error renewing IP addresses: {e}")

def generate_random_mac():
    return ':'.join([format(random.randint(0, 255), '02x') for _ in range(6)])

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
        print("This script is primarily designed for Unix-like systems and may not work correctly on Windows.")
    
    try:
        interface = input("Enter the network interface (e.g., 'eth0'): ")
        print_with_timestamp("=== Network Information ===")

        current_mac = get_current_mac(interface)
        internal_ip = get_internal_ip()
        external_ip = get_external_ip()

        if current_mac:
            print_with_timestamp(f"Current MAC Address: {current_mac}")

        if internal_ip:
            print_with_timestamp(f"Internal IP Address: {internal_ip}")

        if external_ip:
            print_with_timestamp(f"External IP Address: {external_ip}")

        network_status = check_network_connectivity()
        print_with_timestamp(f"Network Connectivity: {'Connected' if network_status else 'Disconnected'}")

        renew_ip_option = input("Do you want to renew IP addresses? (yes/no): ").lower()

        if renew_ip_option == 'yes' and network_status:
            renew_ip()

        randomize_internal_ip_option = input("Do you want to randomize the internal IP address? (yes/no): ").lower()

        if randomize_internal_ip_option == 'yes':
            new_internal_ip = get_internal_ip(randomize=True)
            print_with_timestamp(f"New Internal IP Address: {new_internal_ip}")

        change_mac_option = input("Do you want to change the MAC address? (yes/no): ").lower()

        if change_mac_option == 'yes':
            new_mac = generate_random_mac()
            change_mac(interface, new_mac)
            print_with_timestamp(f"New MAC Address: {new_mac}")

    except KeyboardInterrupt:
        print("\nOperation aborted by user.")
    except Exception as e:
        print_with_timestamp(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
