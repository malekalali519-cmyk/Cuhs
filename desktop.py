import os
import subprocess
import time

VNC_DISPLAY = ":1"
VNC_PORT = 5901
NOVNC_PORT = 6080
RESOLUTION = "1280x720"


def run(cmd, check=True):
    print(f"> {cmd}")
    return subprocess.run(cmd, shell=True, check=check)


def setup_desktop():
    print("Installiere XFCE-Desktop, VNC und noVNC...")
    run("sudo apt-get update -y")
    run("DEBIAN_FRONTEND=noninteractive sudo apt-get install -y xfce4 xfce4-goodies tightvncserver novnc websockify dbus-x11")

    vnc_dir = os.path.expanduser("~/.vnc")
    os.makedirs(vnc_dir, exist_ok=True)
    xstartup_path = os.path.join(vnc_dir, "xstartup")

    xstartup_code = """#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
"""
    with open(xstartup_path, "w", encoding="utf-8") as f:
        f.write(xstartup_code)
    os.chmod(xstartup_path, 0o755)

    passwd_file = os.path.join(vnc_dir, "passwd")
    if not os.path.exists(passwd_file):
        print("\nBitte lege jetzt ein VNC-Passwort (6–8 Zeichen) fest:")
        run(f"vncpasswd {passwd_file}")


def start_services():
    # Alten Server auf :1 falls vorhanden sauber beenden
    run(f"vncserver -kill {VNC_DISPLAY}", check=False)
    time.sleep(1)

    print(f"Starte Desktop auf {VNC_DISPLAY} ({RESOLUTION})...")
    run(f"vncserver {VNC_DISPLAY} -geometry {RESOLUTION} -depth 24")

    print(f"Starte noVNC auf Port {NOVNC_PORT}...")
    subprocess.Popen(
        f"websockify --web=/usr/share/novnc/ {NOVNC_PORT} localhost:{VNC_PORT}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)
    print("\nFertig! Öffne jetzt unten den Tab 'Ports' und klicke auf den Link für Port 6080 (vnc.html).")


if __name__ == "__main__":
    if not os.path.exists("/usr/bin/startxfce4"):
        setup_desktop()
    start_services()
