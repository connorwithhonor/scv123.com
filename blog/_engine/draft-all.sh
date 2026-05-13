#!/usr/bin/env bash
# Draft all 17 SCV123 blog posts. 2-second delay between calls.
# Usage:
#   ./draft-all.sh                # uses default model (claude-sonnet-4-6)
#   ./draft-all.sh opus           # override model
#   START=8 END=12 ./draft-all.sh # draft cards 8 through 12 only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MODEL="${1:-claude-sonnet-4-6}"
START="${START:-1}"
END="${END:-17}"

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ERROR: ANTHROPIC_API_KEY not set in environment" >&2
  exit 1
fi

echo "[draft-all] model=$MODEL cards=$START..$END"
echo "[draft-all] prompt cache will warm after card 1; subsequent calls hit cached system block"
echo ""

FAILED=()
for i in $(seq "$START" "$END"); do
  echo "===== card $i ====="
  if python3 draft.py "$i" --model "$MODEL"; then
    :
  else
    FAILED+=("$i")
    echo "[draft-all] card $i FAILED, continuing" >&2
  fi
  if [ "$i" -lt "$END" ]; then
    sleep 2
  fi
done

echo ""
echo "===== summary ====="
echo "drafts in: $SCRIPT_DIR/drafts/"
if [ "${#FAILED[@]}" -eq 0 ]; then
  echo "all cards drafted clean"
else
  echo "FAILED: ${FAILED[*]}"
  echo "re-run individually: python3 draft.py <id>"
  exit 1
fi
