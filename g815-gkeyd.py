#!/usr/bin/env python3

"""
Logitech G815 Linux G-Key Daemon

Features:
- Automatically installs required dependencies on Arch/CachyOS
- Configures the Logitech G815 into managed/divert mode using Solaar
- Reads raw HID++ G-Key notifications from /dev/hidraw*
- Creates a virtual keyboard device through evdev/uinput
- Maps G1-G5 to F14-F18
- Designed to run as a systemd service

Dependencies:
- solaar
- python-evdev
"""

import os
import re
import sys
import time
import shutil
import subprocess

VERSION = "1.0.0"
DEVICE_NAME = "G815"

REQUIRED_PACKAGES = [
    "solaar",
    "python-evdev",
]

# G1-G5 -> F14-F18
# F13 is intentionally skipped because it may be used by some desktop environments.
MAP_VALUES = {
    0x01: "KEY_F14",
    0x02: "KEY_F15",
    0x04: "KEY_F16",
    0x08: "KEY_F17",
    0x10: "KEY_F18",
}


def run_command(command, check=True, silent=False):
    if not silent:
        print(f"> {' '.join(command)}")

    return subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=check,
    )


def require_root():
    if os.geteuid() != 0:
        print("Error: this program must be run as root.")
        sys.exit(1)


def install_missing_dependencies():
    missing_packages = []

    if shutil.which("solaar") is None:
        missing_packages.append("solaar")

    try:
        import evdev  # noqa: F401
    except ImportError:
        missing_packages.append("python-evdev")

    if not missing_packages:
        print("All required dependencies are installed.")
        return

    print(f"Missing packages: {', '.join(missing_packages)}")

    if shutil.which("pacman") is None:
        print("Error: pacman was not found. Please install the missing packages manually.")
        sys.exit(1)

    print("Installing missing dependencies using pacman...")

    command = ["pacman", "-S", "--needed", "--noconfirm"] + missing_packages
    subprocess.run(command, check=True)


def load_evdev():
    global UInput, e
    from evdev import UInput, ecodes as e


def find_hidraw_device():
    result = run_command(["solaar", "show"], silent=True)
    output = result.stdout

    if "G815 Mechanical Keyboard" not in output:
        print("Error: Logitech G815 was not found by Solaar.")
        sys.exit(1)

    device_block = output.split("G815 Mechanical Keyboard", 1)[1]
    match = re.search(r"Device path\s*:\s*(/dev/hidraw\d+)", device_block)

    if not match:
        print("Error: could not find the G815 /dev/hidraw* device path.")
        sys.exit(1)

    return match.group(1)


def configure_keyboard():
    print("Configuring Logitech G815 managed/divert mode...")

    # Disable onboard profile mode.
    # In this mode, G-keys can emit HID++ notifications instead of plain F1-F5.
    subprocess.run(
        ["solaar", "config", DEVICE_NAME, "onboard_profiles", "Disabled"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    time.sleep(0.2)

    # Enable G-key divert mode.
    subprocess.run(
        ["solaar", "config", DEVICE_NAME, "divert-gkeyd", "true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    time.sleep(0.2)


def create_virtual_keyboard(key_map):
    return UInput(
        {e.EV_KEY: list(key_map.values())},
        name="G815 G-Keys Virtual Keyboard",
    )


def is_gkey_notification(data):
    if len(data) < 8:
        return False

    # Valid GKEY HID++ notification pattern:
    # 11 ff 0a 00 XX 00 00 00 ...
    return (
        data[0] == 0x11 and
        data[1] == 0xFF and
        data[2] == 0x0A and
        data[3] == 0x00 and
        data[5] == 0x00 and
        data[6] == 0x00 and
        data[7] == 0x00
    )


def run_daemon(hidraw_path, key_map):
    virtual_keyboard = create_virtual_keyboard(key_map)

    print(f"Detected G815 HID device: {hidraw_path}")
    print("G815 daemon started successfully.")
    print("Mapped keys:")
    print("  G1 -> F14")
    print("  G2 -> F15")
    print("  G3 -> F16")
    print("  G4 -> F17")
    print("  G5 -> F18")

    last_key = None

    with open(hidraw_path, "rb", buffering=0) as device:
        while True:
            data = device.read(20)

            if not is_gkey_notification(data):
                continue

            value = data[4]

            if value in key_map:
                key = key_map[value]

                if last_key != key:
                    virtual_keyboard.write(e.EV_KEY, key, 1)
                    virtual_keyboard.syn()
                    last_key = key

            elif value == 0x00 and last_key is not None:
                virtual_keyboard.write(e.EV_KEY, last_key, 0)
                virtual_keyboard.syn()
                last_key = None


def main():
    print(f"Logitech G815 Linux G-Key Daemon v{VERSION}")

    require_root()
    install_missing_dependencies()
    load_evdev()

    configure_keyboard()

    hidraw_path = find_hidraw_device()
    key_map = {
        raw_value: getattr(e, key_name)
        for raw_value, key_name in MAP_VALUES.items()
    }

    run_daemon(hidraw_path, key_map)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDaemon stopped.")
