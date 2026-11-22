import json
import os
import sys
from datetime import datetime, timezone
import requests

GITHUB_TOKEN = "DEIN_GITHUB_PAT"
OWNER = "malekalali519-cmyk"
REPO = "Cuhs"
BRANCH = "main"

MACHINE_TYPE = "standardLinux32gb"  # 4 Cores, 16 GB RAM
CORES = 4
MONTHLY_CORE_HOURS_LIMIT = 120      # 120 Core-Std. / 4 Cores = max. 30 Std./Monat
MAX_HOURS_PER_MONTH = MONTHLY_CORE_HOURS_LIMIT / CORES
USAGE_FILE = "usage.json"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


def load_usage():
    if not os.path.exists(USAGE_FILE):
        return {"used_core_hours": 0.0, "active_start": None}
    with open(USAGE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "used_core_hours": float(data.get("used_core_hours", 0.0)),
        "active_start": data.get("active_start")
    }


def save_usage(usage):
    usage["used_core_hours"] = round(float(usage["used_core_hours"]), 2)
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(usage, f, indent=2)


def show_status():
    usage = load_usage()
    used_core = usage["used_core_hours"]
    rem_core = max(0.0, MONTHLY_CORE_HOURS_LIMIT - used_core)
    rem_hours = rem_core / CORES
    used_hours = used_core / CORES

    print(f"Verbraucht: {used_hours:.2f} / {MAX_HOURS_PER_MONTH:.0f} Std. ({used_core:.2f} / {MONTHLY_CORE_HOURS_LIMIT} Core-Std.)")
    print(f"Verbleibend: {rem_hours:.2f} Std. bei 4 Cores / 16 GB RAM")
    if usage["active_start"]:
        print(f"Aktiver Timer gestartet um: {usage['active_start']}")


def start_cloud_pc():
    usage = load_usage()
    rem_core = MONTHLY_CORE_HOURS_LIMIT - usage["used_core_hours"]
    if rem_core < CORES:
        print("Kontingent fast oder komplett aufgebraucht (weniger als 1 Stunde bei 4 Cores übrig).")
        return

    url = f"https://api.github.com/repos/{OWNER}/{REPO}/codespaces"
    payload = {
        "ref": BRANCH,
        "machine": MACHINE_TYPE,
        "display_name": "linux-cloud-pc-16gb"
    }
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code in (200, 201):
        data = res.json()
        usage["active_start"] = datetime.now(timezone.utc).isoformat()
        save_usage(usage)
        print("Cloud-PC gestartet!")
        print("Name:", data.get("name"))
        print("URL:", data.get("web_url"))
    else:
        print("Fehler beim Starten:", res.status_code, res.text)


def stop_cloud_pc():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/codespaces"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print("Fehler beim Abrufen der Codespaces:", res.status_code, res.text)
        return

    codespaces = res.json().get("codespaces", [])
    stopped_any = False

    for cs in codespaces:
        if cs.get("state") == "Available":
            name = cs.get("name")
            stop_url = f"https://api.github.com/user/codespaces/{name}/stop"
            stop_res = requests.post(stop_url, headers=HEADERS)
            if stop_res.status_code in (200, 202, 204):
                print("Gestoppt:", name)
                stopped_any = True
            else:
                print("Konnte nicht stoppen:", name, stop_res.status_code, stop_res.text)

    usage = load_usage()
    if usage["active_start"]:
        start_dt = datetime.fromisoformat(usage["active_start"])
        elapsed_hours = max(0.0, (datetime.now(timezone.utc) - start_dt).total_seconds() / 3600.0)
        added_core_hours = elapsed_hours * CORES
        usage["used_core_hours"] += added_core_hours
        usage["active_start"] = None
        save_usage(usage)
        print(f"Laufzeit verbucht: {elapsed_hours:.2f} Std. (+{added_core_hours:.2f} Core-Std.)")
    elif not stopped_any:
        print("Kein laufender Codespace gefunden.")

    show_status()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "start":
        start_cloud_pc()
    elif cmd == "stop":
        stop_cloud_pc()
    elif cmd == "status":
        show_status()
    else:
        print("Befehle: python cloud_pc.py [status | start | stop]")
