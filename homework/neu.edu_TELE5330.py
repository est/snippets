#!/usr/bin/env python
#coding: utf8

# some random homework, for neu.edu, TELE5330

import subprocess

# because the requirement is too clever to use `sys`
ARGV = subprocess.sys.argv

def nslookup(n):
    stdout, _ = subprocess.Popen(
        'nslookup "%s" | grep name' % n,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        shell=True
    ).communicate()
    try:
        return stdout[stdout.index('name =')+6:-2].strip()
    except ValueError:
        return None

if len(ARGV)!=4:
  exit('Missing parameters: <IP> <IP> <hostname>')

# parse the first ARGV
# why would anyone use `nslookup` and not `dig` or `socket.gethostbyname()`?
print 'IP address = %s' % ARGV[1]

# No Regexp? Really?
ip = nslookup(ARGV[1])
print 'Hostname %s' % ('= %s' % ip if ip else 'not found')

# parse the second ARGV
print 'IP address = %s' % ARGV[2]
ret = subprocess.os.system('ping -c1 -t2 "%s" 2>&1 >/dev/null' % ARGV[2])
print 'Status = %s' % (['Up', 'Down'][bool(ret)])

# parse the third ARGV
stdout, _ = subprocess.Popen(
    'nmap -n -oG - "%s" | grep "Ports:"' % ARGV[3],
    stdout=subprocess.PIPE,
    stdin=subprocess.PIPE,
    shell=True
).communicate()
print 'open TCP connections = %s' % stdout.count('/open/tcp//')
try:
    f_count = stdout[stdout.index(' filtered (')+11:].strip()[:-1]
except ValueError:
    f_count = 0
print 'filtered TCP connections = %s' % f_count


















