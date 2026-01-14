#!/usr/bin/env bash
set -euo pipefail

W=80
H=24
SLEEP=0.05

shades=(232 234 236 238 240 242 244 246 248 250 252 254)
NS=${#shades[@]}

enter() { printf '\e[?25l\e[?7l'; }
leave() { printf '\e[?7h\e[?25h\e[0m\n'; }
trap leave EXIT INT TERM
enter

cols=$(tput cols)
rows=$(tput lines)

ox=$(( (cols - W) / 2 ))
oy=$(( (rows - H) / 2 ))

cx=$((W / 2))
cy=$((H / 2))

t=0

while :; do
  for ((y=0; y<H; y++)); do
    printf '\e[%d;%dH' $((oy + y + 1)) $((ox + 1))
    for ((x=0; x<W; x++)); do
      dx=$(( x - cx ))
      dy=$(( (y - cy) * 2 ))   # <-- key fix

      d=$(( dx*dx + dy*dy ))
      w=$(( (d / 80 - t) % NS ))
      (( w < 0 )) && w=$((w + NS))

      printf '\e[48;5;%sm \e[0m' "${shades[$w]}"
    done
  done
  t=$((t + 1))
  sleep "$SLEEP"
done
