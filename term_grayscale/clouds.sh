#!/usr/bin/env bash
set -euo pipefail

W=80
H=24
SLEEP=0.05
MAX_CLOUDS=5
CLOUD_LIFE=20
SHADES=(232 234 236 238 240 242 244 246 248 250 252 254)
NS=${#SHADES[@]}
ASPECT_X=1   # horizontal stretch
ASPECT_Y=2   # vertical stretch

printf '\e[?1049h'  # alternate screen
printf '\e[?25l'    # hide cursor
printf '\e[?7l'     # disable wrap
trap 'printf "\e[0m\e[?7h\e[?25h\e[?1049l\n"' EXIT INT TERM

clouds=()
t=0

while :; do
  cols=$(tput cols)
  rows=$(tput lines)
  ox=$(( (cols - W)/2 ))
  oy=$(( (rows - H)/2 ))

  (( ${#clouds[@]} < MAX_CLOUDS )) && clouds+=("$((RANDOM%W)) $((RANDOM%H)) 0 $((RANDOM%3+1))")

  canvas=()
  for ((y=0;y<H;y++)); do
    for ((x=0;x<W;x++)); do
      canvas[$((y*W+x))]=0
    done
  done

  new_clouds=()
  for cloud in "${clouds[@]}"; do
    read -r cx cy age radius <<< "$cloud"
    if (( age < CLOUD_LIFE )); then
      r=$(( radius + age/3 ))
      for ((dy=-r; dy<=r; dy++)); do
        for ((dx=-r; dx<=r; dx++)); do
          x=$((cx + dx))
          y=$((cy + dy))
          if (( x>=0 && x<W && y>=0 && y<H )); then
            dxs=$(( dx * ASPECT_X ))
            dys=$(( dy * ASPECT_Y ))
            d2=$(( dxs*dxs + dys*dys ))
            skip=$(( RANDOM % (r+2) ))
            if (( skip < (r+1) && d2 <= r*r )); then
              shade_index=$(( age * (NS-1) / CLOUD_LIFE ))
              canvas[$((y*W+x))]=$shade_index
            fi
          fi
        done
      done
      new_clouds+=("$cx $cy $((age+1)) $radius")
    fi
  done
  clouds=("${new_clouds[@]}")

  for ((y=0;y<H;y++)); do
    printf '\e[%d;%dH' $((oy+y+1)) $((ox+1))
    last=-1
    run=0
    for ((x=0;x<W;x++)); do
      idx=${canvas[$((y*W+x))]}
      c=${SHADES[$idx]}
      if (( c == last )); then
        ((run++))
      else
        (( run>0 )) && printf '\e[48;5;%sm%*s' "$last" "$run" ""
        last=$c
        run=1
      fi
    done
    (( run>0 )) && printf '\e[48;5;%sm%*s' "$last" "$run" ""
  done

  t=$((t+1))
  sleep "$SLEEP"
done
