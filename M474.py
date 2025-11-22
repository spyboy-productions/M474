import subprocess
import os
import random
import re
import requests
import platform
import sys
import json

# Terminal colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    NC = '\033[0m'

BANNER = Colors.YELLOW + r"""
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
""" + Colors.NC

SEP = Colors.GREEN + "=" * 67 + Colors.NC
BACKUP_FILE = os.path.expanduser("~/.mac_spoofer_backup.json")


# ---------- Backup helpers ----------

def load_backup():
    if not os.path.exists(BACKUP_FILE):
        return {}
    try:
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_backup(data):
    try:
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(Colors.RED + f"[!] Failed to save backup file: {e}" + Colors.NC)


# ---------- IP helpers ----------

def get_internal_ip():
    system = platform.system()
    try:
        if system == "Windows":
            output = subprocess.check_output(["ipconfig"], encoding="utf-8", errors="ignore")
            matches = re.findall(r"IPv4 Address[^\n:]*:\s*([\d.]+)", output)
            # skip APIPA 169.254.x.x
            for ip in matches:
                if not ip.startswith("169.254."):
                    return ip
            return matches[0] if matches else None
        else:
            output = subprocess.check_output(["hostname", "-I"], encoding="utf-8")
            ips = [ip for ip in output.split() if ip and not ip.startswith("127.")]
            return ips[0] if ips else None
    except Exception as e:
        print(Colors.RED + f"[!] Error getting internal IP: {e}" + Colors.NC)
        return None


def get_external_ip(timeout=5):
    try:
        resp = requests.get("https://api.ipify.org", timeout=timeout)
        resp.raise_for_status()
        return resp.text.strip()
    except requests.RequestException as e:
        print(Colors.RED + f"[!] Error fetching external IP: {e}" + Colors.NC)
        return None


# ---------- Linux interface / MAC helpers ----------

def detect_primary_interface_linux():
    # Prefer `ip` output
    try:
        output = subprocess.check_output(["ip", "-o", "link", "show"], encoding="utf-8")
        candidates = []
        for line in output.splitlines():
            m = re.match(r"\d+:\s+([^:]+):\s+<([^>]+)>", line)
            if not m:
                continue
            name, flags = m.group(1), m.group(2).split(",")
            if name == "lo":
                continue
            candidates.append((name, flags))
        # Prefer interfaces that are UP
        for name, flags in candidates:
            if "UP" in flags:
                return name
        # Fallback: first non-lo
        return candidates[0][0] if candidates else None
    except Exception:
        # Fallback to ifconfig
        try:
            output = subprocess.check_output(["ifconfig"], encoding="utf-8", errors="ignore")
            blocks = re.split(r"\n(?=\S)", output)
            for block in blocks:
                if block.startswith("lo"):
                    continue
                name = block.split()[0]
                return name
        except Exception:
            return None
    return None


def get_current_mac_linux(iface):
    # Try sysfs first
    path = f"/sys/class/net/{iface}/address"
    try:
        with open(path, "r", encoding="utf-8") as f:
            mac = f.read().strip()
            if mac:
                return mac
    except Exception:
        pass
    # Fallback to `ip`
    try:
        output = subprocess.check_output(["ip", "link", "show", iface], encoding="utf-8", errors="ignore")
        m = re.search(r"link/\w+\s+([0-9a-fA-F:]{17})", output)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def generate_random_mac():
    # Locally administered unicast MAC (LAA)
    # 1st octet: set local bit (0x02), ensure unicast (LSB = 0)
    first_octet = 0x02
    mac_bytes = [first_octet] + [random.randint(0x00, 0xFF) for _ in range(5)]
    return ":".join(f"{b:02x}" for b in mac_bytes)


def change_mac_linux(iface):
    original_mac = get_current_mac_linux(iface)
    if not original_mac:
        print(Colors.RED + f"[!] Could not determine current MAC for {iface}" + Colors.NC)
        return None, None

    backup = load_backup()
    if iface not in backup:
        backup[iface] = original_mac
        save_backup(backup)

    new_mac = generate_random_mac()
    try:
        subprocess.run(["ip", "link", "set", "dev", iface, "down"], check=True)
        subprocess.run(["ip", "link", "set", "dev", iface, "address", new_mac], check=True)
        subprocess.run(["ip", "link", "set", "dev", iface, "up"], check=True)
        return original_mac, new_mac
    except subprocess.CalledProcessError as e:
        print(Colors.RED + f"[!] Failed to change MAC on {iface}: {e}" + Colors.NC)
        return None, None


def revert_mac_linux(iface):
    backup = load_backup()
    original_mac = backup.get(iface)
    if not original_mac:
        print(Colors.RED + f"[!] No backup MAC found for {iface}. Cannot revert." + Colors.NC)
        return False
    try:
        subprocess.run(["ip", "link", "set", "dev", iface, "down"], check=True)
        subprocess.run(["ip", "link", "set", "dev", iface, "address", original_mac], check=True)
        subprocess.run(["ip", "link", "set", "dev", iface, "up"], check=True)
        print(Colors.GREEN + f"[+] Reverted {iface} MAC to {original_mac}" + Colors.NC)
        return True
    except subprocess.CalledProcessError as e:
        print(Colors.RED + f"[!] Failed to revert MAC on {iface}: {e}" + Colors.NC)
        return False


# ---------- IP renew ----------

def renew_ip(system, iface=None):
    print(Colors.YELLOW + "[*] Renewing IP address..." + Colors.NC)
    try:
        if system == "Windows":
            subprocess.run(["ipconfig", "/release"], check=False)
            subprocess.run(["ipconfig", "/renew"], check=False)
        else:
            # Best-effort: try iface-specific dhclient, then generic
            if iface:
                subprocess.run(["dhclient", "-r", iface], check=False)
                subprocess.run(["dhclient", iface], check=False)
            else:
                subprocess.run(["dhclient", "-r"], check=False)
                subprocess.run(["dhclient"], check=False)
    except Exception as e:
        print(Colors.RED + f"[!] Error renewing IP: {e}" + Colors.NC)


# ---------- Main ----------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Simple IP & MAC changer")
    parser.add_argument("--revert", action="store_true",
                        help="Revert MAC to original (Linux only)")
    parser.add_argument("--iface",
                        help="Network interface to use (Linux only, auto-detected if omitted)")
    parser.add_argument("--no-ip-renew", action="store_true",
                        help="Do not renew IP after MAC change/revert")
    args = parser.parse_args()

    system = platform.system()

    print(BANNER)
    print(SEP)

    is_linux = (system == "Linux")
    if is_linux:
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            print(Colors.RED + "[!] This script should be run as root on Linux for MAC/IP changes." + Colors.NC)
            print(Colors.YELLOW + "[i] It will still show info but will NOT modify MAC/IP." + Colors.NC)
            can_modify = False
        else:
            can_modify = True
    else:
        can_modify = False  # MAC spoofing not implemented for Windows in this script

    iface = None
    if is_linux:
        iface = args.iface or detect_primary_interface_linux()
        if not iface:
            print(Colors.RED + "[!] Could not detect a primary network interface." + Colors.NC)
        else:
            print(Colors.GREEN + f"[+] Using interface: {iface}" + Colors.NC)

    # Show current MAC (Linux) or adapters (Windows)
    if is_linux and iface:
        cur_mac = get_current_mac_linux(iface)
        if cur_mac:
            print("Current MAC address:", Colors.GREEN + cur_mac + Colors.NC)
    elif system == "Windows":
        try:
            output = subprocess.check_output(["getmac"], encoding="utf-8", errors="ignore")
            print("Current MAC addresses:\n" + Colors.GREEN + output + Colors.NC)
        except Exception as e:
            print(Colors.RED + f"[!] Failed to get MAC addresses on Windows: {e}" + Colors.NC)

    # IP info (before)
    internal_ip = get_internal_ip()
    external_ip = get_external_ip()
    if internal_ip:
        print("Internal IP address:", Colors.GREEN + internal_ip + Colors.NC)
    if external_ip:
        print("External IP address:", Colors.GREEN + external_ip + Colors.NC)

    print(SEP)

    # ----- Revert flow -----
    if args.revert:
        if not is_linux or not iface:
            print(Colors.RED + "[!] Revert is only supported on Linux with a valid interface." + Colors.NC)
            sys.exit(1)
        if not can_modify:
            print(Colors.RED + "[!] Cannot revert MAC without root privileges." + Colors.NC)
            sys.exit(1)

        revert_mac_linux(iface)
        if not args.no_ip_renew:
            renew_ip(system, iface)

        print(SEP)
        new_internal = get_internal_ip()
        new_external = get_external_ip()
        if new_internal:
            print("Current internal IP:", Colors.GREEN + new_internal + Colors.NC)
        if new_external:
            print("Current external IP:", Colors.GREEN + new_external + Colors.NC)
        return

    # ----- Change MAC (Linux only) -----
    if is_linux and iface and can_modify:
        orig_mac, new_mac = change_mac_linux(iface)
        if new_mac:
            print("New MAC address:", Colors.GREEN + new_mac + Colors.NC)
        else:
            print(Colors.RED + "[!] MAC was not changed." + Colors.NC)
    elif is_linux and not can_modify:
        print(Colors.YELLOW + "[i] Skipping MAC change because we are not root." + Colors.NC)
    else:
        print(Colors.YELLOW + "[i] MAC spoofing is not supported on this OS in this script." + Colors.NC)

    # Renew IP unless disabled
    if not args.no_ip_renew and (is_linux and can_modify or system == "Windows"):
        renew_ip(system, iface if is_linux else None)

    print(SEP)

    # Show updated IP info
    new_internal = get_internal_ip()
    new_external = get_external_ip()
    if new_internal:
        print("New internal IP address:", Colors.GREEN + new_internal + Colors.NC)
    if new_external:
        print("New external IP address:", Colors.GREEN + new_external + Colors.NC)

    if is_linux and iface:
        print(Colors.YELLOW + f"\nTo revert {iface} MAC to the original, run this script with --revert" + Colors.NC)


if __name__ == "__main__":
    main()
