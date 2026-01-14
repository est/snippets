#!/usr/bin/env bash
W=80
H=24
SLEEP=0.05

shades=(232 234 236 238 240 242 244 246 248 250 252 254)
NS=${#shades[@]}

cx=$((W/2))
cy=$((H/2))
t=0

while :; do
  printf '\e[H'
  for ((y=0;y<H;y++)); do
    for ((x=0;x<W;x++)); do
      dx=$((x - cx))
      dy=$(( (y - cy) * 2 ))
      d=$(( dx*dx + dy*dy ))
      w=$(( (d / 80 - t) % NS ))
      (( w < 0 )) && w=$(( w + NS ))
      printf '\e[48;5;%sm \e[0m' "${shades[$w]}"
    done
    printf '\n'
  done
  t=$((t+1))
  sleep "$SLEEP"
done
