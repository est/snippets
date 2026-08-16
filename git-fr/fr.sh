#!/usr/bin/env bash
#
# git-fetchr — resumable `git fetch` for huge repositories on flaky links.
#
# Why: a normal fetch downloads ONE pack containing every object you lack. If
# the link dies mid-transfer the pack is thrown away and the retry restarts
# from zero. fetchr never asks for a big pack:
#
#   phase 1  fetch commits + trees only (--filter=blob:none): a tiny pack.
#            With --full the history is fetched in bounded deepen slices.
#   phase 2  backfill the missing blobs in small batches. Each batch is its
#            own request with lazy-fetch semantics (the server sends exactly
#            the blobs we name). After every round we recompute what is still
#            missing (git rev-list --missing=print) and only re-request
#            those. Interrupt the run and re-run: it resumes where it left
#            off. When everything is present, promisor state is dropped so
#            later plain `git fetch` behaves normally again.
#
# Requires a server with uploadpack.allowFilter and
# uploadpack.allowReachableSHA1InWant (GitHub and GitLab have both).
#
# Usage: git fetchr [options] [<remote> [<ref>]]
#   --full           fetch full history (default: shallow, depth 1)
#   --batch=N        blobs per phase-2 request (default 500)
#   --deepen=N       commits per phase-1 deepen slice (default 500)
#   --max-fetches=N  stop after N git-fetch calls (default: unlimited)
#   --timeout=S      per-request stall timeout in seconds (default 240)
set -euo pipefail

REMOTE=origin
REF=main
SHALLOW=1
BATCH=500
DEEPEN=500
MAX_FETCHES=0
TIMEOUT=600

say() { printf 'fetchr: %s\n' "$*"; }
die() { printf 'fetchr: error: %s\n' "$*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --full) SHALLOW=0 ;;
    --batch=*) BATCH="${1#--batch=}" ;;
    --deepen=*) DEEPEN="${1#--deepen=}" ;;
    --max-fetches=*) MAX_FETCHES="${1#--max-fetches=}" ;;
    --timeout=*) TIMEOUT="${1#--timeout=}" ;;
    --*) die "unknown option: $1" ;;
    *)
      if [ "$REMOTE" = origin ]; then REMOTE="$1"
      elif [ "$REF" = main ]; then REF="$1"
      else die "too many arguments"; fi ;;
  esac
  shift
done

command -v git >/dev/null || die "git not found"
export GIT_TERMINAL_PROMPT=0
TIP_REF="refs/remotes/$REMOTE/$REF"

git remote get-url "$REMOTE" >/dev/null 2>&1 || die "no such remote: $REMOTE"

FETCHES=0
# run_fetch <print|ignore> <cmd...> — with a stall watchdog (SSH has no
# built-in low-speed timeout). On failure with `print`, surface the log tail.
run_fetch() {
  local onfail="$1"; shift
  if [ "$MAX_FETCHES" -gt 0 ] && [ "$FETCHES" -ge "$MAX_FETCHES" ]; then
    say "budget exhausted (--max-fetches=$MAX_FETCHES); re-run to continue"
    exit 0
  fi
  FETCHES=$((FETCHES+1))
  local log; log=$(mktemp) || die "mktemp failed"
  "$@" >"$log" 2>&1 &
  local pid=$!
  local waited=0
  while kill -0 "$pid" 2>/dev/null; do
    sleep 2
    waited=$((waited+2))
    if [ "$waited" -ge "$TIMEOUT" ]; then
      kill "$pid" 2>/dev/null || true
      sleep 1
      pkill -P "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
      rm -f "$log"
      say "  request stalled ${TIMEOUT}s; will retry"
      return 1
    fi
  done
  local rc=0
  wait "$pid" || rc=$?
  if [ "$rc" -ne 0 ] && [ "$onfail" = print ]; then
    sed -n '1,6p' "$log" >&2
  fi
  rm -f "$log"
  return "$rc"
}

missing_shas() {
  git rev-list --objects --missing=print "$TIP_REF" 2>/dev/null | sed -n 's/^?//p' | sort -u
}

# When the repo is complete, drop promisor state so later plain `git fetch`
# calls get full packs again. When incomplete, keep it: phase 2 needs it.
cleanup() {
  # note: no `grep -q` here — it closes the pipe early and the SIGPIPE turns
  # this pipeline nonzero under pipefail, which would wrongly trigger the unset.
  if git rev-parse --verify --quiet "$TIP_REF" >/dev/null 2>&1 \
     && [ "$(missing_shas | wc -l | tr -d ' ')" -eq 0 ]; then
    git config --unset "remote.$REMOTE.promisor" 2>/dev/null || true
    git config --unset "remote.$REMOTE.partialclonefilter" 2>/dev/null || true
    find .git/objects/pack -name '*.promisor' -delete 2>/dev/null || true
  fi
}
trap cleanup EXIT

# ---- phase 1: commits + trees only ---------------------------------------
say "phase 1: fetching $REF (commits + trees only)"
PHASE1_FAILED=0
if ! run_fetch print git fetch --filter=blob:none --depth=1 --no-tags \
  "$REMOTE" "$REF:$TIP_REF"; then
  # On a partial repo a re-run can die inside index-pack --fix-thin (its
  # delta-base check walks tree blobs we don't have yet). If the ref already
  # exists that is not fatal: phase 2 will still make progress on blobs.
  if git rev-parse --verify --quiet "$TIP_REF" >/dev/null 2>&1; then
    PHASE1_FAILED=1
    say "phase 1 fetch failed but $TIP_REF already exists; continuing"
  else
    die "phase 1 failed — does the server support filter=blob:none (partial clone)?"
  fi
fi

# Phase 2 fetches must run as lazy fetches (the server sends exactly the
# blobs we name, bypassing the blob:none filter). git only writes this config
# itself when phase 1 actually transferred data, so set it explicitly.
git config "remote.$REMOTE.promisor" true
git config "remote.$REMOTE.partialclonefilter" blob:none

if [ "$SHALLOW" -eq 0 ]; then
  while :; do
    before=$(git rev-list --count "$TIP_REF" 2>/dev/null || echo 0)
    if ! run_fetch print git fetch --filter=blob:none --deepen="$DEEPEN" --no-tags \
      "$REMOTE" "$REF:$TIP_REF"; then
      say "deepen slice failed; keeping current depth (re-run to continue)"
      break
    fi
    after=$(git rev-list --count "$TIP_REF" 2>/dev/null || echo 0)
    [ "$after" -le "$before" ] && break
    say "  deepened: $after commits known"
  done
  say "full history present"
fi

# ---- phase 2: backfill missing blobs in batches --------------------------
say "phase 2: backfilling missing blobs (batch=$BATCH)"
round=0
while :; do
  MISSING=()
  while IFS= read -r s; do MISSING+=("$s"); done < <(missing_shas)
  N=${#MISSING[@]}
  [ "$N" -eq 0 ] && break
  round=$((round+1))
  say "round $round: $N objects missing"
  nbatch=$(( (N+BATCH-1)/BATCH ))
  b=0
  for ((i=0; i<N; i+=BATCH)); do
    b=$((b+1))
    batch=("${MISSING[@]:i:BATCH}")
    # Fetch with fetch.negotiationAlgorithm=noop (declare no haves) so the
    # server cannot thin-delta against blobs we don't have yet, and feed the
    # wants on stdin like git's own lazy fetch does. This is the one form of
    # `git fetch` that actually delivers blob wants reliably.
    printf '%s\n' "${batch[@]}" \
      | run_fetch ignore git -c fetch.negotiationAlgorithm=noop fetch "$REMOTE" \
          --no-tags --no-write-fetch-head --recurse-submodules=no \
          --filter=blob:none --stdin || true
    say "  batch $b/$nbatch requested (${#batch[@]} objects)"
  done
  AFTER=$(missing_shas | wc -l | tr -d ' ')
  if [ "$AFTER" -ge "$N" ]; then
    say "no progress in round $round; stopping (re-run later to resume)"
    say "stuck objects (first 10):"
    missing_shas | sed -n '1,10p' | sed 's/^/  /'
    exit 1
  fi
done

# ---- finish --------------------------------------------------------------
NPACKS=$(ls .git/objects/pack/*.pack 2>/dev/null | wc -l | tr -d ' ')
if [ "$NPACKS" -gt 8 ]; then
  say "consolidating $NPACKS packs (git repack -ad)..."
  git repack -ad -q || say "repack failed (non-fatal)"
fi
say "done: $REF fully fetched, all objects present"
if [ "$PHASE1_FAILED" -eq 1 ]; then
  say "note: phase 1 could not refresh $TIP_REF; run again to pick up new commits"
fi
