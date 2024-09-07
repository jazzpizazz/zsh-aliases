# NOTE: Expects /htb/ folder. ( sudo mkdir /htb && sudo chown kali:kali /htb )
#
# This is the script can be used for playing HTB boxes. It does the following:
# - Check if we have a tun0 ip, if not it exits
# - Ask for the name of the box
#   - it is used to create the folder structure and initial hostname (boxname.htb)
#   - based on the tun0 ip a linux reverse shell (sh and php) are generated in the www folder
#   - TODO: create symlink to /opt/tools/ in the www folder as well and start webserver
# - Ask for the box IP
# - Pings the box to check if its up, after 15 pings it will ask you if you want to:
#   - continue -> it will ping 15 more times and come back to the same prompt
#   - skip -> skip the ping step and just assume the box is up (for boxes not responding to pings)
#   - exit -> exit the script
# - As soon as the box is pinge-able or the ping check is skipped it sets up a tmux session with:
#   - a "ports" window with panes running a udp and tcp scan
#   - a "vhosts" window running a vhost enum
#   - a "fuzz" window running to web directory fuzzers
# It then fullscreens the current i3 pane and attaches to this tmux session.
#
# Other TODO's:
# - Ask for host OS and implement my windows workflow
# - Improve ping check, the fact that a box pings does not mean all services are up yet.

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
        result = subprocess.run(['zsh',  '-c', f'source ~/.zshrc && {command}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            print(f"[+] Command '{command}' executed successfully")
        else:
            print(f"[-] Command '{command}' failed to execute")
            print(result.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"[-] Error executing command '{command}': {e}")
        sys.exit(1)


def start_tmux_session_with_windows(session_name, command1, command2, command3, command4, command5):
    try:
        subprocess.run(['tmux', 'new-session', '-d', '-s', session_name, '-n', 'ports'], check=True)

        subprocess.run(['tmux', 'split-window', '-v', '-t', f'{session_name}:ports'], check=True)
        run_zsh_command_in_tmux_pane(session_name, 'ports.0', command1)
        run_zsh_command_in_tmux_pane(session_name, 'ports.1', command2)

        subprocess.run(['tmux', 'new-window', '-t', session_name, '-n', 'vhost'], check=True)
        run_zsh_command_in_tmux_pane(session_name, 'vhost', command3)

        subprocess.run(['tmux', 'new-window', '-t', session_name, '-n', 'fuzz'], check=True)
        subprocess.run(['tmux', 'split-window', '-v', '-t', f'{session_name}:fuzz'], check=True)
        run_zsh_command_in_tmux_pane(session_name, 'fuzz.0', command4)
        run_zsh_command_in_tmux_pane(session_name, 'fuzz.1', command5)

        subprocess.run(['tmux', 'attach-session', '-t', session_name])

    except subprocess.CalledProcessError as e:
        print(f"[-] Failed to set up tmux session '{session_name}' with windows: {e}")
        sys.exit(1)


def run_zsh_command_in_tmux_pane(session_name, pane, command):
    try:
        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{pane}', command, 'C-m'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[-] Failed to run command '{command}' in pane {pane}: {e}")
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
                consecutive_failures = 0
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


tun0_ip= check_tun0_interface()
if tun0_ip:
    print(f"[+] tun0 is connected with IP: {tun0_ip}")

box_name = input("[?] Enter the name: ")

create_directory(box_name)
create_directory(box_name + "/www/")
os.chdir(f"/htb/{box_name}/www/")

run_zsh_command(f"gen_lin_rev {tun0_ip} 8443")
run_zsh_command(f"gen_php_rev {tun0_ip} 8443")

os.chdir(f"/htb/{box_name}/")

print("[i] Wait until you have a box IP, after entering we start pinging it to see if its up")
box_ip = input("[?] Enter the IP: ")
ping_host(box_ip)
run_zsh_command(f"addhost {box_ip} {box_name}.htb")
os.system(FULLSCREEN_I3_PANE)

command1 = f"nmap_default {box_ip} -p-"
command2 = f"nmap_udp {box_ip}"
command3 = f"sleep 2 && vhost {box_name}.htb"
command4 = f"fuzz_dir http://{box_name}.htb"
command5 = f"feroxbuster -u http://{box_name}.htb"

start_tmux_session_with_windows(box_name, command1, command2, command3, command4, command5)
