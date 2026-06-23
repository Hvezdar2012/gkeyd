# Logitech G815 Linux G-Keys Daemon

Small Linux daemon for Logitech G815 keyboards.

It enables G1-G5 keys on Linux by using Logitech HID++ G-Key divert mode through Solaar and then remapping raw G-Key events to virtual function keys.

Default mapping:

| G-Key | Output |
| ----- | ------ |
| G1    | F14    |
| G2    | F15    |
| G3    | F16    |
| G4    | F17    |
| G5    | F18    |

F13 is intentionally skipped because some desktop environments may already use it.

---

## Supported system

This project was primarily created and tested on:

* CachyOS
* Arch Linux based systems
* KDE Plasma Wayland
* Logitech G815

It may work on other Linux distributions and Logitech G-series keyboards, but this is not guaranteed.

---

## Requirements

Required packages:

```bash
sudo pacman -S solaar python-evdev
```

The script can also try to install missing dependencies automatically on Arch/CachyOS using `pacman`.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Hvezdar2012/gkeyd.git
cd gkeyd
```

Install the script:

```bash
sudo cp g815-gkeyd.py /usr/local/bin/g815-gkeyd.py
sudo chmod +x /usr/local/bin/g815-gkeyd.py
```

Test manually:

```bash
sudo /usr/local/bin/g815-gkeyd.py
```

In another terminal, verify the virtual keyboard:

```bash
sudo pacman -S evtest
sudo evtest
```

Select:

```text
G815 G-Keys Virtual Keyboard
```

Press G1-G5 and you should see F14-F18 events.

---

## Install as systemd service

Copy the service file:

```bash
sudo cp g815-gkeyd.service /etc/systemd/system/g815-gkeyd.service
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now g815-gkeyd.service
```

Check status:

```bash
systemctl status g815-gkeyd.service
```

View logs:

```bash
journalctl -u g815-gkeyd.service -f
```

Restart:

```bash
sudo systemctl restart g815-gkeyd.service
```

Disable:

```bash
sudo systemctl disable --now g815-gkeyd.service
```

---

## Changing G1-G5 key mapping

Open the script:

```bash
sudo nano /usr/local/bin/g815-gkeyd.py
```

Find:

```python
MAP_VALUES = {
    0x01: "KEY_F14",
    0x02: "KEY_F15",
    0x04: "KEY_F16",
    0x08: "KEY_F17",
    0x10: "KEY_F18",
}
```

Change the output keys as needed.

Examples:

```python
0x01: "KEY_A"
```

or:

```python
0x01: "KEY_F19"
```

After changes, restart the service:

```bash
sudo systemctl restart g815-gkeyd.service
```

---

## RGB lighting

This project does not control RGB lighting.

For RGB, OpenRGB is recommended:

```bash
sudo pacman -S openrgb
sudo openrgb
```

---

## How it works

The Logitech G815 exposes a HID++ feature called `GKEY`.

Solaar can enable:

```text
Divert G and M Keys
```

When enabled, G1-G5 stop behaving like normal F1-F5 keys and instead emit raw HID++ notifications.

Observed G-Key values:

| Key     | Raw value |
| ------- | --------- |
| G1      | `0x01`    |
| G2      | `0x02`    |
| G3      | `0x04`    |
| G4      | `0x08`    |
| G5      | `0x10`    |
| Release | `0x00`    |

Observed packet pattern:

```text
11 ff 0a 00 XX 00 00 00 ...
```

The Python daemon reads these packets from `/dev/hidraw*` and creates a virtual keyboard using `evdev/uinput`.

---

## License

This project is released into the public domain.

You may use, copy, modify, publish, distribute, sell, or do anything else with this code without asking for permission.

No warranty is provided. Use at your own risk.

---

## Credits

This project was created experimentally with the help of ChatGPT.

The goal was to make Logitech G815 G-keys usable on Linux without Logitech G Hub.
