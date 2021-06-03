!/bin/sh

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 knockport1 [knockport2 ...] openport" >&2
  exit 1
fi


# clear all lol
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT
sudo iptables -F

# create chain
sudo iptables -N KNOCKING
sudo iptables -N GATE1
sudo iptables -N GATE2
sudo iptables -N GATE3
sudo iptables -N PASSED


# allow existing tcp and local iface
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -i lo -j ACCEPT


# $1 usually venet0:0 for most kvm vps out there
# sudo iptables -A INPUT -i $1 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 33333 -j ACCEPT
sudo iptables -A INPUT -p udp -j ACCEPT
sudo iptables -A INPUT -p tcp -j KNOCKING

# 1st port knock
sudo iptables -A GATE1 -p tcp --dport $2 -m recent --name AUTH1 --set -j DROP
sudo iptables -A GATE1 -j RETURN
sudo iptables -A GATE2 -p tcp --dport $2 -j DROP
sudo iptables -A GATE2 -m recent --name AUTH1 --remove

# 2nd port knock
sudo iptables -A GATE2 -p tcp --dport $3 -m recent --name AUTH2 --set -j DROP
sudo iptables -A GATE2 -j GATE1
sudo iptables -A GATE3 -p tcp --dport $3 -j DROP
sudo iptables -A GATE3 -m recent --name AUTH2 --remove

# 3rd port knock
sudo iptables -A GATE3 -p tcp --dport $4 -m recent --name AUTH3 --set -j DROP
sudo iptables -A GATE3 -j GATE1
sudo iptables -A PASSED -p tcp --dport $4 -j DROP
# uncomment this line to limit one connection per knock
# sudo iptables -A PASSED -m recent --name AUTH3 --remove

# knock success, allow connection
sudo iptables -A PASSED -p tcp --dport $5 -j ACCEPT
sudo iptables -A PASSED -m state --state NEW,RELATED -p tcp --dport $5  -m recent --name AUTH3 --set
sudo iptables -A PASSED -j GATE1

# apply those chains to iptables
sudo iptables -A KNOCKING -m recent --rcheck --seconds 30 --name AUTH3 -j PASSED
sudo iptables -A KNOCKING -m recent --rcheck --seconds 10 --name AUTH2 -j GATE3
sudo iptables -A KNOCKING -m recent --rcheck --seconds 10 --name AUTH1 -j GATE2
sudo iptables -A KNOCKING -j GATE1
