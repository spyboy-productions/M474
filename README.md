<p align="center">
    <a href="https://spyboy.in/twitter">
      <img src="https://img.shields.io/badge/-TWITTER-black?logo=twitter&style=for-the-badge">
    </a>
    &nbsp;
    <a href="https://spyboy.in/">
      <img src="https://img.shields.io/badge/-spyboy.in-black?logo=google&style=for-the-badge">
    </a>
    &nbsp;
    <a href="https://spyboy.blog/">
      <img src="https://img.shields.io/badge/-spyboy.blog-black?logo=wordpress&style=for-the-badge">
    </a>
    &nbsp;
    <a href="https://spyboy.in/Discord">
      <img src="https://img.shields.io/badge/-Discord-black?logo=discord&style=for-the-badge">
    </a>
</p>

<img width="100%" align="centre" src="https://github.com/spyboy-productions/M474/blob/main/M474.png" />

<br>

# 🛰️ M474 — Network Privacy Enhancer

**M474** is an open-source **network privacy & MAC randomization tool** designed to improve your online anonymity.  

It provides:

- MAC spoofing (Linux)
- IP renewal (Linux + Windows)
- Network interface auto-detection
- Safe revert with backup
- No broken vendor parsing, no temp files
- Fully cross-platform safe execution

<h4 align="center">This tool is a Proof of Concept and for Educational Purposes Only.</h4>

> [!IMPORTANT]
> Misuse of MAC spoofing can disrupt your network connectivity.  
> Run responsibly and only on systems you control.

---

## ✨ Features

### 🟢 **Linux (Full Support)**
- **MAC Address Spoofing**  
  Random, locally-administered valid MACs  
- **MAC Revert Function**  
  Automatically restores your original MAC from a secure backup  
- **Automatic Interface Detection**  
  Works on wlan0, eth0, enpXsY, wlpXsY, etc.  
- **IP Renewal** (internal + external)  
- **Safe Execution Without Root**  
  Shows info but won’t break anything

### 🔵 **Windows (Safe, Partial Support)**
- MAC spoofing blocked (to avoid registry corruption)  
- **Internal & external IP detection**  
- **IP renew support (`ipconfig /renew`)**  
- Cleaner output and automatic error handling

---

## 🛠️ Installation

```bash
git clone https://github.com/spyboy-productions/M474.git
````

```bash
cd M474
```

### 🔧 Install Python requirements

(Not many—only standard modules unless you added more)

```bash
pip3 install -r requirements.txt
```

---

## ▶️ Usage

### 🟢 Run normally (Linux + Windows)

```bash
sudo python3 M474.py
```

### 🔄 Revert MAC back to original (Linux only)

```bash
sudo python3 M474.py --revert
```

### 📡 Specify your own interface

```bash
sudo python3 M474.py --iface wlan0
```

### 🚫 Skip IP renewal

```bash
sudo python3 M474.py --no-ip-renew
```

---

## 🧠 Notes

* Script automatically detects your primary network interface
* Backs up your original MAC at:
  `~/.mac_spoofer_backup.json`
* Linux-only MAC changes are intentional for safety
* Windows MAC spoofing via registry can be added—upon request

---

## 💬 Need help?

If you're facing issues:

### 👉 [Chat here on Discord](https://discord.gg/ZChEmMwE8d)

[![Discord Server](https://discord.com/api/guilds/726495265330298973/embed.png)](https://discord.gg/ZChEmMwE8d)

---

## 🤝 Contributions

Contributions and suggestions are welcome!
Feel free to open:

* an **Issue**
* a **Pull Request**
* a **Feature Request**

---

## Future Plans (ToDo)

* Add vendor-based MAC address randomization
* Add periodic auto-randomization (every X minutes)
* Add advanced privacy modes
* Add optional Windows spoofing support
* Add GUI version

---

## ⭔ Snapshots

<img width="100%" align="centre" src="https://github.com/spyboy-productions/M474/blob/main/Snap-m474.png" />

---

<h4 align="center">⭐ If you find this project useful, please consider giving it a star! ⭐</h4>
