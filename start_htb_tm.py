"""
HTB Launcher (Terminator Edition)

Automates Hack The Box machine setup using Terminator:
- Verifies tun0 VPN connection
- Creates working directories under /htb/<box>
- Generates reverse shells
- Adds /etc/hosts entry
- Waits for box to respond to ping
- Opens Terminator tabs with recon/fuzzing tools

Streamlines initial setup for HTB-style workflow using Terminator.
"""

import os
import subprocess
import sys
import time

FULLSCREEN_I3_PANE = "i3-msg '[con_id=\"__focused__\"] fullscreen enable'"


def check_tun0_interface():
    try:
        result = subprocess.run(['ip', 'addr', 'show', 'tun0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            print("[-] tun0 not found or not connected")
            sys.exit(1)

        for line in result.stdout.splitlines():
            if "inet " in line:
                ip_address = line.strip().split()[1].split('/')[0]
                return ip_address

        print("[-] tun0 found but no IP address assigned")
        sys.exit(1)

    except Exception as e:
        print(f"[-] Error checking tun0: {e}")
        sys.exit(1)


def create_directory(name):
    path = f"/htb/{name}"

    try:
        os.makedirs(path, exist_ok=True)
        print(f"[+] Successfully created the directory: {path}")

    except PermissionError:
        print(f"[-] Permission denied: Cannot create directory at {path}")
        sys.exit(1)

    except OSError as e:
        print(f"[-] Failed to create the directory: {e}")
        sys.exit(1)


def run_zsh_command(command):
    try:
        result = subprocess.run(['zsh', '-c', f'source ~/.zshrc && {command}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            print(f"[+] Command '{command}' executed successfully")
        else:
            print(f"[-] Command '{command}' failed to execute")
            print(result.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"[-] Error executing command '{command}': {e}")
        sys.exit(1)


def ping_host(ip):
    consecutive_failures = 0
    print("[i] Waiting for ping...")
    while True:
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if result.returncode == 0:
                print(f"[+] Got ping!")
                return
            else:
                consecutive_failures += 1

        except Exception as e:
            print(f"[-] Error while trying to ping {ip}: {e}")
            sys.exit(1)

        if consecutive_failures >= 15:
            action = input(f"[-] Could not ping host yet! (c)ontinue/(s)kip/(e)xit? ").strip().lower()
            if action == 'c':
                consecutive_failures = 0
                print("[+] Continuing to ping...")
            elif action == 's':
                print("[+] Skipping ping checks and continuing...")
                break
            elif action == 'e':
                print("[+] Exiting the script.")
                sys.exit(0)
            else:
                print("[-] Invalid input, please enter 'c', 's', or 'e'.")
        else:
            time.sleep(1)


def start_terminator_session(box_ip, box_name):
    command_list = [
        ("rustscan-tcp", f"rustscan -a {box_ip} -- -sC -sV -o rustscan"),
        ("ports-tcp", f"nmap_default {box_ip} -p-"),
        ("ports-udp", f"nmap_udp {box_ip}"),
        ("vhost", f"sleep 2 && vhost {box_name}.htb"),
        ("fuzz1", f"fuzz_dir http://{box_name}.htb"),
        ("fuzz2", f"feroxbuster -u http://{box_name}.htb"),
        ("enum4linux", f"enum4linux -v {box_ip}"),
        ("ligolo-proxy", "ip link del ligolo 2>/dev/null; ip tuntap add dev ligolo mode tun user $(whoami); ip link set ligolo up && ligolo-proxy -selfcert"),
        ("responder", "responder -I tun0"),
    ]

    for title, cmd in command_list:
        subprocess.Popen([
            "terminator",
            "--new-tab",
            "--title", title,
            "--command", f"zsh -i -c '{cmd}; exec zsh'"
        ])
        time.sleep(1)
        # Fullscreen the window using wmctrl
        subprocess.run(["wmctrl", "-r", title, "-b", "add,maximized_vert,maximized_horz"])


# === Main Execution ===

if __name__ == "__main__":
    tun0_ip = check_tun0_interface()
    if tun0_ip:
        print(f"[+] tun0 is connected with IP: {tun0_ip}")

    box_name = input("[?] Enter the name: ")

    create_directory(box_name)
    create_directory(box_name + "/www/")
    os.chdir(f"/htb/{box_name}/www/")

    run_zsh_command(f"gen_lin_rev {tun0_ip} 8443")
    run_zsh_command(f"gen_php_rev {tun0_ip} 8443")

    os.chdir(f"/htb/{box_name}/")

    print("[i] Wait until you have a box IP, after entering we start pinging it to see if it's up")
    box_ip = input("[?] Enter the IP: ")
    ping_host(box_ip)
    run_zsh_command(f"addhost {box_ip} {box_name}.htb")

    start_terminator_session(box_ip, box_name)
