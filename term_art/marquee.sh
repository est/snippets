#!/usr/bin/env bash
set -euo pipefail

# ---------- terminal setup ----------
enter() {
  printf '\e[?25l\e[?7l'   # hide cursor, disable wrap
}
leave() {
  printf '\e[?7h\e[?25h\e[0m\n'  # restore wrap, cursor, attrs
}
trap leave EXIT INT TERM
enter

# ---------- state ----------
shades=({232..255})
n=${#shades[@]}
offset=0

# update terminal width on resize
cols=$(tput cols)
trap 'cols=$(tput cols)' WINCH

# ---------- render loop ----------
while :; do
  printf '\r'
  for ((i=0; i<cols; i++)); do
    c=${shades[$(( (i+offset)%n ))]}
    printf '\e[38;5;%sm█\e[0m' "$c"
  done
  offset=$(( (offset+1)%n ))
  sleep 0.04
done
