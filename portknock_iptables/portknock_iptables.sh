#!/bin/sh

# show help
if [ "$#" -lt 2 ]; then
  echo "Usage: $0 iface knockport1 [knockport2 ...] openport" >&2
  echo "Author: github.com/est"
  exit 1
fi

# debug
sudo () {
  echo $*
}
tac() { tail -r -- "$@"; }  # for macos

# clear all lol
# sudo iptables -P INPUT ACCEPT
# sudo iptables -P FORWARD ACCEPT
# sudo iptables -P OUTPUT ACCEPT
# sudo iptables -F

# create chain
sudo iptables -N KNOCKING  2>/dev/null
sudo iptables -N GATE1  2>/dev/null
sudo iptables -N GATE2  2>/dev/null
sudo iptables -N GATE3  2>/dev/null
sudo iptables -N PASSED  2>/dev/null

# clear old shit
for ln in $(sudo iptables -L INPUT --line-numbers | grep '/* estpk:' | awk '{print $1}' | tac); do
  sudo iptables -D INPUT $ln;
done;

sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT -m comment --comment "estpk: limit ssh access"
sudo iptables -A INPUT -i lo -j ACCEPT -m comment --comment "estpk: allow local iface"
# sudo iptables -A INPUT -i venet0:0 -j ACCEPT -m comment --comment "estpk: allow other iface"
# sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT -m comment --comment "estpk: whitelist ssh port"
sudo iptables -A INPUT -p udp -j ACCEPT -m comment --comment "estpk: allow udp"
sudo iptables -A INPUT -p tcp -j KNOCKING -m comment --comment "estpk: start block everything"

# 1st port knock
sudo iptables -A GATE1 -p tcp --dport $1 -m recent --name AUTH1 --set -j DROP
sudo iptables -A GATE1 -j RETURN

# 2nd port knock
sudo iptables -A GATE2 -p tcp --dport $1 -j DROP
sudo iptables -A GATE2 -m recent --name AUTH1 --remove
sudo iptables -A GATE2 -p tcp --dport $2 -m recent --name AUTH2 --set -j DROP
sudo iptables -A GATE2 -j GATE1

# 3rd port knock
sudo iptables -A GATE3 -p tcp --dport $2 -j DROP
sudo iptables -A GATE3 -m recent --name AUTH2 --remove
sudo iptables -A GATE3 -p tcp --dport $3 -m recent --name AUTH3 --set -j DROP
sudo iptables -A GATE3 -j GATE1


# if knock succeed, allow connection
sudo iptables -A PASSED -p tcp --dport $3 -j DROP
# uncomment this line to limit one connection per knock
# sudo iptables -A PASSED -m recent --name AUTH3 --remove
sudo iptables -A PASSED -p tcp --dport $4 -j ACCEPT
sudo iptables -A PASSED -m state --state NEW,RELATED -p tcp --dport $4  -m recent --name AUTH3 --set
sudo iptables -A PASSED -j GATE1

# apply those chains to iptables
sudo iptables -A KNOCKING -m recent --rcheck --seconds 30 --name AUTH3 -j PASSED
sudo iptables -A KNOCKING -m recent --rcheck --seconds 10 --name AUTH2 -j GATE3
sudo iptables -A KNOCKING -m recent --rcheck --seconds 10 --name AUTH1 -j GATE2
sudo iptables -A KNOCKING -j GATE1
