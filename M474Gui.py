#!/usr/bin/env python3

import subprocess
import os
import random
import re
import requests
import platform
import sys
import json
import threading
from typing import Optional, Tuple, Dict
import tkinter as tk
from tkinter import messagebox, scrolledtext

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    from ttkbootstrap.dialogs import Messagebox
except ImportError:
    print("Error: ttkbootstrap is required. Install it with: pip install ttkbootstrap")
    sys.exit(1)


BACKUP_FILE = os.path.expanduser("~/.m474_backup.json")
APP_TITLE = "M474"
APP_VERSION = "2.0.0"


class SecureConfig:
    
    @staticmethod
    def load_backup() -> Dict[str, str]:
        if not os.path.exists(BACKUP_FILE):
            return {}
        try:
            if hasattr(os, 'stat'):
                file_stat = os.stat(BACKUP_FILE)
                if file_stat.st_mode & 0o044:
                    print(f"Warning: Backup file has insecure permissions")
            
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return {}
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading backup: {e}")
            return {}

    @staticmethod
    def save_backup(data: Dict[str, str]) -> bool:
        try:
            temp_file = f"{BACKUP_FILE}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            if hasattr(os, 'chmod'):
                os.chmod(temp_file, 0o600)
            
            os.replace(temp_file, BACKUP_FILE)
            return True
        except (IOError, OSError) as e:
            print(f"Error saving backup: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False

    @staticmethod
    def delete_backup() -> bool:
        try:
            if os.path.exists(BACKUP_FILE):
                os.remove(BACKUP_FILE)
            return True
        except (IOError, OSError) as e:
            print(f"Error deleting backup: {e}")
            return False


class NetworkManager:
    
    @staticmethod
    def get_internal_ip() -> Optional[str]:
        system = platform.system()
        try:
            if system == "Windows":
                output = subprocess.check_output(
                    ["ipconfig"], 
                    encoding="utf-8", 
                    errors="ignore",
                    timeout=5
                )
                matches = re.findall(r"IPv4 Address[^\n:]*:\s*([\d.]+)", output)
                for ip in matches:
                    if not ip.startswith("169.254."):
                        return ip
                return matches[0] if matches else None
            else:
                output = subprocess.check_output(
                    ["hostname", "-I"], 
                    encoding="utf-8",
                    timeout=5
                )
                ips = [ip for ip in output.split() if ip and not ip.startswith("127.")]
                return ips[0] if ips else None
        except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            print(f"Error getting internal IP: {e}")
            return None

    @staticmethod
    def get_external_ip(timeout: int = 5) -> Optional[str]:
        try:
            resp = requests.get("https://api.ipify.org", timeout=timeout)
            resp.raise_for_status()
            ip = resp.text.strip()
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                return ip
            return None
        except requests.RequestException as e:
            print(f"Error fetching external IP: {e}")
            return None

    @staticmethod
    def detect_primary_interface_linux() -> Optional[str]:
        try:
            output = subprocess.check_output(
                ["ip", "-o", "link", "show"], 
                encoding="utf-8",
                timeout=5
            )
            candidates = []
            for line in output.splitlines():
                m = re.match(r"\d+:\s+([^:]+):\s+<([^>]+)>", line)
                if not m:
                    continue
                name, flags = m.group(1), m.group(2).split(",")
                if name == "lo":
                    continue
                candidates.append((name, flags))
            
            for name, flags in candidates:
                if "UP" in flags:
                    return name
            return candidates[0][0] if candidates else None
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            try:
                output = subprocess.check_output(
                    ["ifconfig"], 
                    encoding="utf-8", 
                    errors="ignore",
                    timeout=5
                )
                blocks = re.split(r"\n(?=\S)", output)
                for block in blocks:
                    if block.startswith("lo"):
                        continue
                    name = block.split()[0]
                    return name
            except (subprocess.SubprocessError, subprocess.TimeoutExpired):
                return None
        return None

    @staticmethod
    def get_current_mac_linux(iface: str) -> Optional[str]:
        path = f"/sys/class/net/{iface}/address"
        try:
            with open(path, "r", encoding="utf-8") as f:
                mac = f.read().strip()
                if mac and re.match(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$", mac):
                    return mac
        except IOError:
            pass
        
        try:
            output = subprocess.check_output(
                ["ip", "link", "show", iface], 
                encoding="utf-8", 
                errors="ignore",
                timeout=5
            )
            m = re.search(r"link/\w+\s+([0-9a-fA-F:]{17})", output)
            if m:
                return m.group(1)
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass
        return None

    @staticmethod
    def generate_random_mac() -> str:
        first_octet = 0x02
        mac_bytes = [first_octet] + [random.randint(0x00, 0xFF) for _ in range(5)]
        return ":".join(f"{b:02x}" for b in mac_bytes)

    @staticmethod
    def change_mac_linux(iface: str, save_backup: bool = True) -> Tuple[Optional[str], Optional[str]]:
        original_mac = NetworkManager.get_current_mac_linux(iface)
        if not original_mac:
            return None, None

        if save_backup:
            backup = SecureConfig.load_backup()
            if iface not in backup:
                backup[iface] = original_mac
                SecureConfig.save_backup(backup)

        new_mac = NetworkManager.generate_random_mac()
        try:
            subprocess.run(
                ["ip", "link", "set", "dev", iface, "down"], 
                check=True,
                timeout=10
            )
            subprocess.run(
                ["ip", "link", "set", "dev", iface, "address", new_mac], 
                check=True,
                timeout=10
            )
            subprocess.run(
                ["ip", "link", "set", "dev", iface, "up"], 
                check=True,
                timeout=10
            )
            return original_mac, new_mac
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Failed to change MAC on {iface}: {e}")
            return None, None

    @staticmethod
    def revert_mac_linux(iface: str) -> bool:
        backup = SecureConfig.load_backup()
        original_mac = backup.get(iface)
        if not original_mac:
            return False
        
        try:
            subprocess.run(
                ["ip", "link", "set", "dev", iface, "down"], 
                check=True,
                timeout=10
            )
            subprocess.run(
                ["ip", "link", "set", "dev", iface, "address", original_mac], 
                check=True,
                timeout=10
            )
            subprocess.run(
                ["ip", "link", "set", "dev", iface, "up"], 
                check=True,
                timeout=10
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Failed to revert MAC on {iface}: {e}")
            return False

    @staticmethod
    def renew_ip(system: str, iface: Optional[str] = None) -> bool:
        try:
            if system == "Windows":
                subprocess.run(["ipconfig", "/release"], check=False, timeout=15)
                subprocess.run(["ipconfig", "/renew"], check=False, timeout=15)
            else:
                if iface:
                    subprocess.run(["dhclient", "-r", iface], check=False, timeout=15)
                    subprocess.run(["dhclient", iface], check=False, timeout=15)
                else:
                    subprocess.run(["dhclient", "-r"], check=False, timeout=15)
                    subprocess.run(["dhclient"], check=False, timeout=15)
            return True
        except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            print(f"Error renewing IP: {e}")
            return False


class M474GUI:
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} v{APP_VERSION}")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        self.system = platform.system()
        self.is_linux = self.system == "Linux"
        self.can_modify = False
        self.current_iface = None
        self.prevent_backup = tk.BooleanVar(value=False)
        
        if self.is_linux:
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                self.can_modify = True
            else:
                self.can_modify = False
        
        self._create_widgets()
        self._check_system_compatibility()
        self._refresh_network_info()

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        self._create_header(main_frame)
        self._create_system_info_section(main_frame)
        self._create_interface_section(main_frame)
        self._create_security_section(main_frame)
        self._create_network_info_section(main_frame)
        self._create_actions_section(main_frame)
        self._create_log_section(main_frame)
        self._create_status_bar()

    def _create_header(self, parent):
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=X, pady=(0, 20))
        
        title_label = ttk.Label(
            header_frame,
            text=APP_TITLE,
            font=("Helvetica", 24, "bold"),
            bootstyle="primary"
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header_frame,
            text=f"Version {APP_VERSION} - Network Identity Management Tool",
            font=("Helvetica", 10),
            bootstyle="secondary"
        )
        subtitle_label.pack()

    def _create_system_info_section(self, parent):
        info_frame = ttk.Labelframe(
            parent,
            text="System Information",
            padding=15,
            bootstyle="info"
        )
        info_frame.pack(fill=X, pady=(0, 10))
        
        os_frame = ttk.Frame(info_frame)
        os_frame.pack(fill=X, pady=2)
        ttk.Label(os_frame, text="Operating System:", width=20).pack(side=LEFT)
        self.os_label = ttk.Label(os_frame, text=self.system, bootstyle="inverse-info")
        self.os_label.pack(side=LEFT)
        
        priv_frame = ttk.Frame(info_frame)
        priv_frame.pack(fill=X, pady=2)
        ttk.Label(priv_frame, text="Privileges:", width=20).pack(side=LEFT)
        
        priv_text = "Administrator" if self.can_modify else "Standard User"
        priv_style = "inverse-success" if self.can_modify else "inverse-warning"
        self.priv_label = ttk.Label(priv_frame, text=priv_text, bootstyle=priv_style)
        self.priv_label.pack(side=LEFT)
        
        if not self.can_modify and self.is_linux:
            warn_label = ttk.Label(
                info_frame,
                text="⚠ Root privileges required for MAC address modification",
                bootstyle="warning",
                font=("Helvetica", 9, "italic")
            )
            warn_label.pack(fill=X, pady=(5, 0))

    def _create_interface_section(self, parent):
        iface_frame = ttk.Labelframe(
            parent,
            text="Network Interface",
            padding=15,
            bootstyle="primary"
        )
        iface_frame.pack(fill=X, pady=(0, 10))
        
        select_frame = ttk.Frame(iface_frame)
        select_frame.pack(fill=X)
        
        ttk.Label(select_frame, text="Interface:").pack(side=LEFT, padx=(0, 10))
        
        self.iface_var = tk.StringVar()
        self.iface_entry = ttk.Entry(
            select_frame,
            textvariable=self.iface_var,
            width=20,
            state="readonly" if not self.is_linux else "normal"
        )
        self.iface_entry.pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(
            select_frame,
            text="Auto-Detect",
            command=self._auto_detect_interface,
            bootstyle="info-outline",
            width=12
        ).pack(side=LEFT)

    def _create_security_section(self, parent):
        security_frame = ttk.Labelframe(
            parent,
            text="Security Options",
            padding=15,
            bootstyle="danger"
        )
        security_frame.pack(fill=X, pady=(0, 10))
        
        prevent_frame = ttk.Frame(security_frame)
        prevent_frame.pack(fill=X)
        
        self.prevent_check = ttk.Checkbutton(
            prevent_frame,
            text="Prevent Backup Storage (No Revert Available)",
            variable=self.prevent_backup,
            bootstyle="danger-round-toggle",
            command=self._toggle_prevent_backup
        )
        self.prevent_check.pack(side=LEFT)
        
        info_icon = ttk.Label(
            prevent_frame,
            text="ⓘ",
            foreground="#ff6b6b",
            font=("Helvetica", 12, "bold")
        )
        info_icon.pack(side=LEFT, padx=(10, 0))
        
        warning_label = ttk.Label(
            security_frame,
            text="When enabled, original MAC addresses will NOT be saved. Revert function will be unavailable.",
            bootstyle="danger",
            font=("Helvetica", 8, "italic"),
            wraplength=700
        )
        warning_label.pack(fill=X, pady=(5, 0))
        
        btn_frame = ttk.Frame(security_frame)
        btn_frame.pack(fill=X, pady=(10, 0))
        
        self.clear_backup_btn = ttk.Button(
            btn_frame,
            text="Clear All Backups",
            command=self._clear_backups,
            bootstyle="danger-outline",
            width=20
        )
        self.clear_backup_btn.pack(side=LEFT, padx=(0, 10))
        
        self.view_backup_btn = ttk.Button(
            btn_frame,
            text="View Backups",
            command=self._view_backups,
            bootstyle="info-outline",
            width=20
        )
        self.view_backup_btn.pack(side=LEFT)

    def _create_network_info_section(self, parent):
        net_frame = ttk.Labelframe(
            parent,
            text="Network Information",
            padding=15,
            bootstyle="success"
        )
        net_frame.pack(fill=X, pady=(0, 10))
        
        mac_frame = ttk.Frame(net_frame)
        mac_frame.pack(fill=X, pady=2)
        ttk.Label(mac_frame, text="MAC Address:", width=20).pack(side=LEFT)
        self.mac_label = ttk.Label(
            mac_frame,
            text="N/A",
            font=("Courier", 10),
            bootstyle="inverse-dark"
        )
        self.mac_label.pack(side=LEFT)
        
        int_ip_frame = ttk.Frame(net_frame)
        int_ip_frame.pack(fill=X, pady=2)
        ttk.Label(int_ip_frame, text="Internal IP:", width=20).pack(side=LEFT)
        self.int_ip_label = ttk.Label(
            int_ip_frame,
            text="N/A",
            font=("Courier", 10),
            bootstyle="inverse-dark"
        )
        self.int_ip_label.pack(side=LEFT)
        
        ext_ip_frame = ttk.Frame(net_frame)
        ext_ip_frame.pack(fill=X, pady=2)
        ttk.Label(ext_ip_frame, text="External IP:", width=20).pack(side=LEFT)
        self.ext_ip_label = ttk.Label(
            ext_ip_frame,
            text="N/A",
            font=("Courier", 10),
            bootstyle="inverse-dark"
        )
        self.ext_ip_label.pack(side=LEFT)
        
        ttk.Button(
            net_frame,
            text="Refresh Network Info",
            command=self._refresh_network_info,
            bootstyle="success-outline",
            width=20
        ).pack(pady=(10, 0))

    def _create_actions_section(self, parent):
        actions_frame = ttk.Labelframe(
            parent,
            text="Actions",
            padding=15,
            bootstyle="warning"
        )
        actions_frame.pack(fill=X, pady=(0, 10))
        
        btn_container = ttk.Frame(actions_frame)
        btn_container.pack()
        
        self.change_btn = ttk.Button(
            btn_container,
            text="Change MAC Address",
            command=self._change_mac,
            bootstyle="warning",
            width=25
        )
        self.change_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.revert_btn = ttk.Button(
            btn_container,
            text="Revert MAC Address",
            command=self._revert_mac,
            bootstyle="danger",
            width=25
        )
        self.revert_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.renew_btn = ttk.Button(
            btn_container,
            text="Renew IP Address",
            command=self._renew_ip,
            bootstyle="info",
            width=25
        )
        self.renew_btn.grid(row=1, column=0, padx=5, pady=5)
        
        self.spoof_btn = ttk.Button(
            btn_container,
            text="Change MAC & Renew IP",
            command=self._full_spoof,
            bootstyle="success",
            width=25
        )
        self.spoof_btn.grid(row=1, column=1, padx=5, pady=5)

    def _create_log_section(self, parent):
        log_frame = ttk.Labelframe(
            parent,
            text="Activity Log",
            padding=10,
            bootstyle="secondary"
        )
        log_frame.pack(fill=BOTH, expand=YES)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            wrap=tk.WORD,
            font=("Courier", 9),
            bg="#2b2b2b",
            fg="#ffffff",
            insertbackground="#ffffff"
        )
        self.log_text.pack(fill=BOTH, expand=YES)
        self.log_text.config(state=tk.DISABLED)
        
        ttk.Button(
            log_frame,
            text="Clear Log",
            command=self._clear_log,
            bootstyle="secondary-outline",
            width=15
        ).pack(pady=(5, 0))

    def _create_status_bar(self):
        self.status_bar = ttk.Label(
            self.root,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=W,
            padding=5,
            bootstyle="inverse-secondary"
        )
        self.status_bar.pack(side=BOTTOM, fill=X)

    def _log(self, message: str, level: str = "info"):
        self.log_text.config(state=tk.NORMAL)
        
        if level == "error":
            prefix = "[ERROR] "
        elif level == "success":
            prefix = "[SUCCESS] "
        elif level == "warning":
            prefix = "[WARNING] "
        else:
            prefix = "[INFO] "
        
        self.log_text.insert(tk.END, f"{prefix}{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self._log("Log cleared")

    def _update_status(self, message: str):
        self.status_bar.config(text=message)

    def _check_system_compatibility(self):
        if not self.is_linux:
            self._log(
                "MAC spoofing is only supported on Linux systems",
                "warning"
            )
            self._log(f"Current system: {self.system}", "info")
        
        if self.is_linux and not self.can_modify:
            self._log(
                "Root privileges required for MAC modification",
                "warning"
            )
            self._log(
                "Please run with: sudo python3 m474.py",
                "info"
            )

    def _toggle_prevent_backup(self):
        if self.prevent_backup.get():
            self._log("Backup prevention ENABLED - Revert will be unavailable", "warning")
            self.revert_btn.config(state=tk.DISABLED)
        else:
            self._log("Backup prevention DISABLED - Revert available", "info")
            self.revert_btn.config(state=tk.NORMAL)

    def _clear_backups(self):
        result = Messagebox.show_question(
            "Delete all stored backup MAC addresses?\n\n"
            "This action cannot be undone. You will not be able to revert to original MAC addresses.",
            "Confirm Backup Deletion"
        )
        
        if result != "Yes":
            return
        
        if SecureConfig.delete_backup():
            self._log("All backups deleted successfully", "success")
            Messagebox.show_info(
                "All backup MAC addresses have been deleted.",
                "Backups Deleted"
            )
        else:
            self._log("Failed to delete backups", "error")
            Messagebox.show_error(
                "Failed to delete backup file.",
                "Deletion Failed"
            )

    def _view_backups(self):
        backup = SecureConfig.load_backup()
        
        if not backup:
            Messagebox.show_info(
                "No backup MAC addresses stored.",
                "No Backups"
            )
            return
        
        backup_text = "Stored Backup MAC Addresses:\n\n"
        for iface, mac in backup.items():
            backup_text += f"{iface}: {mac}\n"
        
        Messagebox.show_info(backup_text, "Backup Information")

    def _auto_detect_interface(self):
        if not self.is_linux:
            Messagebox.show_error(
                "Interface detection is only supported on Linux",
                "Not Supported"
            )
            return
        
        self._update_status("Detecting network interface...")
        
        def detect():
            iface = NetworkManager.detect_primary_interface_linux()
            self.root.after(0, lambda: self._interface_detected(iface))
        
        threading.Thread(target=detect, daemon=True).start()

    def _interface_detected(self, iface: Optional[str]):
        if iface:
            self.current_iface = iface
            self.iface_var.set(iface)
            self._log(f"Detected interface: {iface}", "success")
            self._update_status(f"Interface: {iface}")
            self._refresh_network_info()
        else:
            self._log("Could not detect network interface", "error")
            self._update_status("Interface detection failed")
            Messagebox.show_error(
                "Could not detect network interface",
                "Detection Failed"
            )

    def _refresh_network_info(self):
        self._update_status("Refreshing network information...")
        
        def refresh():
            iface = self.iface_var.get() or self.current_iface
            
            mac = None
            if self.is_linux and iface:
                mac = NetworkManager.get_current_mac_linux(iface)
            
            internal_ip = NetworkManager.get_internal_ip()
            external_ip = NetworkManager.get_external_ip()
            
            self.root.after(
                0,
                lambda: self._update_network_display(mac, internal_ip, external_ip)
            )
        
        threading.Thread(target=refresh, daemon=True).start()

    def _update_network_display(
        self,
        mac: Optional[str],
        internal_ip: Optional[str],
        external_ip: Optional[str]
    ):
        self.mac_label.config(text=mac or "N/A")
        self.int_ip_label.config(text=internal_ip or "N/A")
        self.ext_ip_label.config(text=external_ip or "N/A")
        
        self._log("Network information refreshed", "success")
        self._update_status("Ready")

    def _change_mac(self):
        if not self._validate_operation():
            return
        
        iface = self.iface_var.get() or self.current_iface
        if not iface:
            Messagebox.show_error(
                "Please select or detect a network interface first",
                "No Interface Selected"
            )
            return
        
        warning_msg = f"Change MAC address for interface '{iface}'?\n\n"
        warning_msg += "This will temporarily disconnect the network."
        
        if self.prevent_backup.get():
            warning_msg += "\n\n⚠ WARNING: Backup is DISABLED. Original MAC will NOT be saved!"
        
        result = Messagebox.show_question(warning_msg, "Confirm MAC Change")
        
        if result != "Yes":
            return
        
        self._update_status("Changing MAC address...")
        self._disable_buttons()
        
        def change():
            save_backup = not self.prevent_backup.get()
            orig_mac, new_mac = NetworkManager.change_mac_linux(iface, save_backup)
            self.root.after(
                0,
                lambda: self._mac_changed(orig_mac, new_mac, iface, save_backup)
            )
        
        threading.Thread(target=change, daemon=True).start()

    def _mac_changed(
        self,
        orig_mac: Optional[str],
        new_mac: Optional[str],
        iface: str,
        saved_backup: bool
    ):
        self._enable_buttons()
        
        if new_mac:
            self._log(f"MAC changed on {iface}", "success")
            self._log(f"Original: {orig_mac}", "info")
            self._log(f"New: {new_mac}", "info")
            
            if not saved_backup:
                self._log("Original MAC was NOT backed up (prevention enabled)", "warning")
            
            self._update_status("MAC address changed successfully")
            self._refresh_network_info()
            
            msg = f"MAC address changed successfully!\n\n"
            msg += f"Interface: {iface}\n"
            msg += f"Old MAC: {orig_mac}\n"
            msg += f"New MAC: {new_mac}"
            
            if not saved_backup:
                msg += "\n\n⚠ Original MAC was NOT saved (backup prevention enabled)"
            
            Messagebox.show_info(msg, "Success")
        else:
            self._log("Failed to change MAC address", "error")
            self._update_status("MAC change failed")
            Messagebox.show_error(
                "Failed to change MAC address. Check the log for details.",
                "Operation Failed"
            )

    def _revert_mac(self):
        if not self._validate_operation():
            return
        
        iface = self.iface_var.get() or self.current_iface
        if not iface:
            Messagebox.show_error(
                "Please select or detect a network interface first",
                "No Interface Selected"
            )
            return
        
        backup = SecureConfig.load_backup()
        if iface not in backup:
            Messagebox.show_warning(
                f"No backup MAC found for interface '{iface}'",
                "No Backup Available"
            )
            return
        
        result = Messagebox.show_question(
            f"Revert MAC address for interface '{iface}' to original?\n\n"
            f"Original MAC: {backup[iface]}",
            "Confirm MAC Revert"
        )
        
        if result != "Yes":
            return
        
        self._update_status("Reverting MAC address...")
        self._disable_buttons()
        
        def revert():
            success = NetworkManager.revert_mac_linux(iface)
            self.root.after(0, lambda: self._mac_reverted(success, iface))
        
        threading.Thread(target=revert, daemon=True).start()

    def _mac_reverted(self, success: bool, iface: str):
        self._enable_buttons()
        
        if success:
            self._log(f"MAC reverted on {iface}", "success")
            self._update_status("MAC address reverted successfully")
            self._refresh_network_info()
            
            Messagebox.show_info(
                f"MAC address reverted to original successfully!\n\n"
                f"Interface: {iface}",
                "Success"
            )
        else:
            self._log("Failed to revert MAC address", "error")
            self._update_status("MAC revert failed")
            Messagebox.show_error(
                "Failed to revert MAC address. Check the log for details.",
                "Operation Failed"
            )

    def _renew_ip(self):
        result = Messagebox.show_question(
            "Renew IP address?\n\n"
            "This may temporarily disconnect the network.",
            "Confirm IP Renewal"
        )
        
        if result != "Yes":
            return
        
        self._update_status("Renewing IP address...")
        self._disable_buttons()
        
        def renew():
            iface = self.iface_var.get() or self.current_iface if self.is_linux else None
            success = NetworkManager.renew_ip(self.system, iface)
            self.root.after(0, lambda: self._ip_renewed(success))
        
        threading.Thread(target=renew, daemon=True).start()

    def _ip_renewed(self, success: bool):
        self._enable_buttons()
        
        if success:
            self._log("IP address renewal initiated", "success")
            self._update_status("IP address renewed")
            self.root.after(2000, self._refresh_network_info)
            
            Messagebox.show_info(
                "IP address renewal initiated successfully!",
                "Success"
            )
        else:
            self._log("Failed to renew IP address", "warning")
            self._update_status("IP renewal may have failed")

    def _full_spoof(self):
        if not self._validate_operation():
            return
        
        iface = self.iface_var.get() or self.current_iface
        if not iface:
            Messagebox.show_error(
                "Please select or detect a network interface first",
                "No Interface Selected"
            )
            return
        
        warning_msg = f"Perform full network identity change?\n\n"
        warning_msg += f"This will:\n"
        warning_msg += f"1. Change MAC address on {iface}\n"
        warning_msg += f"2. Renew IP address\n\n"
        warning_msg += f"The network will be temporarily disconnected."
        
        if self.prevent_backup.get():
            warning_msg += "\n\n⚠ WARNING: Backup is DISABLED. Original MAC will NOT be saved!"
        
        result = Messagebox.show_question(warning_msg, "Confirm Full Spoof")
        
        if result != "Yes":
            return
        
        self._update_status("Performing full spoof...")
        self._disable_buttons()
        
        def full_spoof():
            save_backup = not self.prevent_backup.get()
            orig_mac, new_mac = NetworkManager.change_mac_linux(iface, save_backup)
            if not new_mac:
                self.root.after(0, lambda: self._full_spoof_failed())
                return
            
            NetworkManager.renew_ip(self.system, iface)
            
            self.root.after(
                0,
                lambda: self._full_spoof_complete(orig_mac, new_mac, iface, save_backup)
            )
        
        threading.Thread(target=full_spoof, daemon=True).start()

    def _full_spoof_complete(
        self,
        orig_mac: str,
        new_mac: str,
        iface: str,
        saved_backup: bool
    ):
        self._enable_buttons()
        
        self._log("Full spoof completed", "success")
        self._log(f"Interface: {iface}", "info")
        self._log(f"Old MAC: {orig_mac}", "info")
        self._log(f"New MAC: {new_mac}", "info")
        self._log("IP renewal initiated", "info")
        
        if not saved_backup:
            self._log("Original MAC was NOT backed up (prevention enabled)", "warning")
        
        self._update_status("Full spoof completed")
        
        self.root.after(2000, self._refresh_network_info)
        
        msg = f"Network identity changed successfully!\n\n"
        msg += f"Interface: {iface}\n"
        msg += f"Old MAC: {orig_mac}\n"
        msg += f"New MAC: {new_mac}\n\n"
        msg += f"IP renewal initiated."
        
        if not saved_backup:
            msg += "\n\n⚠ Original MAC was NOT saved (backup prevention enabled)"
        
        Messagebox.show_info(msg, "Success")

    def _full_spoof_failed(self):
        self._enable_buttons()
        self._log("Full spoof failed", "error")
        self._update_status("Operation failed")
        
        Messagebox.show_error(
            "Failed to change MAC address. IP renewal was not attempted.",
            "Operation Failed"
        )

    def _validate_operation(self) -> bool:
        if not self.is_linux:
            Messagebox.show_error(
                "MAC address operations are only supported on Linux",
                "Not Supported"
            )
            return False
        
        if not self.can_modify:
            Messagebox.show_error(
                "Root privileges are required for this operation.\n\n"
                "Please run the application with:\n"
                "sudo python3 m474.py",
                "Insufficient Privileges"
            )
            return False
        
        return True

    def _disable_buttons(self):
        self.change_btn.config(state=tk.DISABLED)
        self.revert_btn.config(state=tk.DISABLED)
        self.renew_btn.config(state=tk.DISABLED)
        self.spoof_btn.config(state=tk.DISABLED)

    def _enable_buttons(self):
        self.change_btn.config(state=tk.NORMAL)
        if not self.prevent_backup.get():
            self.revert_btn.config(state=tk.NORMAL)
        self.renew_btn.config(state=tk.NORMAL)
        self.spoof_btn.config(state=tk.NORMAL)


def main():
    root = ttk.Window(themename="darkly")
    
    root.minsize(700, 650)
    
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    app = M474GUI(root)
    
    def on_closing():
        if Messagebox.show_question(
            "Are you sure you want to exit?",
            "Confirm Exit"
        ) == "Yes":
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()


if __name__ == "__main__":
    main()
